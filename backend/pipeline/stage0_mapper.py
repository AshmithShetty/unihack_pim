import io
import pandas as pd
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ValidationError
from groq import Groq
import os
from dotenv import load_dotenv
from backend.schemas import GOLDEN_RECORD_COLUMNS

load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "dummy"))
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

class ColumnMapping(BaseModel):
    supplier_column: str
    mapped_target: str = Field(description="Must be exactly one of the GOLDEN_RECORD_COLUMNS or '__IGNORE__', '__CONTEXT__', '__NORMALIZE__'")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    reasoning: str

class MappingProposal(BaseModel):
    mappings: List[ColumnMapping]

def run_mapper(file_bytes: bytes, project_id: int) -> Dict:
    """
    Reads the first few rows of the CSV, calls Gemini LLM to map the columns
    to the golden record schema.
    """
    # Read just the first 4 rows (1 header + 3 data)
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), nrows=3)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")

    supplier_columns = list(df.columns)
    
    # Format data sample for prompt
    data_sample = df.to_dict(orient="records")

    prompt = f"""
    You are an expert data mapper for a PIM (Product Information Management) system.
    We need to map the following supplier columns to our exact expected output schema.
    
    Supplier Columns: {supplier_columns}
    Data Sample (First 3 rows): {data_sample}
    
    Target Golden Record Columns: {GOLDEN_RECORD_COLUMNS}
    
    Rules:
    1. For each supplier column, choose exactly ONE target column from the Golden Record Columns.
    2. If a supplier column does not match any target column, use "__IGNORE__".
    3. If the supplier column provides general context but no direct mapping, use "__CONTEXT__".
    4. You MUST be confident. If unsure, use "__IGNORE__".
    """

    # Inject dummy JSON into prompt instead of OpenAPI schema to prevent hallucination
    dummy_json = MappingProposal(mappings=[ColumnMapping(supplier_column="example_col", mapped_target="__IGNORE__", confidence=0.9, reasoning="example")]).model_dump_json(by_alias=True, exclude_none=False)
    prompt += f"\n\nYou MUST return your answer as a raw JSON object exactly matching the structure of this example. Do NOT output a JSON schema, output the actual data object:\n{dummy_json}"

    # Call LLM with native Pydantic validation retries
    max_retries = 3
    proposal = None
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=4096
            )
            raw_text = response.choices[0].message.content
            
            # Robust JSON extraction to handle reasoning models (like Qwen/DeepSeek)
            import re
            clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', clean_text, re.DOTALL)
            if match:
                clean_text = match.group(1)
                
            proposal = MappingProposal.model_validate_json(clean_text.strip())
            break
        except ValidationError as e:
            if attempt == max_retries - 1:
                print(f"LLM Mapping failed validation after {max_retries} retries: {e}")
                proposal = MappingProposal(mappings=[
                    ColumnMapping(supplier_column=c, mapped_target="__IGNORE__", confidence=0.0, reasoning="Fallback")
                    for c in supplier_columns
                ])
                break
            # Append error to prompt for the next try
            prompt += f"\n\nValidation Failed: {e}\nPlease correct your previous JSON output to match the schema exactly."
        except Exception as e:
            # Fallback if model fails or API key is not set
            print(f"LLM Mapping failed: {e}. Falling back to default.")
            proposal = MappingProposal(mappings=[
                ColumnMapping(supplier_column=c, mapped_target="__IGNORE__", confidence=0.0, reasoning="Fallback")
                for c in supplier_columns
            ])
            break

    # Hard verification
    valid_targets = set(GOLDEN_RECORD_COLUMNS + ["__IGNORE__", "__CONTEXT__", "__NORMALIZE__"])
    final_mapping = {}
    
    for m in proposal.mappings:
        target = m.mapped_target
        if target not in valid_targets:
            target = "__IGNORE__"
        
        final_mapping[m.supplier_column] = {
            "mapped_target": target,
            "confidence": m.confidence,
            "reasoning": m.reasoning
        }
        
    return final_mapping
