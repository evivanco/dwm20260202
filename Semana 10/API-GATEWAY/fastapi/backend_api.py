from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Servicio de catálogo - Libre & Rico",
    description="Productos sin gluten. Enrutado por el API Gateway."
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


@app.get("/productos")
def productos(solo_disponibles: bool = False):
    if solo_disponibles:
        # Los productos por encargo no dependen del stock, se elaboran al pedirlos
        disponibles = [p for p in PRODUCTOS if p["stock"] > 0 or p["tipo"] == "ENCARGO"]
        return {"productos": disponibles}
    return {"productos": PRODUCTOS}


@app.get("/productos/{id_producto}")
def producto(id_producto: int):
    for p in PRODUCTOS:
        if p["id"] == id_producto:
            return p
    raise HTTPException(status_code=404, detail="No existe un producto con ese id.")