import os
import secrets
import httpx
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(title="API Gateway Seguro con Introspección")
security = HTTPBearer(auto_error=False)

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

if not VAULT_TOKEN:
    raise RuntimeError("VAULT_TOKEN no está configurado")

async def get_gateway_secrets():
    url = f"{VAULT_ADDR}/v1/secret/data/gateway"
    headers = {"X-Vault-Token": VAULT_TOKEN}
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="No fue posible acceder a Vault")
        return response.json()["data"]["data"]

async def authenticate_client(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    vault_secrets = await get_gateway_secrets()
    backend_secret = vault_secrets.get("backend_share_secret")
    introspection_secret = vault_secrets.get("introspection_secret")
    
    # Consultar al AuthService si el token es válido (Introspección)
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.post(
                "http://127.0.0.1:8100/introspect",
                json={"token": credentials.credentials},
                headers={"X-Gateway-Secret": introspection_secret}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=503, detail="AuthService no disponible")
            
            data = response.json()
            if not data.get("active"):
                raise HTTPException(status_code=401, detail="token inválido o expirado")
                
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Error de conexión con AuthService")

    return {
        "username": data["username"],
        "roles": ",".join(data["roles"]),
        "backend_secret": backend_secret
    }

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str, request: Request, auth: dict = Depends(authenticate_client)):
    target_url = f"http://localhost:9000/{path}"
    body = await request.body()
    
    gateway_headers = {
        "X-Gateway-Secret": auth["backend_secret"],
        "X-Authenticated-User": auth["username"],
        "X-Authenticated-Roles": auth["roles"],
        "Content-Type": request.headers.get("content-type", "application/json")
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            upstream = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                content=body,
                headers=gateway_headers
            )
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Backend no disponible")

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=dict(upstream.headers)
    )