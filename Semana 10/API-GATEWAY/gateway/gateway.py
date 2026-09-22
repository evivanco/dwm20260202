import httpx
from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI(title="API Gateway - Libre & Rico")

CATALOGO_URL = "http://localhost:9000"
PEDIDOS_URL = "http://localhost:9001"

# Tokens de prueba.
TOKENS = {
    "token-cliente": "CLIENTE",
    "token-admin": "ADMINISTRADOR",
}

# Si está en True, el gateway responde sin llamar a ningún servicio
MODO_MANTENCION = False

def verificar_perfil(x_token, permitidos):
    """Decisión 1: sin sesión válida o sin permiso, la petición no pasa."""
    if not x_token:
        raise HTTPException(status_code=401, detail="Debes iniciar sesión.")
    perfil = TOKENS.get(x_token)
    if perfil is None:
        raise HTTPException(status_code=401, detail="La sesión no es válida.")
    if perfil not in permitidos:
        raise HTTPException(status_code=403, detail="Tu perfil no tiene permiso.")
    return perfil


async def reenviar(metodo, url, params=None, json=None):
    """Reenvía la petición al servicio y traduce sus fallas a mensajes claros."""
    if MODO_MANTENCION:
        raise HTTPException(status_code=503, detail="Sitio en mantención. Vuelve en unos minutos.")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.request(metodo, url, params=params, json=json)
    except httpx.ConnectError:
        # servicio caído
        raise HTTPException(status_code=503, detail="El servicio no está disponible en este momento.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="El servicio tardó demasiado en responder.")

    if response.status_code >= 400:
        try:
            detalle = response.json().get("detail", "Error en el servicio.")
        except ValueError:
            detalle = "Error en el servicio."
        raise HTTPException(status_code=response.status_code, detail=detalle)

    return response.json()


@app.get("/api/health")
async def health():
    """Consulta el servicio y resume su estado."""
    estado = {}
    for nombre, url in (("catalogo", CATALOGO_URL), ("pedidos", PEDIDOS_URL)):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{url}/health")
            estado[nombre] = "ok" if r.status_code == 200 else "con problemas"
        except httpx.HTTPError:
            estado[nombre] = "caído"
    return {"gateway": "ok", "servicios": estado}


# ---- Catálogo: público ----

@app.get("/api/productos")
async def productos(solo_disponibles: bool = False):
    return await reenviar("GET", f"{CATALOGO_URL}/productos",
                          params={"solo_disponibles": solo_disponibles})


@app.get("/api/productos/{id_producto}")
async def producto(id_producto: int):
    return await reenviar("GET", f"{CATALOGO_URL}/productos/{id_producto}")


# pedidos-privacidad

@app.get("/api/pedidos")
async def pedidos(x_token: str = Header(default="")):
    # admin capaz de ver todos los pedidos, solo el
    verificar_perfil(x_token, ["ADMINISTRADOR"])
    return await reenviar("GET", f"{PEDIDOS_URL}/pedidos")


@app.post("/api/pedidos", status_code=201)
async def crear_pedido(request: Request, x_token: str = Header(default="")):
    verificar_perfil(x_token, ["CLIENTE"])
    datos = await request.json()

    lineas = datos.get("lineas")
    if not lineas:
        raise HTTPException(status_code=400, detail="El pedido no tiene productos.")

    # el gateway consulta a el catálogo antes de enviar el pedido.
    # Si falta stock, el pedido nunca va a allegar a la cola de pedidos.
    for linea in lineas:
        producto = await reenviar("GET", f"{CATALOGO_URL}/productos/{linea.get('id_producto')}")
        if producto["tipo"] == "STOCK" and producto["stock"] < linea.get("cantidad", 0):
            raise HTTPException(
                status_code=409,
                detail=f"Solo quedan {producto['stock']} unidades de {producto['nombre']}."
            )

    return await reenviar("POST", f"{PEDIDOS_URL}/pedidos", json=datos)

##adapte el ejemplo a mi caso correspondiente que es libre & rico, cambie los servicios de los puertos 
# el puerto 9000(fastapi) es el catalogo de los productos y el 9001(fastapi2) es el servicio de pedidos
# , el cual se encarga de recibir los pedidos de los clientes y enviarlos al servicio de catalogo para verificar si hay stock disponible.
#agregue tambien con la ayuda de la ia , hacer que decida si la peticion pasa o si responde con algun error
#contiene control de acceso:sin token(401), perfil no permitido(403),los pedidos los crean los clientes y los ven los administradores
#servicio muerto: si cualquier servicio no responde , se imprime el 503 con un mensaje del error. y 504 si se demora mucho
#el modo mantencion es el indicardor que hace que el gateway le responda con un 503 sin llamar a ningun servicio
#los tokens los escribi pero segun lo que vimos hoy deberia colocarlos en el administrados de secretos 
