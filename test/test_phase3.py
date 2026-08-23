import urllib.request
import urllib.error
import json
import time
import os
import mimetypes

BASE_URL = "http://127.0.0.1:8000"
CSV_PATH = os.path.join("..", "docs", "Unihack_Input.csv")

def encode_multipart_formdata(fields, files):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = []
    
    for key, value in fields.items():
        body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n")
        
    for key, filepath in files.items():
        filename = os.path.basename(filepath)
        mimetype = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
        with open(filepath, 'rb') as f:
            file_content = f.read()
            
        body.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"; filename=\"{filename}\"\r\nContent-Type: {mimetype}\r\n\r\n".encode('utf-8'))
        body.append(file_content)
        body.append(b"\r\n")
        
    body.append(f"--{boundary}--\r\n".encode('utf-8'))
    
    content_type = f"multipart/form-data; boundary={boundary}"
    
    # Combine bytes
    final_body = b""
    for item in body:
        final_body += item if isinstance(item, bytes) else item.encode('utf-8')
        
    return content_type, final_body

def make_request(method, endpoint, data=None, is_json=True, is_multipart=False):
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if is_multipart:
        content_type, body = encode_multipart_formdata({}, data)
        headers["Content-Type"] = content_type
    elif is_json and data:
        body = json.dumps(data).encode('utf-8')
        headers["Content-Type"] = "application/json"
    else:
        body = None

    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read()
            if is_json:
                return json.loads(resp_body)
            return resp_body
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        raise e

def run_test():
    print("🚀 Starting Phase 3 End-to-End Test...")
    
    # 1. Create Project
    print("\n1. Creating new project...")
    proj_resp = make_request("POST", "/api/projects", {"project_name": "Terminal Test Phase 3"})
    project_id = proj_resp["project_id"]
    print(f"✅ Project Created! ID: {project_id}")
    
    # 2. Upload CSV
    print(f"\n2. Uploading CSV ({CSV_PATH})...")
    upload_resp = make_request("POST", f"/api/projects/{project_id}/upload", data={"file": CSV_PATH}, is_multipart=True, is_json=True)
    mapping = upload_resp.get("mapping_proposal", {})
    print(f"✅ CSV Uploaded! Mapping generated with {len(mapping)} columns.")
    
    # 3. Confirm Mapping (Triggers Background Task)
    print("\n3. Confirming Mapping & Starting Background Enrichment...")
    make_request("POST", f"/api/projects/{project_id}/confirm", data=mapping)
    print("✅ Background task started!")
    
    # 4. Polling Rows
    print("\n4. Polling for Completion (this takes time since it crawls the web)...")
    seen_failed = set()
    
    while True:
        rows_resp = make_request("GET", f"/api/projects/{project_id}/rows")
        rows = rows_resp.get("rows", [])
        
        if not rows:
            print("⏳ No rows returned yet...")
            time.sleep(2)
            continue
            
        pending = sum(1 for r in rows if r["status"] == "pending")
        running = sum(1 for r in rows if r["status"] == "running")
        done = sum(1 for r in rows if r["status"] == "done")
        failed = sum(1 for r in rows if r["status"] == "failed")
        
        total = len(rows)
        print(f"   Status -> Pending: {pending} | Running: {running} | Done: {done} | Failed: {failed} | Total: {total}")
        
        # Print newly failed rows instantly
        for r in rows:
            if r["status"] == "failed" and r["row_id"] not in seen_failed:
                print(f"   ❌ Row {r['row_id']} Failed: {r.get('review_reason')}")
                seen_failed.add(r["row_id"])
        
        if done + failed == total and total > 0:
            print("\n✅ All rows processed!")
            
            if failed > 0:
                print(f"\n❌ {failed} rows failed. Here is the reason for the first failure:")
                first_failed = next(r for r in rows if r["status"] == "failed")
                print(f"   Reason: {first_failed.get('review_reason', 'Unknown error')}")
                
            if done > 0:
                print("\n🔍 Sample of first enriched row:")
                first_done = next(r for r in rows if r["status"] == "done")
                filled = {k: v for k, v in first_done.items() if v}
                print(json.dumps(filled, indent=2))
                
            break
            
        time.sleep(3)

    # 5. Export CSV
    print("\n5. Testing Export Endpoint...")
    try:
        csv_bytes = make_request("GET", f"/api/projects/{project_id}/export", is_json=False)
        print(f"✅ Export successful! Downloaded {len(csv_bytes)} bytes of CSV data.")
    except Exception as e:
        print(f"❌ Export failed: {e}")

    print("\n🎉 Phase 3 Test Complete!")

if __name__ == "__main__":
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: Cannot find {CSV_PATH}. Make sure you run this script from the 'test' directory.")
    else:
        run_test()
