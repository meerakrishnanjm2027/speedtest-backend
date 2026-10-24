from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import secrets
import time
import requests

app = FastAPI(title="Personal Speed Test API")

# --- CORS Configuration ---
# Allows your Vercel/Netlify frontend to communicate with this Render backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper: Fast Random Data Generation ---
# Uses secrets.token_bytes which is faster than os.urandom for streaming
def generate_random_data(size: int):
    chunk_size = 65536  # 64KB chunks are optimal for TCP throughput
    generated = 0
    while generated < size:
        to_generate = min(chunk_size, size - generated)
        yield secrets.token_bytes(to_generate)
        generated += to_generate

# --- 1. Network Info Endpoint (Optimized) ---
@app.get("/network-info")
async def get_network_info():
    """
    Fetches client IP, ISP, and Location using ipinfo.io.
    Includes fallback logic if the API is rate-limited or unreachable.
    """
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "ip": data.get("ip", "N/A"),
                "isp": data.get("org", "Unknown ISP"),
                "city": data.get("city", "Unknown"),
                "region": data.get("region", ""),
                "country": data.get("country", ""),
                "server_location": "Render Cloud (Global)",
                "server_name": "SpeedTest-Backend-v2"
            }
        else:
            # Handle API errors gracefully
            return {
                "ip": "Unavailable",
                "isp": "API Rate Limit Reached",
                "city": "Try again later",
                "server_location": "Render Cloud (Global)"
            }
            
    except requests.exceptions.RequestException as e:
        # Handle network timeouts or DNS failures
        return {
            "ip": "Error",
            "isp": "Connection Failed",
            "city": str(e)[:50],
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
    """
    Streams random bytes for download testing.
    'connections' param tells frontend how many parallel streams to open.
    """
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
    """
    Tells the frontend exactly how to run the test for maximum accuracy.
    Matches industry standards like Ookla.
    """
    return {
        "download": {
            "sizes": [1000000, 5000000, 25000000],
            "threads": 4,       # Use 4 parallel connections
            "warmup_time": 2    # Ignore first 2 seconds (ramp-up phase)
        },
        "upload": {
            "sizes": [1000000, 5000000, 10000000],
            "threads": 3,       # Use 3 parallel connections
            "warmup_time": 2
        }
    }
