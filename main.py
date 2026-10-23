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
    allow_credentials=False, # Changed to False to fix CORS on Netlify
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
    """
    try:
        # Get the client IP from the proxy headers (Render sets this)
        forwarded = request.headers.get("x-forwarded-for")
        user_ip = forwarded.split(",")[0].strip() if forwarded else request.client.host

        # If testing locally, the IP will be 127.0.0.1 and fail. 
        # This fixes that so it works locally AND on Render.
        is_private = (
            user_ip in ("127.0.0.1", "::1", "localhost")
            or user_ip.startswith("192.168.")
            or user_ip.startswith("10.")
            or user_ip.startswith("172.")
        )

        url = "https://ipapi.co/json/" if is_private else f"https://ipapi.co/{user_ip}/json/"
        
        # Look up the client's IP
        response = requests.get(url, timeout=5)
        data = response.json()

        return {
            "ip": data.get("ip", user_ip),
            "isp": data.get("org", "Unknown ISP"),
            "city": data.get("city", "Unknown"),
            "region": data.get("region", ""),
            "country": data.get("country_name", ""),
            "server_location": "Local Dev" if is_private else "Render Cloud (Global)",
            "server_name": "SpeedTest-Backend-v2",
        }
    except Exception as e:
        return {"error": "Could not fetch network info", "details": str(e)}
