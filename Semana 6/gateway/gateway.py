from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI(title="API Gateway", description="Enrutador central")

backend_url = "http://localhost:9000"
backend_url2 = "http://localhost:9100"

@app.get("/api/products")
async def gateway_products():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{backend_url}/products")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Backend 1 no disponible")

@app.get("/api/productos")
async def gateway_productos():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{backend_url2}/productos")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Backend 2 no disponible")