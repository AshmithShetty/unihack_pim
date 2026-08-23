from ..schemas import EnrichedProduct

def run_stage4_validator(product: EnrichedProduct, reference_data: dict, has_web_data: bool) -> EnrichedProduct:
    confidence = 1.0
    
    # 1. INVOICE_DESC: len <= 40 AND val == val.upper()
    if product.invoice_desc:
        if len(product.invoice_desc) > 40 or product.invoice_desc != product.invoice_desc.upper():
            product.invoice_desc = None
            confidence -= 0.1
            
    # 2. MOBILE_DESC: 60 <= len <= 80
    if product.mobile_desc:
        if not (60 <= len(product.mobile_desc) <= 80):
            product.mobile_desc = None
            confidence -= 0.05
            
    # 3. UOM fields
    # UOMs will now be validated by the LLM prompt. We will not forcefully delete UOMs here.
    
    # 4. Decimal -> Fraction (Native Python implementation)
    decimal_to_fraction = {
        ".125": "1/8", ".25": "1/4", ".375": "3/8", ".5": "1/2", 
        ".625": "5/8", ".75": "3/4", ".875": "7/8",
        ".0625": "1/16", ".1875": "3/16", ".3125": "5/16", ".4375": "7/16", 
        ".5625": "9/16", ".6875": "11/16", ".8125": "13/16", ".9375": "15/16"
    }
    
    for attr_name in ["length", "height", "width", "weight", "volume"]:
        val = getattr(product, attr_name)
        uom_val = getattr(product, f"{attr_name}_uom", None)
        
        # Only convert if UOM is explicitly imperial or null
        is_imperial = uom_val is None or str(uom_val).lower() in ['in', 'inch', 'inches', 'lb', 'lbs', 'oz', 'ozs']
        
        if val and "." in val and is_imperial:
            try:
                parts = val.split(".")
                decimal_part = "." + parts[1]
                if decimal_part in decimal_to_fraction:
                    frac = decimal_to_fraction[decimal_part]
                    new_val = f"{parts[0]}-{frac}" if parts[0] != "0" else frac
                    setattr(product, attr_name, new_val)
            except Exception:
                pass
                
    # 5. LOV Check (omitted as per Hackathon Update - relying on LLM)
                    
    # 6. Final Confidence Score
    if not has_web_data:
        confidence -= 0.3
        
    product.confidence_score = max(0.0, round(confidence, 2))
    product.needs_human_review = product.confidence_score < 0.6
    
    if product.needs_human_review:
        product.review_reason = "Low confidence score"
        
    return product
