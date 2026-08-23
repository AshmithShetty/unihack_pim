import os
from groq import AsyncGroq
from pydantic import ValidationError
import time
from ..schemas import EnrichedProduct
from typing import Dict, Any, Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Setup Groq native client
client = AsyncGroq(api_key=GROQ_API_KEY)

async def run_stage3_enricher(row_data: Dict[str, Any], scraper_data: Dict[str, Any], prompt_template: str, mapping: Dict[str, str]) -> EnrichedProduct:
    # Build user prompt
    page_text = scraper_data.get("page_text", "")
    if page_text:
        page_text = page_text[:2000] # Reduced to 2000 to save input tokens
        
    pdf_texts = "\n".join([text[:500] for text in scraper_data.get("pdf_texts", {}).values()])
    
    user_content = f"""
    Row Data (Original): {row_data}
    Column Mapping: {mapping}
    
    Product Page Content:
    {page_text}
    
    {pdf_texts}
    """
    
    # Inject dummy JSON into prompt instead of OpenAPI schema to prevent hallucination
    from ..schemas import AttributeTriad
    dummy_product = EnrichedProduct.model_construct(
        attributes=[AttributeTriad(label="Example Label", value="Example Value", uom="Optional Unit")],
        item_features=["Example Feature 1"]
    )
    dummy_json = dummy_product.model_dump_json(by_alias=True, exclude_none=False)
    user_content += f"\n\nYou MUST return your answer as a raw JSON object containing exactly these keys. Do NOT output a JSON schema definition, output the actual populated data object:\n{dummy_json}"
    
    # Call LLM with explicitly high max_tokens and native Pydantic validation retries
    max_retries = 3
    product = None
    
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,
                max_tokens=4096
            )
            raw_text = response.choices[0].message.content
            print(f"\n[DEBUG] Attempt {attempt + 1} RAW TEXT: {repr(raw_text[:500])}...\n")
            
            # Robust JSON extraction to handle reasoning models (like Qwen/DeepSeek)
            import re
            clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', clean_text, re.DOTALL)
            if match:
                clean_text = match.group(1)
                
            product = EnrichedProduct.model_validate_json(clean_text.strip())
            break
        except ValidationError as e:
            if attempt == max_retries - 1:
                raise ValueError(f"LLM Enrichment failed validation after {max_retries} retries: {e}")
            # Feed the exact validation error back to Gemini so it can correct it
            user_content += f"\n\nValidation Failed: {e}\nPlease correct your previous JSON output to match the schema exactly."
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            import asyncio
            await asyncio.sleep(2)
    
    # Merge back the URLs found by scraper
    product.mfr_url = scraper_data.get("mfr_url")
    product.ref_urls = scraper_data.get("ref_urls", [])
    
    def get_supplier_col_for_target(mapping: dict, target: str) -> Optional[str]:
        for supplier_col, data in mapping.items():
            if isinstance(data, dict) and data.get("mapped_target") == target:
                return supplier_col
        return None
    
    # Preserve the original row mapping data dynamically based on mapping!
    mpn_col = get_supplier_col_for_target(mapping, "Mfg_Part_Num")
    desc_col = get_supplier_col_for_target(mapping, "Part_Desc")
    e1_col = get_supplier_col_for_target(mapping, "E1_Brand")
    uni_col = get_supplier_col_for_target(mapping, "Unilog_Brand")
    dib_col = get_supplier_col_for_target(mapping, "DIB_Brand")
    manuf_col = get_supplier_col_for_target(mapping, "Part_Manuf")
    
    product.mfg_part_num = row_data.get(mpn_col) if mpn_col else None
    product.part_desc = row_data.get(desc_col) if desc_col else None
    product.e1_brand = row_data.get(e1_col) if e1_col else None
    product.unilog_brand = row_data.get(uni_col) if uni_col else None
    product.dib_brand = row_data.get(dib_col) if dib_col else None
    product.part_manuf = row_data.get(manuf_col) if manuf_col else None
    
    return product
