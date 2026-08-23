from pydantic import BaseModel, Field
from typing import List, Optional
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / "docs" / "Unihack_ Expected Output - Delivery Format.csv"

# Read GOLDEN_RECORD_COLUMNS once
with open(CSV_PATH, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    GOLDEN_RECORD_COLUMNS = next(reader)

class AttributeTriad(BaseModel):
    label: Optional[str] = None
    value: Optional[str] = None
    uom: Optional[str] = None

class EnrichedProduct(BaseModel):
    # URLs
    mfr_url: Optional[str] = Field(None, alias="MFR URL")
    ref_urls: List[Optional[str]] = Field(default_factory=list, max_length=5)
    
    # IDs
    part_number: Optional[str] = Field(None, alias="PART_NUMBER")
    dept: Optional[str] = Field(None, alias="Dept")
    class_: Optional[str] = Field(None, alias="Class")
    fine: Optional[str] = Field(None, alias="Fine")
    sku: Optional[str] = Field(None, alias="SKU - MY_PART_NUMBER")
    
    # Input verbatim
    mfg_part_num: Optional[str] = Field(None, alias="Mfg_Part_Num")
    part_desc: Optional[str] = Field(None, alias="Part_Desc")
    e1_brand: Optional[str] = Field(None, alias="E1_Brand")
    unilog_brand: Optional[str] = Field(None, alias="Unilog_Brand")
    dib_brand: Optional[str] = Field(None, alias="DIB_Brand")
    part_manuf: Optional[str] = Field(None, alias="Part_Manuf")
    
    # Identity
    manufacturer_name: Optional[str] = Field(None, alias="MANUFACTURER_NAME")
    brand_name: Optional[str] = Field(None, alias="BRAND_NAME")
    trade_name: Optional[str] = Field(None, alias="TRADE_NAME")
    manufacturer_part_number: Optional[str] = Field(None, alias="MANUFACTURER_PART_NUMBER")
    alternate_part_number: Optional[str] = Field(None, alias="ALTERNATE_PART_NUMBER")
    
    # Taxonomy
    classpath: Optional[str] = Field(None, alias="Classpath")
    
    # Descriptions
    mobile_desc: Optional[str] = Field(None, alias="MOBILE_DESC")
    invoice_desc: Optional[str] = Field(None, alias="INVOICE_DESC")
    short_desc: Optional[str] = Field(None, alias="SHORT_DESC")
    long_desc1: Optional[str] = Field(None, alias="LONG_DESC1")
    retail_desc: Optional[str] = Field(None, alias="RETAIL_DESC")
    marketing_description: Optional[str] = Field(None, alias="MARKETING_DESCRIPTION")
    
    # Features
    item_features: List[Optional[str]] = Field(default_factory=list, max_length=20)
    
    # Product Meta
    with_: Optional[str] = Field(None, alias="With")
    standard_approvals: Optional[str] = Field(None, alias="Standard/Approvals")
    prop_65: Optional[str] = Field(None, alias="Prop 65")
    application: Optional[str] = Field(None, alias="Application")
    includes: Optional[str] = Field(None, alias="Includes")
    product_name: Optional[str] = Field(None, alias="Product Name")
    
    # Attributes
    attributes: List[AttributeTriad] = Field(default_factory=list, max_length=50)
    
    # Product Codes
    upc: Optional[str] = Field(None, alias="UPC")
    ean: Optional[str] = Field(None, alias="EAN")
    gtin: Optional[str] = Field(None, alias="GTIN")
    unspsc: Optional[str] = Field(None, alias="UNSPSC")
    
    # Commercial
    warranty: Optional[str] = Field(None, alias="Warranty")
    list_price: Optional[str] = Field(None, alias="List Price")
    selling_qty: Optional[str] = Field(None, alias="Selling Qty")
    selling_uom: Optional[str] = Field(None, alias="Selling UOM")
    standard_packaging_information: Optional[str] = Field(None, alias="Standard Packaging Information")
    
    # Dimensions
    length: Optional[str] = Field(None, alias="LENGTH")
    length_uom: Optional[str] = Field(None, alias="LENGTH_UOM")
    height: Optional[str] = Field(None, alias="HEIGHT")
    height_uom: Optional[str] = Field(None, alias="HEIGHT_UOM")
    width: Optional[str] = Field(None, alias="WIDTH")
    width_uom: Optional[str] = Field(None, alias="WIDTH_UOM")
    weight: Optional[str] = Field(None, alias="WEIGHT")
    weight_uom: Optional[str] = Field(None, alias="WEIGHT_UOM")
    volume: Optional[str] = Field(None, alias="VOLUME")
    volume_uom: Optional[str] = Field(None, alias="VOLUME_UOM")
    
    # Digital Assets (Images)
    product_image: Optional[str] = Field(None, alias="Product Image")
    alternate_images: List[Optional[str]] = Field(default_factory=list, max_length=4)
    
    # Digital Assets (Docs)
    sds: Optional[str] = Field(None, alias="SDS")
    sds_1: Optional[str] = Field(None, alias="SDS_1")
    warranty_information: Optional[str] = Field(None, alias="Warranty Information")
    catalog: Optional[str] = Field(None, alias="Catalog")
    specification_sheet: Optional[str] = Field(None, alias="Specification Sheet")
    instruction_installation_manual: Optional[str] = Field(None, alias="Instruction/Installation Manual")
    service_manual: Optional[str] = Field(None, alias="Service Manual")
    owners_user_manual: Optional[str] = Field(None, alias="Owners/User Manual")
    line_drawing: Optional[str] = Field(None, alias="Line Drawing")
    mtr: Optional[str] = Field(None, alias="MTR")
    rohs: Optional[str] = Field(None, alias="RoHS")
    full_engineering_drawing: Optional[str] = Field(None, alias="Full Engineering Drawing")
    energy_star_guide: Optional[str] = Field(None, alias="Energy Star Guide")
    technical_bulletin: Optional[str] = Field(None, alias="Technical Bulletin")
    submittal: Optional[str] = Field(None, alias="Submittal")
    compatibility_chart: Optional[str] = Field(None, alias="Compatibility Chart")
    size_chart: Optional[str] = Field(None, alias="Size Chart")
    product_label_insert: Optional[str] = Field(None, alias="Product Label/Insert")
    video_link: Optional[str] = Field(None, alias="Video Link")
    video_link_1: Optional[str] = Field(None, alias="Video Link 1")
    
    # Flags
    country_of_origin: Optional[str] = Field(None, alias="Country Of Origin")
    discontinued: Optional[str] = Field(None, alias="Discontinued")
    actual_image: Optional[str] = Field(None, alias="Actual Image (Yes/No)")

    # Internal pipeline fields
    confidence_score: Optional[float] = None
    needs_human_review: bool = False
    review_reason: Optional[str] = None

def flatten_enriched_product(product: EnrichedProduct) -> dict:
    flat = {}
    
    # Depending on pydantic version
    if hasattr(product, "model_dump"):
        data = product.model_dump(by_alias=True)
    else:
        data = product.dict(by_alias=True)
    
    # Initialize all golden record columns to None
    for col in GOLDEN_RECORD_COLUMNS:
        flat[col] = None

    # Normal scalar fields
    for k, v in data.items():
        if k in GOLDEN_RECORD_COLUMNS:
            flat[k] = v

    # Ref URLs (1-5)
    ref_urls = data.get("ref_urls", [])
    for i, url in enumerate(ref_urls):
        if i < 5:
            flat[f"Ref URL {i+1}"] = url

    # Item Features (1-20)
    features = data.get("item_features", [])
    for i, feat in enumerate(features):
        if i < 20:
            flat[f"ITEM_FEATURES_{i+1}"] = feat

    # Attributes (1-50)
    attrs = data.get("attributes", [])
    for i, attr in enumerate(attrs):
        if i < 50:
            idx = i + 1
            flat[f"ATTRIBUTE_LABEL {idx}"] = attr.get("label")
            flat[f"ATTRIBUTE_VALUE {idx}"] = attr.get("value")
            flat[f"ATTRIBUTE_UOM {idx}"] = attr.get("uom")

    # Alternate Images (1-4)
    alt_imgs = data.get("alternate_images", [])
    for i, img in enumerate(alt_imgs):
        if i < 4:
            flat[f"Alternate Image {i+1}"] = img

    return flat
