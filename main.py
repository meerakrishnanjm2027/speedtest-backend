from fastapi import Request

@app.get("/network-info")
async def get_network_info(request: Request):
    try:
        # Get user IP from headers (behind a proxy) or fallback to socket
        forwarded = request.headers.get("x-forwarded-for")
        user_ip = forwarded.split(",")[0].strip() if forwarded else request.client.host

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
