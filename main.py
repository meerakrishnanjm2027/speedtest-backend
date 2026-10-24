from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import secrets
import time
import requests

app = FastAPI(title="Personal Speed Test API")

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper: Fast Random Data Generation ---
def generate_random_data(size: int):
    chunk_size = 65536
    generated = 0
    while generated < size:
        to_generate = min(chunk_size, size - generated)
        yield secrets.token_bytes(to_generate)
        generated += to_generate

# --- 1. Network Info Endpoint (Dual-API Fallback) ---
@app.get("/network-info")
async def get_network_info():
    """
    Tries ip-api.com first, falls back to ipinfo.io.
    ALWAYS returns consistent keys: ip, isp, city, region, country
    """
    apis = [
        {
            "name": "ip-api.com",
            "url": "http://ip-api.com/json/?fields=status,message,country,regionName,city,isp,query",
            "parser": lambda d: {
                "ip": d.get("query"),
                "isp": d.get("isp"),
                "city": d.get("city"),
                "region": d.get("regionName"),
                "country": d.get("country")
            } if d.get("status") == "success" else None
        },
        {
            "name": "ipinfo.io",
            "url": "https://ipinfo.io/json",
            "parser": lambda d: {
                "ip": d.get("ip"),
                "isp": d.get("org"),  # ipinfo uses 'org' instead of 'isp'
                "city": d.get("city"),
                "region": d.get("region"),
                "country": d.get("country")
            }
        }
    ]
    
    for api in apis:
        try:
            resp = requests.get(api["url"], timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                parsed = api["parser"](data)
                
                # Only return if we got a valid IP address
                if parsed and parsed.get("ip"):
                    print(f"[NETWORK] ✅ Success via {api['name']}")
                    return {
                        **parsed,
                        "server_location": "Render Cloud (Global)",
                        "server_name": "SpeedTest-Backend-v2"
                    }
        except Exception as e:
            print(f"[NETWORK] ❌ Failed {api['name']}: {e}")
            continue
    
    # All APIs failed
    print("[NETWORK] ️ All APIs unreachable")
    return {
        "ip": "Unavailable",
        "isp": "All APIs Unreachable",
        "city": "Check Render Logs",
        "region": "",
        "country": "",
        "server_location": "Render Cloud (Global)"
    }

# --- 2. Ping Test ---
@app.get("/ping")
async def ping():
    return {"status": "ok", "timestamp": time.time()}

# --- 3. Download Test (Multi-Thread Ready) ---
@app.get("/download")
async def download(
    size: int = Query(default=25000000), 
    connections: int = Query(default=1)
):
    return StreamingResponse(
        generate_random_data(size), 
        media_type="application/octet-stream",
        headers={"Content-Length": str(size)}
    )

# --- 4. Upload Test ---
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    return {"received_bytes": len(content)}

# --- 5. Test Configuration ---
@app.get("/config")
async def get_config():
    return {
        "download": {
            "sizes": [1000000, 5000000, 25000000],
            "threads": 4,
            "warmup_time": 2
        },
        "upload": {
            "sizes": [1000000, 5000000, 10000000],
            "threads": 3,
            "warmup_time": 2
        }
    }
