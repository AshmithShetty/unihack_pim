import re
import os
import json
import pandas as pd
from typing import Dict, Tuple, List, Optional
from groq import AsyncGroq
from backend.schemas import GOLDEN_RECORD_COLUMNS

def clean_value(val: any) -> Optional[str]:
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    
    # Strip placeholders like "-- unknown --" or generic "-" or "_"
    if re.match(r'^--\s.*\s--$', val_str) or re.match(r'^[-_]+$', val_str):
        return None
        
    lower_val = val_str.lower()
    if lower_val in ('n/a', 'none', 'unknown', ''):
        return None
        
    return val_str

async def resolve_manufacturer(part_manuf: str, part_desc: str, manufacturer_df: Optional[pd.DataFrame]) -> dict:
    resolved = {
        "MANUFACTURER_NAME": None,
        "BRAND_NAME": None,
        "brand_domain": None
    }
    
    combined_info = f"Manufacturer field: {part_manuf}\nDescription: {part_desc}"
    if not combined_info.strip():
        return resolved
        
    try:
        client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        prompt = (
            "Extract the Canonical Manufacturer Name and Brand Name from the following product information. "
            "Return ONLY a valid JSON object with keys 'MANUFACTURER_NAME' and 'BRAND_NAME'. "
            "If you cannot find one, set its value to null.\n\n"
            f"{combined_info}"
        )
        
        response = await client.chat.completions.create(
            model=os.getenv("GROQ_MODEL"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        result = json.loads(response.choices[0].message.content)
        resolved["MANUFACTURER_NAME"] = result.get("MANUFACTURER_NAME")
        resolved["BRAND_NAME"] = result.get("BRAND_NAME")
        # In this hackathon update, we don't need a domain for the scraper since we banned distributors anyway, 
        # DDG will find the manufacturer naturally.
    except Exception as e:
        print(f"Error resolving manufacturer via LLM: {e}")

    return resolved

async def clean_and_resolve(row: dict, confirmed_mapping: dict, manufacturer_df: Optional[pd.DataFrame] = None) -> Tuple[Dict, List[str]]:
    """
    Cleans raw row data, applies mapping, resolves manufacturer,
    and returns (filled_row_dict, gap_list).
    """
    # 1. Initialize filled row with all golden columns as None
    filled_row = {col: None for col in GOLDEN_RECORD_COLUMNS}
    
    def get_supplier_col_for_target(mapping: dict, target: str) -> Optional[str]:
        for supplier_col, data in mapping.items():
            if isinstance(data, dict) and data.get("mapped_target") == target:
                return supplier_col
        return None
        
    # 2. Extract original data dynamically using the mapping
    mpn_col = get_supplier_col_for_target(confirmed_mapping, "Mfg_Part_Num")
    brand_col = get_supplier_col_for_target(confirmed_mapping, "Part_Manuf")
    desc_col = get_supplier_col_for_target(confirmed_mapping, "Part_Desc")
    
    filled_row["Mfg_Part_Num"] = clean_value(row.get(mpn_col)) if mpn_col else None
    filled_row["Part_Manuf"] = clean_value(row.get(brand_col)) if brand_col else None
    filled_row["Part_Desc"] = clean_value(row.get(desc_col)) if desc_col else None
    
    # 3. Resolve Manufacturer
    part_manuf = filled_row.get("Part_Manuf") or ""
    part_desc = filled_row.get("Part_Desc") or ""
    
    resolved = await resolve_manufacturer(part_manuf, part_desc, manufacturer_df)
    
    if resolved["MANUFACTURER_NAME"]:
        filled_row["MANUFACTURER_NAME"] = resolved["MANUFACTURER_NAME"]
    if resolved["BRAND_NAME"]:
        filled_row["BRAND_NAME"] = resolved["BRAND_NAME"]
        
    # 4. Compute gap_list (columns that are still None)
    gap_list = [col for col, val in filled_row.items() if val is None]
    
    # Store brand_domain temporarily for stage 2 (won't be saved to DB directly)
    filled_row["_brand_domain"] = resolved["brand_domain"]
    
    return filled_row, gap_list
