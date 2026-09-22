from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="Servicio de pedidos - Libre & Rico",
    description="Pedidos de clientes. Enrutado por el API Gateway."
)


class Linea(BaseModel):
    id_producto: int
    cantidad: int = Field(gt=0)


class PedidoIn(BaseModel):
    cliente: str
    lineas: List[Linea]


PEDIDOS = [
    {"id": 1001, "cliente": "cliente@correo.cl", "estado": "PAGADO"},
    {"id": 1002, "cliente": "cliente@correo.cl", "estado": "PENDIENTE_PAGO"},
]


@app.get("/health")
def health():
    return {"status": "ok",
             "service": "pedidos"
             }


@app.get("/pedidos")
def pedidos():
    return {"pedidos": PEDIDOS}


@app.post("/pedidos", status_code=201)
def crear_pedido(pedido: PedidoIn):
    nuevo = {
        "id": 1000 + len(PEDIDOS) + 1,
        "cliente": pedido.cliente,
        "estado": "PENDIENTE_PAGO",
        "lineas": [linea.model_dump() for linea in pedido.lineas],
    }
    PEDIDOS.append(nuevo)
    return nuevo