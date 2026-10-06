from typing import List

from fastapi import FastAPI, Depends, Header, HTTPException
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


def verify_gateway(
    x_authenticated_user: str | None = Header(default=None),
    x_authenticated_roles: str | None = Header(default=None),
):
    if x_authenticated_user is None or x_authenticated_roles is None:
        raise HTTPException(
            status_code=401,
            detail="Missing gateway authentication headers",
        )


@app.get("/health")
def health():
    return {"status": "ok",
             "service": "pedidos"
             }


@app.get("/pedidos", dependencies=[Depends(verify_gateway)])
def pedidos(
    x_authenticated_user: str | None = Header(default=None),
    x_authenticated_roles: str | None = Header(default=None),
):
    return {
        "identity": {
            "username": x_authenticated_user,
            "roles": x_authenticated_roles,
        },
        "pedidos": PEDIDOS,
    }

@app.post("/pedidos", status_code=201, dependencies=[Depends(verify_gateway)])
def crear_pedido(
    pedido: PedidoIn,
    x_authenticated_user: str | None = Header(default=None),
    x_authenticated_roles: str | None = Header(default=None),
):
    nuevo = {
        "id": 1000 + len(PEDIDOS) + 1,
        "cliente": pedido.cliente,
        "estado": "PENDIENTE_PAGO",
        "lineas": [linea.model_dump() for linea in pedido.lineas],
    }
    PEDIDOS.append(nuevo)
    return {
        "identity": {
            "username": x_authenticated_user,
            "roles": x_authenticated_roles,
        },
        "pedido": nuevo,
    }