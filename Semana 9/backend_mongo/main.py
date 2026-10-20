import contextlib
from fastapi import FastAPI, HTTPException, Response
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId

# Configuración de la base de datos
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "BD1_2"

client = None
db = None
collection = None

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db, collection
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db["items"]
    yield
    client.close()

# ¡ESTA ES LA LÍNEA QUE FALTABA!
app = FastAPI(title="Servicio con Persistencia MongoDB", lifespan=lifespan)

# Modelos Pydantic
class ItemIn(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del producto")
    precio: float = Field(..., gt=0, description="Precio mayor a 0")
    tags: List[str] = Field(default_factory=list)
    activo: bool = True

class ItemOut(ItemIn):
    id: str

def doc_to_item_out(doc: dict) -> ItemOut:
    return ItemOut(
        id=str(doc["_id"]),
        nombre=doc.get("nombre", ""),
        precio=doc.get("precio", 0.0),
        tags=doc.get("tags", []),
        activo=doc.get("activo", True)
    )

# Endpoints CRUD
@app.get("/items", response_model=List[ItemOut])
async def get_items(q: Optional[str] = None, skip: int = 0, limit: int = 50):
    query = {}
    if q:
        query["nombre"] = {"$regex": q, "$options": "i"}
    cursor = collection.find(query).skip(skip).limit(limit)
    items = []
    async for doc in cursor:
        items.append(doc_to_item_out(doc))
    return items

@app.post("/items", response_model=ItemOut, status_code=201)
async def create_item(item: ItemIn):
    res = await collection.insert_one(item.model_dump())
    doc = await collection.find_one({"_id": res.inserted_id})
    return doc_to_item_out(doc)

@app.get("/items/{item_id}", response_model=ItemOut)
async def get_item_by_id(item_id: str):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    doc = await collection.find_one({"_id": ObjectId(item_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    return doc_to_item_out(doc)

@app.put("/items/{item_id}", response_model=ItemOut)
async def update_item(item_id: str, item: ItemIn):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    res = await collection.update_one({"_id": ObjectId(item_id)}, {"$set": item.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    doc = await collection.find_one({"_id": ObjectId(item_id)})
    return doc_to_item_out(doc)

@app.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: str):
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    res = await collection.delete_one({"_id": ObjectId(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    return Response(status_code=204)