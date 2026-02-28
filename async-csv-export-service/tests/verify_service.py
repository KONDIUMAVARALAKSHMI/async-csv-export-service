import requests
import time
import sys
import gzip
import io

BASE_URL = "http://localhost:8080"

def wait_for_ready():
    print("Checking if service is ready...")
    for _ in range(30):
        try:
            resp = requests.get(f"{BASE_URL}/health")
            if resp.status_code == 200:
                print("Service is UP!")
                return True
        except:
            pass
        time.sleep(2)
    return False

def test_full_export():
    print("\n--- Testing Full Export (10M Rows) ---")
    resp = requests.post(f"{BASE_URL}/exports/csv")
    if resp.status_code != 202:
        print(f"FAILED to initiate: {resp.status_code}")
        return None
    
    export_id = resp.json()["exportId"]
    print(f"Job initiated: {export_id}")
    
    while True:
        status_resp = requests.get(f"{BASE_URL}/exports/{export_id}/status")
        data = status_resp.json()
        status = data["status"]
        progress = data["progress"]
        print(f"Status: {status} | Progress: {progress['percentage']}% ({progress['processedRows']}/{progress['totalRows']})", end="\r")
        
        if status == "completed":
            print("\nExport completed successfully!")
            return export_id
        if status == "failed":
            print(f"\nExport FAILED: {data['error']}")
            return None
        
        time.sleep(5)

def test_download(export_id):
    print("\n--- Testing Download (Resumable & Gzip) ---")
    
    # 1. Byte Range
    headers = {"Range": "bytes=0-1023"}
    resp = requests.get(f"{BASE_URL}/exports/{export_id}/download", headers=headers)
    if resp.status_code == 206 and len(resp.content) == 1024:
        print("PASS: Resumable download (Range: 0-1023) works.")
    else:
        print(f"FAIL: Resumable download returned {resp.status_code}, length {len(resp.content)}")

    # 2. Gzip
    headers = {"Accept-Encoding": "gzip"}
    resp = requests.get(f"{BASE_URL}/exports/{export_id}/download", headers=headers)
    if resp.headers.get("Content-Encoding") == "gzip":
        print("PASS: Gzip compression confirmed in headers.")
        try:
            # Try to decompress
            content = gzip.decompress(resp.content)
            print(f"PASS: Decompressed size: {len(content)} bytes.")
        except Exception as e:
            print(f"FAIL: Decompression failed: {e}")
    else:
        print(f"FAIL: Gzip header missing. Headers: {resp.headers}")

def test_cancel():
    print("\n--- Testing Job Cancellation ---")
    resp = requests.post(f"{BASE_URL}/exports/csv")
    export_id = resp.json()["exportId"]
    print(f"Job started: {export_id}")
    
    # Wait a bit for processing to start
    time.sleep(2)
    
    print("Sending DELETE request...")
    del_resp = requests.delete(f"{BASE_URL}/exports/{export_id}")
    if del_resp.status_code == 204:
        print("PASS: Cancellation request accepted.")
        
        status_resp = requests.get(f"{BASE_URL}/exports/{export_id}/status")
        status = status_resp.json()["status"]
        if status == "cancelled":
            print("PASS: Job status updated to 'cancelled'.")
        else:
            print(f"NOTE: Job status is '{status}'. Expected 'cancelled'.")
    else:
        print(f"FAIL: Cancellation failed with {del_resp.status_code}")

def test_concurrency():
    print("\n--- Testing 3 Concurrent Jobs ---")
    job_ids = []
    for i in range(3):
        resp = requests.post(f"{BASE_URL}/exports/csv?country_code=US")
        jid = resp.json()["exportId"]
        job_ids.append(jid)
        print(f"Started job {i+1}: {jid}")

    completed = [False] * 3
    while not all(completed):
        for i, jid in enumerate(job_ids):
            if not completed[i]:
                status = requests.get(f"{BASE_URL}/exports/{jid}/status").json()["status"]
                if status == "completed":
                    completed[i] = True
                    print(f"Job {i+1} ({jid}) completed!")
        time.sleep(2)
    print("PASS: All 3 concurrent jobs reached completion stage.")

if __name__ == "__main__":
    if not wait_for_ready():
        print("Service did not become ready in time. Please make sure docker-compose is running.")
        sys.exit(1)
    
    eid = test_full_export()
    if eid:
        test_download(eid)
    
    test_cancel()
    test_concurrency()
    print("\nAll tests finished!")
