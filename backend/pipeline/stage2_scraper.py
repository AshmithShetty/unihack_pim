import asyncio
import os
import urllib.parse
from typing import Dict, Any
from crawl4ai import AsyncWebCrawler
from groq import Groq
import aiohttp
import fitz

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

async def generate_smart_query(filled_row: dict) -> str:
    """Pillar 1: Uses Gemini to compute the optimal search query, stripping out bad distributor data."""
    prompt = f"""
    You are an expert search query generator.
    Given this messy product row, extract ONLY the Brand and the Manufacturer Part Number to form a perfect Google search query.
    Do NOT include distributor names, internal notes like 'Display Only', or generic terms.
    If the brand is not explicitly stated, try to infer it from the description.
    Return ONLY the raw search query string (e.g. 'GE PDD415PYYFS dishwasher').
    
    Row Data: {filled_row}
    """
    
    def call_groq():
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1024
        )
        raw_text = response.choices[0].message.content
        import re
        clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()
        return clean_text
        
    query = await asyncio.to_thread(call_groq)
    return query

async def fetch_ddg_links(crawler: AsyncWebCrawler, search_query: str, brand_name: str = None) -> list:
    """Pillar 2: The Redirect Unmasker. Decodes DuckDuckGo redirects to guarantee we get the real links."""
    encoded_query = urllib.parse.quote_plus(search_query)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    result = await crawler.arun(url=search_url)
    
    links = []
    
    import re
    # Extract raw uddg redirects using regex on the raw HTML to bypass crawl4ai's link parser which misses them
    redirects = re.findall(r'uddg=(https[^&"\'\\]+)', result.html)
    
    for redirect in redirects:
        href = urllib.parse.unquote(redirect)
        links.append(href)
        
    if brand_name:
        brand_clean = re.sub(r'[^a-zA-Z0-9]', '', brand_name.lower())
        if brand_clean and len(brand_clean) > 2:
            # Sort links, prioritizing those that contain the brand name
            links.sort(key=lambda x: 0 if brand_clean in x.lower() else 1)
                
    return links

async def run_stage2_scraper(filled_row: dict, row_data: dict) -> Dict[str, Any]:
    page_text = ""
    mfr_url = None
    pdf_urls = []
    pdf_texts = {}
    
    # Pillar 1: Smart Query Generation
    try:
        base_query = await generate_smart_query(filled_row)
    except Exception as e:
        print(f"Query generation failed: {e}")
        # Robust Fallback: Pull from row_data instead of filled_row in case mapping failed
        mpn = filled_row.get('Mfg_Part_Num') or row_data.get('Mfg_Part_Num', '')
        desc = filled_row.get('Part_Desc') or row_data.get('Part_Desc', '')
        base_query = f"{mpn} {desc}".strip()
        if not base_query:
            # Universal fallback: join up to the first 3 string columns from raw row_data
            str_vals = [str(v) for v in row_data.values() if v and isinstance(v, (str, int, float))]
            base_query = " ".join(str_vals[:3])
            if not base_query:
                base_query = "Product" # Absolute fallback
            
    print(f"\n[AI Search Engine] Generated Smart Query: {base_query}\n")
    
    brand_name = filled_row.get("BRAND_NAME") or filled_row.get("MANUFACTURER_NAME")
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        try:
            # Step 1: Find the official product page
            links = await fetch_ddg_links(crawler, base_query, brand_name)
            
            if links:
                mfr_url = links[0]
                print(f"[AI Search Engine] Official Product Page Found: {mfr_url}")
                await asyncio.sleep(1) # Rate limit
                
                prod_result = await crawler.arun(url=mfr_url)
                page_text = prod_result.markdown
                
                # Extract PDFs from main page
                if prod_result.links:
                    all_links = prod_result.links.get("internal", []) + prod_result.links.get("external", [])
                    for link_dict in all_links:
                        href = link_dict.get("href", "")
                        if href.lower().endswith(".pdf") and href.startswith("http"):
                            pdf_urls.append(href)
                            
            # Pillar 3: Dedicated Spec Sheet Discovery
            pdf_query = f"filetype:pdf {base_query} spec sheet"
            pdf_links = await fetch_ddg_links(crawler, pdf_query, brand_name)
            
            for plink in pdf_links:
                if plink.lower().endswith(".pdf"):
                    pdf_urls.append(plink)
                    
            pdf_urls = list(set(pdf_urls))[:5] # Unique and limit to 5
            
            if pdf_urls:
                print(f"[AI Search Engine] Spec Sheets Found: {len(pdf_urls)} PDFs")
            
            # Crawl PDFs using aiohttp and PyMuPDF to avoid Playwright download crashes
            async with aiohttp.ClientSession() as session:
                for pdf_url in pdf_urls:
                    try:
                        async with session.get(pdf_url, timeout=10) as response:
                            if response.status == 200:
                                pdf_bytes = await response.read()
                                
                                # Extract text with PyMuPDF in a thread
                                def extract_pdf_text(b):
                                    doc = fitz.open(stream=b, filetype="pdf")
                                    text = ""
                                    for page in doc:
                                        text += page.get_text()
                                    return text
                                    
                                pdf_text = await asyncio.to_thread(extract_pdf_text, pdf_bytes)
                                pdf_texts[pdf_url] = pdf_text
                    except Exception as e:
                        print(f"Error extracting PDF {pdf_url}: {e}")
                        
        except Exception as e:
            print(f"Scraper error: {e}")
            
    return {
        "page_text": page_text,
        "pdf_texts": pdf_texts,
        "mfr_url": mfr_url,
        "ref_urls": pdf_urls
    }
