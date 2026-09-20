from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI(
    title="Fitness API Gateway",
    description="Orquestador central del sistema de gimnasio"
)

# URLs de los servicios de backend
USERS_SERVICE_URL = "http://localhost:9000"
WORKOUTS_SERVICE_URL = "http://localhost:9001"

@app.get("/health")
def gateway_health():
    return {"status": "OK", "service": "Fitness API Gateway"}

# --- Enrutamiento hacia Servicio 1: Usuarios (Puerto 9000) ---
@app.get("/api/v1/members")
async def proxy_members():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{USERS_SERVICE_URL}/members")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de Usuarios no disponible")

@app.get("/api/v1/members/summary")
async def proxy_summary():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{USERS_SERVICE_URL}/members/summary")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de Usuarios no disponible")

# --- Enrutamiento hacia Servicio 2: Entrenamientos (Puerto 9001) ---
@app.get("/api/v1/workouts")
async def proxy_workouts():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{WORKOUTS_SERVICE_URL}/workouts")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de Entrenamientos no disponible")

@app.get("/api/v1/exercises")
async def proxy_exercises():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{WORKOUTS_SERVICE_URL}/exercises")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de Entrenamientos no disponible")