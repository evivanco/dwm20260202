import secrets
import os
from fastapi import FastAPI, Header, HTTPException, Depends

app = FastAPI(title="Backend Privado Protegido")

INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")
if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("INTERNAL_GATEWAY_SECRET no está configurado")

async def verify_gateway(x_gateway_secret: str = Header(None)):
    if not x_gateway_secret:
        raise HTTPException(status_code=403, detail="Solicitud no autorizada desde Gateway")
    
    valid = secrets.compare_digest(x_gateway_secret, INTERNAL_GATEWAY_SECRET)
    if not valid:
        raise HTTPException(status_code=403, detail="Solicitud no autorizada desde Gateway")

@app.get("/products", dependencies=[Depends(verify_gateway)])
async def get_products(x_authenticated_client: str = Header("default")):
    return {
        "authenticated_client": x_authenticated_client,
        "products": [
            {"id": 1, "name": "notebook", "price": 900},
            {"id": 2, "name": "monitor", "price": 250}
        ]
    }