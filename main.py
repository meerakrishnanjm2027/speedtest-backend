from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Allow React frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your React URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. PING: Measure latency
@app.get("/ping")
async def ping():
    return {"status": "ok"}

# 2. DOWNLOAD: Stream random bytes to the client
@app.get("/download")
async def download(size: int = 25000000): # Default 25MB
    def generate_bytes():
        chunk_size = 65536 # 64KB chunks
        sent = 0
        while sent < size:
            yield os.urandom(min(chunk_size, size - sent))
            sent += chunk_size
            
    return StreamingResponse(generate_bytes(), media_type="application/octet-stream")

# 3. UPLOAD: Accept a file and measure its size
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    return {"received_bytes": len(content)}
// Add these state variables at the top of your App component
const [networkInfo, setNetworkInfo] = useState(null);
const [isFetchingInfo, setIsFetchingInfo] = useState(false);

// Add this function to fetch network details
const fetchNetworkInfo = async () => {
  setIsFetchingInfo(true);
  try {
    const res = await fetch(`${API_URL}/network-info`);
    const data = await res.json();
    setNetworkInfo(data);
  } catch (error) {
    console.error("Failed to fetch network info:", error);
  } finally {
    setIsFetchingInfo(false);
  }
};

// Call this when the page loads OR right before starting the test
useEffect(() => {
  fetchNetworkInfo();
}, []);

// Update your UI to display the info (Add this above your "Start Test" button)
<div style={{ marginBottom: '20px', fontSize: '14px', color: '#aaa' }}>
  {networkInfo ? (
    <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', flexWrap: 'wrap' }}>
      <span>🌍 <strong>Server:</strong> {networkInfo.server_location}</span>
      <span>📡 <strong>ISP:</strong> {networkInfo.isp}</span>
      <span>🔗 <strong>IP:</strong> {networkInfo.ip}</span>
      <span>📍 <strong>Location:</strong> {networkInfo.city}, {networkInfo.country}</span>
    </div>
  ) : (
    <span>{isFetchingInfo ? "Detecting network..." : "Network info unavailable"}</span>
  )}
</div>
