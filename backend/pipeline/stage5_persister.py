from ..schemas import EnrichedProduct, flatten_enriched_product
from ..database import get_db

def run_stage5_persister(product: EnrichedProduct, row_id: int):
    flat_data = flatten_enriched_product(product)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Update enriched_rows
    # Convert values to strings for db insert
    update_fields = {}
    for k, v in flat_data.items():
        update_fields[k] = str(v) if v is not None else None
        
    set_clause = ", ".join([f'"{k}" = ?' for k in update_fields.keys()])
    values = tuple(update_fields.values()) + (row_id,)
    cursor.execute(f"UPDATE enriched_rows SET {set_clause}, status='done' WHERE row_id=?", values)
    
    # 2. Insert into audit_log
    # Field_name, source_type, source_url, field_confidence
    for k, v in update_fields.items():
        if v is not None and k not in ["row_id", "project_id", "status", "confidence_score", "needs_human_review", "review_reason"]:
            cursor.execute(
                "INSERT INTO audit_log (row_id, field_name, source_type, source_url, field_confidence) VALUES (?, ?, ?, ?, ?)",
                (row_id, k, "llm", product.mfr_url, product.confidence_score)
            )
            
    conn.commit()
    conn.close()
