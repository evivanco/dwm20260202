import os
import secrets

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8100")

app = FastAPI(
    title="API Gateway seguro - Libre & Rico",
    description="Valida el token del cliente contra Vault y enruta hacia los servicios"
)

security = HTTPBearer(auto_error=False)

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
CATALOGO_URL = os.getenv("CATALOGO_URL", "http://localhost:9000")
PEDIDOS_URL = os.getenv("PEDIDOS_URL", "http://localhost:9001")

if not VAULT_TOKEN:
    raise RuntimeError("VAULT_TOKEN no esta configurado en las variables de entorno")


# ---- Vault ----

async def obtener_secretos():
    """Pide a Vault los dos secretos del laboratorio."""
    url = f"{VAULT_ADDR}/v1/secret/data/gateway2"
    headers = {"X-Vault-Token": VAULT_TOKEN}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="No fue posible acceder a Vault.")

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="No fue posible acceder a Vault.")

    return response.json()["data"]["data"]


async def autenticar_cliente(
    credenciales: HTTPAuthorizationCredentials = Depends(security)
):
    """El gateway ya no valida el token: le pregunta al servicio de autenticacion."""
    if credenciales is None:
        raise HTTPException(status_code=401, detail="Bearer token requerido.")

    secretos = await obtener_secretos()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/introspect",
                json={"token": credenciales.credentials},
                headers={"X-Gateway-Auth-Secret": secretos["auth_introspection_secret"]},
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Servicio de autenticacion no disponible.")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Error consultando el servicio de autenticacion.")

    identidad = response.json()

    if not identidad.get("active", False):
        raise HTTPException(status_code=401, detail="Token invalido o expirado.")

    return {
        "user_id": identidad["user_id"],
        "username": identidad["username"],
        "roles": identidad["roles"],
        "backend_secret": secretos["backend_shared_secret"],
    }


# ---- Reenvío ----

async def reenviar(metodo, url, auth, params=None, json=None):
    """Agrega la credencial interna que el backend exige y traduce las fallas."""
    headers = {
        "X-Gateway-Secret": auth["backend_secret"],
        "X-Authenticated-User": auth["username"],
        "X-Authenticated-Roles": ",".join(auth["roles"]),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                metodo, url, params=params, json=json, headers=headers
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="El servicio no esta disponible.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="El servicio tardo demasiado.")

    if response.status_code >= 400:
        try:
            detalle = response.json().get("detail", "Error en el servicio.")
        except ValueError:
            detalle = "Error en el servicio."
        raise HTTPException(status_code=response.status_code, detail=detalle)

    return response.json()


# ---- Estado ----

@app.get("/health")
async def health():
    estado = {}
    for nombre, url in (("catalogo", CATALOGO_URL), ("pedidos", PEDIDOS_URL)):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{url}/health")
            estado[nombre] = "ok" if r.status_code == 200 else "con problemas"
        except httpx.HTTPError:
            estado[nombre] = "caido"
    return {"gateway": "ok", "servicios": estado}


# ---- Catalogo ----

@app.get("/api/productos")
async def productos(solo_disponibles: bool = False, auth=Depends(autenticar_cliente)):
    return await reenviar(
        "GET", f"{CATALOGO_URL}/productos", auth,
        params={"solo_disponibles": solo_disponibles}
    )


@app.get("/api/productos/{id_producto}")
async def producto(id_producto: int, auth=Depends(autenticar_cliente)):
    return await reenviar("GET", f"{CATALOGO_URL}/productos/{id_producto}", auth)


# ---- Pedidos ----

@app.get("/api/pedidos")
async def pedidos(auth=Depends(autenticar_cliente)):
    return await reenviar("GET", f"{PEDIDOS_URL}/pedidos", auth)


@app.post("/api/pedidos", status_code=201)
async def crear_pedido(request: Request, auth=Depends(autenticar_cliente)):
    datos = await request.json()

    lineas = datos.get("lineas")
    if not lineas:
        raise HTTPException(status_code=400, detail="El pedido no tiene productos.")

    # El gateway consulta el catalogo antes de enviar el pedido:
    # si falta stock, el pedido nunca llega al servicio de pedidos.
    for linea in lineas:
        respuesta = await reenviar(
            "GET", f"{CATALOGO_URL}/productos/{linea.get('id_producto')}", auth
        )
        producto = respuesta["producto"]

        if producto["tipo"] == "STOCK" and producto["stock"] < linea.get("cantidad", 0):
            raise HTTPException(
                status_code=409,
                detail=f"Solo quedan {producto['stock']} unidades de {producto['nombre']}."
            )

##adapte el ejemplo a mi caso correspondiente que es libre & rico, cambie los servicios de los puertos 
# el puerto 9000(fastapi) es el catalogo de los productos y el 9001(fastapi2) es el servicio de pedidos
# , el cual se encarga de recibir los pedidos de los clientes y enviarlos al servicio de catalogo para verificar si hay stock disponible.
#agregue tambien con la ayuda de la ia , hacer que decida si la peticion pasa o si responde con algun error
#contiene control de acceso:sin token(401), perfil no permitido(403),los pedidos los crean los clientes y los ven los administradores
#servicio muerto: si cualquier servicio no responde , se imprime el 503 con un mensaje del error. y 504 si se demora mucho
#el modo mantencion es el indicardor que hace que el gateway le responda con un 503 sin llamar a ningun servicio
#los tokens los escribi pero segun lo que vimos hoy deberia colocarlos en el administrados de secretos 
