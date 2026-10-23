from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI()

# Allow React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# 1. PING: Measure latency
# -------------------------------------------------------------------
@app.get("/ping")
async def ping():
    return {"status": "ok"}


# -------------------------------------------------------------------
# 2. DOWNLOAD: Stream random bytes to the client
# -------------------------------------------------------------------
@app.get("/download")
async def download(size: int = 25000000):  # Default 25MB
    def generate_bytes():
        chunk_size = 65536  # 64KB chunks
        sent = 0
        while sent < size:
            yield os.urandom(min(chunk_size, size - sent))
            sent += chunk_size

    return StreamingResponse(generate_bytes(), media_type="application/octet-stream")


# -------------------------------------------------------------------
# 3. UPLOAD: Accept a file and measure its size
# -------------------------------------------------------------------
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    return {"received_bytes": len(content)}


# -------------------------------------------------------------------
# 4. NETWORK INFO: Client's public IP, ISP, and city via ipapi.co
# -------------------------------------------------------------------
@app.get("/network-info")
async def get_network_info(request: Request):
    """
    Fetches the *client's* public IP, ISP, and City using ipapi.co.

    Note: We pass the client's real IP (from X-Forwarded-For, set by
    Render's proxy) to ipapi.co. Without this, the API would return
    Render's server IP → "Amazon Technologies Inc." instead of the
    user's actual ISP like "Jio" or "ACT Fibernet".
    """
    try:
        # Get the client IP from the proxy headers (Render sets this)
        forwarded = request.headers.get("x-forwarded-for")
        user_ip = forwarded.split(",")[0].strip() if forwarded else request.client.host

        # Look up the client's IP (not the server's)
        response = requests.get(f"https://ipapi.co/{user_ip}/json/", timeout=5)
        data = response.json()

        return {
            "ip": data.get("ip", user_ip),
            "isp": data.get("org", "Unknown ISP"),
            "city": data.get("city", "Unknown"),
            "region": data.get("region", ""),
            "country": data.get("country_name", ""),
            "server_location": "Render Cloud (Global)",
            "server_name": "SpeedTest-Backend-v2",
        }
    except Exception as e:
        return {"error": "Could not fetch network info", "details": str(e)}
