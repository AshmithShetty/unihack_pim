from pydantic import BaseModel, Field
from typing import List, Optional
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

_GOLDEN_RECORD_HEADER = "MFR URL,Ref URL 1,Ref URL 2,Ref URL 3,Ref URL 4,Ref URL 5,PART_NUMBER,Dept,Class,Fine,SKU - MY_PART_NUMBER,Mfg_Part_Num,Part_Desc,E1_Brand,Unilog_Brand,DIB_Brand,Part_Manuf,MANUFACTURER_NAME,BRAND_NAME,TRADE_NAME,MANUFACTURER_PART_NUMBER,ALTERNATE_PART_NUMBER,Classpath,MOBILE_DESC,INVOICE_DESC,SHORT_DESC,LONG_DESC1,RETAIL_DESC,MARKETING_DESCRIPTION,ITEM_FEATURES_1,ITEM_FEATURES_2,ITEM_FEATURES_3,ITEM_FEATURES_4,ITEM_FEATURES_5,ITEM_FEATURES_6,ITEM_FEATURES_7,ITEM_FEATURES_8,ITEM_FEATURES_9,ITEM_FEATURES_10,ITEM_FEATURES_11,ITEM_FEATURES_12,ITEM_FEATURES_13,ITEM_FEATURES_14,ITEM_FEATURES_15,ITEM_FEATURES_16,ITEM_FEATURES_17,ITEM_FEATURES_18,ITEM_FEATURES_19,ITEM_FEATURES_20,With,Standard/Approvals,Prop 65,Application,Includes,Product Name,ATTRIBUTE_LABEL 1,ATTRIBUTE_VALUE 1,ATTRIBUTE_UOM 1,ATTRIBUTE_LABEL 2,ATTRIBUTE_VALUE 2,ATTRIBUTE_UOM 2,ATTRIBUTE_LABEL 3,ATTRIBUTE_VALUE 3,ATTRIBUTE_UOM 3,ATTRIBUTE_LABEL 4,ATTRIBUTE_VALUE 4,ATTRIBUTE_UOM 4,ATTRIBUTE_LABEL 5,ATTRIBUTE_VALUE 5,ATTRIBUTE_UOM 5,ATTRIBUTE_LABEL 6,ATTRIBUTE_VALUE 6,ATTRIBUTE_UOM 6,ATTRIBUTE_LABEL 7,ATTRIBUTE_VALUE 7,ATTRIBUTE_UOM 7,ATTRIBUTE_LABEL 8,ATTRIBUTE_VALUE 8,ATTRIBUTE_UOM 8,ATTRIBUTE_LABEL 9,ATTRIBUTE_VALUE 9,ATTRIBUTE_UOM 9,ATTRIBUTE_LABEL 10,ATTRIBUTE_VALUE 10,ATTRIBUTE_UOM 10,ATTRIBUTE_LABEL 11,ATTRIBUTE_VALUE 11,ATTRIBUTE_UOM 11,ATTRIBUTE_LABEL 12,ATTRIBUTE_VALUE 12,ATTRIBUTE_UOM 12,ATTRIBUTE_LABEL 13,ATTRIBUTE_VALUE 13,ATTRIBUTE_UOM 13,ATTRIBUTE_LABEL 14,ATTRIBUTE_VALUE 14,ATTRIBUTE_UOM 14,ATTRIBUTE_LABEL 15,ATTRIBUTE_VALUE 15,ATTRIBUTE_UOM 15,ATTRIBUTE_LABEL 16,ATTRIBUTE_VALUE 16,ATTRIBUTE_UOM 16,ATTRIBUTE_LABEL 17,ATTRIBUTE_VALUE 17,ATTRIBUTE_UOM 17,ATTRIBUTE_LABEL 18,ATTRIBUTE_VALUE 18,ATTRIBUTE_UOM 18,ATTRIBUTE_LABEL 19,ATTRIBUTE_VALUE 19,ATTRIBUTE_UOM 19,ATTRIBUTE_LABEL 20,ATTRIBUTE_VALUE 20,ATTRIBUTE_UOM 20,ATTRIBUTE_LABEL 21,ATTRIBUTE_VALUE 21,ATTRIBUTE_UOM 21,ATTRIBUTE_LABEL 22,ATTRIBUTE_VALUE 22,ATTRIBUTE_UOM 22,ATTRIBUTE_LABEL 23,ATTRIBUTE_VALUE 23,ATTRIBUTE_UOM 23,ATTRIBUTE_LABEL 24,ATTRIBUTE_VALUE 24,ATTRIBUTE_UOM 24,ATTRIBUTE_LABEL 25,ATTRIBUTE_VALUE 25,ATTRIBUTE_UOM 25,ATTRIBUTE_LABEL 26,ATTRIBUTE_VALUE 26,ATTRIBUTE_UOM 26,ATTRIBUTE_LABEL 27,ATTRIBUTE_VALUE 27,ATTRIBUTE_UOM 27,ATTRIBUTE_LABEL 28,ATTRIBUTE_VALUE 28,ATTRIBUTE_UOM 28,ATTRIBUTE_LABEL 29,ATTRIBUTE_VALUE 29,ATTRIBUTE_UOM 29,ATTRIBUTE_LABEL 30,ATTRIBUTE_VALUE 30,ATTRIBUTE_UOM 30,ATTRIBUTE_LABEL 31,ATTRIBUTE_VALUE 31,ATTRIBUTE_UOM 31,ATTRIBUTE_LABEL 32,ATTRIBUTE_VALUE 32,ATTRIBUTE_UOM 32,ATTRIBUTE_LABEL 33,ATTRIBUTE_VALUE 33,ATTRIBUTE_UOM 33,ATTRIBUTE_LABEL 34,ATTRIBUTE_VALUE 34,ATTRIBUTE_UOM 34,ATTRIBUTE_LABEL 35,ATTRIBUTE_VALUE 35,ATTRIBUTE_UOM 35,ATTRIBUTE_LABEL 36,ATTRIBUTE_VALUE 36,ATTRIBUTE_UOM 36,ATTRIBUTE_LABEL 37,ATTRIBUTE_VALUE 37,ATTRIBUTE_UOM 37,ATTRIBUTE_LABEL 38,ATTRIBUTE_VALUE 38,ATTRIBUTE_UOM 38,ATTRIBUTE_LABEL 39,ATTRIBUTE_VALUE 39,ATTRIBUTE_UOM 39,ATTRIBUTE_LABEL 40,ATTRIBUTE_VALUE 40,ATTRIBUTE_UOM 40,ATTRIBUTE_LABEL 41,ATTRIBUTE_VALUE 41,ATTRIBUTE_UOM 41,ATTRIBUTE_LABEL 42,ATTRIBUTE_VALUE 42,ATTRIBUTE_UOM 42,ATTRIBUTE_LABEL 43,ATTRIBUTE_VALUE 43,ATTRIBUTE_UOM 43,ATTRIBUTE_LABEL 44,ATTRIBUTE_VALUE 44,ATTRIBUTE_UOM 44,ATTRIBUTE_LABEL 45,ATTRIBUTE_VALUE 45,ATTRIBUTE_UOM 45,ATTRIBUTE_LABEL 46,ATTRIBUTE_VALUE 46,ATTRIBUTE_UOM 46,ATTRIBUTE_LABEL 47,ATTRIBUTE_VALUE 47,ATTRIBUTE_UOM 47,ATTRIBUTE_LABEL 48,ATTRIBUTE_VALUE 48,ATTRIBUTE_UOM 48,ATTRIBUTE_LABEL 49,ATTRIBUTE_VALUE 49,ATTRIBUTE_UOM 49,ATTRIBUTE_LABEL 50,ATTRIBUTE_VALUE 50,ATTRIBUTE_UOM 50,UPC,EAN,GTIN,UNSPSC,Warranty,List Price,Selling Qty,Selling UOM,Standard Packaging Information,LENGTH,LENGTH_UOM,HEIGHT,HEIGHT_UOM,WIDTH,WIDTH_UOM,WEIGHT,WEIGHT_UOM,VOLUME,VOLUME_UOM,Product Image,Alternate Image 1,Alternate Image 2,Alternate Image 3,Alternate Image 4,SDS,SDS_1,Warranty Information,Catalog,Specification Sheet,Instruction/Installation Manual,Service Manual,Owners/User Manual,Line Drawing,MTR,RoHS,Full Engineering Drawing,Energy Star Guide,Technical Bulletin,Submittal,Compatibility Chart,Size Chart,Product Label/Insert,Video Link,Video Link 1,Country Of Origin,Discontinued,Actual Image (Yes/No)"

GOLDEN_RECORD_COLUMNS = _GOLDEN_RECORD_HEADER.split(",")

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
