import os
import secrets

from fastapi import (
    FastAPI,
    HTTPException,
    Header,
    Depends
)

app = FastAPI(
    title="Protected Backend API - Servicio de catálogo - Libre & Rico",
    description="Productos sin gluten. Enrutado por el API Gateway."
)

INTERNAL_GATEWAY_SECRET = os.getenv(
    "INTERNAL_GATEWAY_SECRET",
)

if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError(
        "INTERNAL_GATEWAY_SECRET no está definido en las variables de entorno."
    )

def verify_gateway(
        x_gateway_secret:str = Header(default="")
):
    valid = secrets.compare_digest(
        x_gateway_secret,
        INTERNAL_GATEWAY_SECRET
    )

    if not valid:
        raise HTTPException(
            status_code=403,
            detail="solicitud no autorizada desde el gateway"
        )

PRODUCTOS = [
    {"id": 1, "nombre": "Marraqueta sin gluten", "precio": 2500, "stock": 20, "tipo": "STOCK"},
    {"id": 2, "nombre": "Pan de molde integral", "precio": 4200, "stock": 8, "tipo": "STOCK"},
    {"id": 3, "nombre": "Brownie sin gluten", "precio": 1800, "stock": 0, "tipo": "STOCK"},
    {"id": 4, "nombre": "Torta de chocolate", "precio": 18000, "stock": 0, "tipo": "ENCARGO"},
]


@app.get("/health")
def health():
    return {"status": "ok", 
            "service": "catalogo"
            }


@app.get(
        "/productos",
        dependencies=[Depends(verify_gateway)]
)
def productos(    
    solo_disponibles: bool = False,
    x_authenticated_client: str = Header(default="None")
):
    if solo_disponibles:
        # Los productos por encargo no dependen del stock, se elaboran al pedirlos
        disponibles = [p for p in PRODUCTOS if p["stock"] > 0 or p["tipo"] == "ENCARGO"]
        return {
            "x_authenticated_client": x_authenticated_client,
            "productos": disponibles
        }
    return {
        "x_authenticated_client": x_authenticated_client,
        "productos": PRODUCTOS
    }


@app.get(
    "/productos/{id_producto}",
    dependencies=[Depends(verify_gateway)]
)
def producto(
    id_producto: int,
    x_authenticated_client: str | None = Header(default=None)
):
    for p in PRODUCTOS:
        if p["id"] == id_producto:
            return {
                "authenticated_client": x_authenticated_client,
                "producto": p
            }
    raise HTTPException(status_code=404, detail="No existe un producto con ese id.")


