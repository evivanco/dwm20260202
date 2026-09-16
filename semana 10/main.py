from typing import List, Optional, Dict
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from contextlib import asynccontextmanager

# configuracion de bd mongodb
MONGODB_URI = "mongodb://localhost:27017"
DB_NAME = "bdunab2"
COLL_NAME = "items"

client: AsyncIOMotorClient | None = None
db = None
coll = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db, coll
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    coll = db[COLL_NAME]
    yield
    client.close()


app = FastAPI(title="fastapi libre y rico", version="1.0.0", lifespan=lifespan)


class Item(BaseModel):
    nombre: str = Field(min_length=1, description="Nombre del item")
    # CLP no usa decimales xlo tanto int
    precio: int = Field(gt=0, description="Precio en pesos chilenos")
    stock: int = Field(default=0, ge=0, description="Unidades disponibles (RF-07)")
    tags: List[str] = Field(default_factory=list)
    activo: bool = True


class ItemOut(Item):
    id: str
    disponible: bool = Field(default=False, description="Activo y con stock > 0")


class OperacionStock(str, Enum):
    INGRESAR = "ingresar"      # ->produccion del dia
    DESCONTAR = "descontar"    # ->venta o merma
    ESTABLECER = "establecer"  # ->correccion de inventario


class AjusteStock(BaseModel):
    operacion: OperacionStock
    cantidad: int = Field(ge=0)
    motivo: str = Field(default="", max_length=200)


def doc_to_item(doc: Dict) -> ItemOut:
    stock = doc.get("stock", 0)
    activo = doc.get("activo", True)
    return ItemOut(
        id=str(doc["_id"]),
        nombre=doc["nombre"],
        precio=doc["precio"],
        stock=stock,
        tags=doc.get("tags", []),
        activo=activo,
        disponible=activo and stock > 0,  #  tngo k recordar cambiar el supuesto S-06
    )


def validar_id(item_id: str) -> ObjectId:
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    return ObjectId(item_id)


# EndPoint
@app.get("/health", tags=["sistema"])
def health():
    return {"status": "ok"}


@app.get("/items", response_model=List[ItemOut], tags=["items"])
async def listar_items(
    q: Optional[str] = Query(None, description="filtro por el nombre que contenga q"),
    solo_disponibles: bool = Query(False, description="oculta lo agotado (RF-07)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = {}
    if q:
        query["nombre"] = {"$regex": q, "$options": "i"}
    if solo_disponibles:
        query["activo"] = True
        query["stock"] = {"$gt": 0}
    cursor = coll.find(query).skip(skip).limit(limit)
    items: List[ItemOut] = []
    async for doc in cursor:
        items.append(doc_to_item(doc))
    return items


@app.post("/items", response_model=ItemOut, status_code=201, tags=["items"])
async def crear_item(item: Item):
    res = await coll.insert_one(item.model_dump())
    doc = await coll.find_one({"_id": res.inserted_id})
    return doc_to_item(doc)


# cambio-  alerta de reposicion para el mantenedor (RF-07)
@app.get("/items/sin-stock", response_model=List[ItemOut], tags=["stock"])
async def items_sin_stock():
    cursor = coll.find({"activo": True, "stock": {"$lte": 0}})
    return [doc_to_item(doc) async for doc in cursor]


@app.get("/items/{item_id}", response_model=ItemOut, tags=["items"])
async def obtener_item(item_id: str):
    doc = await coll.find_one({"_id": validar_id(item_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return doc_to_item(doc)


@app.put("/items/{item_id}", response_model=ItemOut, tags=["items"])
async def actualizar_item(item_id: str, item: Item):
    oid = validar_id(item_id)
    res = await coll.update_one({"_id": oid}, {"$set": item.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    doc = await coll.find_one({"_id": oid})
    return doc_to_item(doc)


# cambio- actualizar la disponibilidad sin reenviar el item completo (RF-07)
@app.patch("/items/{item_id}/stock", response_model=ItemOut, tags=["stock"])
async def ajustar_stock(item_id: str, ajuste: AjusteStock):
    oid = validar_id(item_id)
    doc = await coll.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    actual = doc.get("stock", 0)
    if ajuste.operacion == OperacionStock.INGRESAR:
        nuevo = actual + ajuste.cantidad
    elif ajuste.operacion == OperacionStock.ESTABLECER:
        nuevo = ajuste.cantidad
    else:
        nuevo = actual - ajuste.cantidad
        if nuevo < 0:
            # el stock jamas puede ser negativo
            raise HTTPException(
                status_code=409,
                detail=f"Solo hay {actual} unidades de '{doc['nombre']}'",
            )

    await coll.update_one(
        {"_id": oid},
        {
            "$set": {"stock": nuevo, "stock_actualizado": datetime.now(timezone.utc)},
            "$push": {
                "movimientos_stock": {
                    "fecha": datetime.now(timezone.utc),
                    "operacion": ajuste.operacion.value,
                    "cantidad": ajuste.cantidad,
                    "stock_anterior": actual,
                    "stock_nuevo": nuevo,
                    "motivo": ajuste.motivo,
                }
            },
        },
    )
    return doc_to_item(await coll.find_one({"_id": oid}))


# cambio- : baja logica en vez de borrado fisico (RF-10)
# Borrar el documento rompe los pedidos y boletas que lo referencian.
@app.delete("/items/{item_id}", response_model=ItemOut, tags=["items"])
async def desactivar_item(item_id: str):
    oid = validar_id(item_id)
    res = await coll.update_one({"_id": oid}, {"$set": {"activo": False}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return doc_to_item(await coll.find_one({"_id": oid}))