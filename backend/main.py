from fastapi import FastAPI, UploadFile, File, Form, WebSocket, BackgroundTasks, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import pandas as pd
import os
import shutil
import sqlite3
from pathlib import Path
import asyncio

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from .database import (
    init_db, get_db, get_all_projects, update_project_status, 
    update_project_filename, update_project_mapping, insert_row, update_row_status,
    get_project_rows
)
from .pipeline.stage0_mapper import run_mapper
from .pipeline.stage1_cleaner import clean_and_resolve
from .pipeline.stage2_scraper import run_stage2_scraper
from .pipeline.stage3_enricher import run_stage3_enricher
from .pipeline.stage4_validator import run_stage4_validator
from .pipeline.stage5_persister import run_stage5_persister
from .chatbot import get_vanna_instance
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
os.makedirs(INPUT_DIR, exist_ok=True)

try:
    with open(BASE_DIR / "backend" / "prompts" / "system_prompt.txt", "r") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = ""

app = FastAPI(title="UniHack PIM")

# Configure CORS
origins = [
    "http://localhost:5173", # Local frontend
]

frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for reference files
reference_data = {
    "manufacturer_df": None,
    "uom_set": set(),
    "decimal_fraction_dict": {},
    "lov_dict": {}
}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: int):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, websocket: WebSocket, project_id: int):
        if project_id in self.active_connections and websocket in self.active_connections[project_id]:
            self.active_connections[project_id].remove(websocket)

    async def broadcast_to_project(self, project_id: int, message: dict):
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    # 1. Init Database
    init_db()
    
    # 2. Setup Vanna AI
    get_vanna_instance()
    
    print("Startup complete. Database initialized and Vanna trained.")

class ProjectCreate(BaseModel):
    project_name: str

@app.get("/api/projects")
async def get_projects():
    projects = get_all_projects()
    return {"status": "ok", "projects": projects}

@app.post("/api/projects")
async def create_project(project: ProjectCreate):
    conn = get_db()
    cursor = conn.cursor()
    created_at = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO projects (project_name, status, created_at) VALUES (?, ?, ?)",
        (project.project_name, "pending", created_at)
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"status": "ok", "project_id": project_id, "project_name": project.project_name}

@app.delete("/api/projects/{id}")
async def delete_project(id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT filename FROM projects WHERE project_id=?", (id,))
    res = cursor.fetchone()
    
    cursor.execute("DELETE FROM projects WHERE project_id=?", (id,))
    cursor.execute("DELETE FROM enriched_rows WHERE project_id=?", (id,))
    conn.commit()
    conn.close()
    
    if res and res['filename']:
        file_path = INPUT_DIR / f"{id}_{res['filename']}"
        if file_path.exists():
            os.remove(file_path)
            
    return {"status": "ok", "deleted_id": id}

@app.post("/api/projects/{id}/upload")
async def upload_project_csv(id: int, file: UploadFile = File(...)):
    # Save the file
    filename = f"{id}_{file.filename}"
    file_path = INPUT_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    update_project_filename(id, file.filename)
    
    # Read bytes for mapper
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        
    try:
        mapping_proposal = run_mapper(file_bytes, id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"status": "ok", "mapping_proposal": mapping_proposal}

def get_supplier_col_for_target(mapping: dict, target: str) -> Optional[str]:
    for supplier_col, data in mapping.items():
        if isinstance(data, dict) and data.get("mapped_target") == target:
            return supplier_col
    return None

async def enrich_single_row(row_id: int, project_id: int, row_data: dict, mapping: dict, semaphore: asyncio.Semaphore):
    async with semaphore:
        update_row_status(row_id, "running")
        try:
            # Stage 1: Cleaner
            filled_row, gap_list = clean_and_resolve(row_data, mapping, reference_data["manufacturer_df"])
            
            # Stage 2: Scraper
            scraper_data = await run_stage2_scraper(filled_row, row_data)
            
            # Stage 3: Enricher
            product = run_stage3_enricher(row_data, scraper_data, SYSTEM_PROMPT, mapping)
            
            # Stage 4: Validator
            has_web_data = bool(scraper_data.get("page_text"))
            product = run_stage4_validator(product, reference_data, has_web_data)
            
            # Stage 5: Persister
            run_stage5_persister(product, row_id)
            
            # Increment processed_rows
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE projects SET processed_rows = processed_rows + 1 WHERE project_id=?", (project_id,))
            conn.commit()
            conn.close()

            # Broadcast update
            await manager.broadcast_to_project(project_id, {
                "type": "row_updated",
                "row_id": row_id,
                "status": "done",
                "confidence_score": product.confidence_score
            })

        except Exception as e:
            update_row_status(row_id, "failed", needs_human_review=1, review_reason=str(e))
            
        finally:
            # Artificial delay for rate limits. Groq supports high RPM so we can process fast
            await asyncio.sleep(1.0)

async def enrich_all_rows(project_id: int, mapping: dict):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM projects WHERE project_id=?", (project_id,))
    res = cursor.fetchone()
    conn.close()
    
    if not res or not res['filename']:
        return
        
    filename = f"{project_id}_{res['filename']}"
    file_path = INPUT_DIR / filename
    
    df = pd.read_csv(file_path)
    
    # Insert pending rows
    row_ids_and_data = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        
        data = {
            "project_id": project_id,
            "status": "pending"
        }
        
        # Universally map all confirmed target columns for the initial DB insert
        for supplier_col, map_info in mapping.items():
            if isinstance(map_info, dict):
                target = map_info.get("mapped_target")
                if target and target not in ["__IGNORE__", "__CONTEXT__"]:
                    val = row_dict.get(supplier_col)
                    if pd.notna(val) and val is not None:
                        data[target] = str(val)
        row_id = insert_row("enriched_rows", data)
        row_ids_and_data.append((row_id, row_dict))
        
    update_project_status(project_id, "running", total_rows=len(df))
    
    # Run async enrichment sequentially to avoid Rate Limits on the new model
    semaphore = asyncio.Semaphore(4)
    tasks = [
        enrich_single_row(rid, project_id, rdata, mapping, semaphore)
        for rid, rdata in row_ids_and_data
    ]
    await asyncio.gather(*tasks)
    
    update_project_status(project_id, "done")

@app.post("/api/projects/{id}/confirm")
async def confirm_project_mapping(id: int, mapping: dict, background_tasks: BackgroundTasks):
    mapping_json = json.dumps(mapping)
    update_project_mapping(id, mapping_json)
    
    # Dispatch background task
    background_tasks.add_task(enrich_all_rows, id, mapping)
    
    return {"status": "ok", "project_id": id, "message": "Enrichment started in background"}

@app.get("/api/projects/{id}/rows")
async def get_project_rows_api(id: int):
    rows = get_project_rows(id)
    return {"status": "ok", "rows": rows}

@app.get("/api/projects/{id}/export")
async def export_project_csv(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enriched_rows WHERE project_id=? AND status='done'", (id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No done rows found")
        
    df = pd.DataFrame([dict(r) for r in rows])
    
    from .schemas import GOLDEN_RECORD_COLUMNS
    cols = [c for c in GOLDEN_RECORD_COLUMNS if c in df.columns]
    df = df[cols]
    
    export_path = INPUT_DIR / f"export_{id}.csv"
    df.to_csv(export_path, index=False)
    
    return FileResponse(path=export_path, filename=f"Project_{id}_Enriched.csv", media_type="text/csv")

@app.websocket("/ws/projects/{id}")
async def websocket_endpoint(websocket: WebSocket, id: int):
    await manager.connect(websocket, id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, id)

@app.patch("/api/projects/{id}/rows/{row_id}")
async def edit_row(id: int, row_id: int, updates: dict):
    conn = get_db()
    cursor = conn.cursor()
    allowed_cols = [c[1] for c in cursor.execute("PRAGMA table_info(enriched_rows)").fetchall()]
    
    set_clauses = []
    values = []
    for k, v in updates.items():
        if k in allowed_cols:
            set_clauses.append(f"{k}=?")
            values.append(v)
            
    if not set_clauses:
        conn.close()
        return {"status": "ok", "message": "No valid fields updated"}
        
    values.append(row_id)
    query = f"UPDATE enriched_rows SET {', '.join(set_clauses)}, status='done' WHERE row_id=?"
    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()
    
    await manager.broadcast_to_project(id, {
        "type": "row_updated",
        "row_id": row_id,
        "status": "done"
    })
    
    return {"status": "ok"}

@app.get("/api/rows/{row_id}/audit")
async def get_row_audit(row_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enriched_rows WHERE row_id=?", (row_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")
        
    audit_data = [
        {"field_name": "MANUFACTURER_NAME", "source_type": "LLM_INFERENCE", "source_url": None, "field_confidence": 0.92},
        {"field_name": "BRAND_NAME", "source_type": "LLM_INFERENCE", "source_url": None, "field_confidence": 0.92},
        {"field_name": "SHORT_DESC", "source_type": "GENERATED", "source_url": None, "field_confidence": 0.95},
        {"field_name": "INVOICE_DESC", "source_type": "GENERATED", "source_url": None, "field_confidence": 0.95},
        {"field_name": "Product Image", "source_type": "MANUFACTURER_WEBSITE", "source_url": row["MFR URL"] if row.keys() and "MFR URL" in row.keys() else None, "field_confidence": 1.0}
    ]
    return {"status": "ok", "audit": audit_data}

class ChatQuery(BaseModel):
    question: str
    project_id: Optional[int] = None

@app.post("/api/chat")
async def chat(query: ChatQuery):
    agent = get_vanna_instance()
    if not agent:
        raise HTTPException(status_code=500, detail="Chatbot is not configured.")
        
    try:
        res = agent.ask_database(query.question, query.project_id)
        return {
            "status": "ok",
            "answer": res["answer"],
            "sql": res["sql"],
            "results": res["results"]
        }
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
