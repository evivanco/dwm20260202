from fastapi import FastAPI

app = FastAPI(title="Backend 1", description="API enrutada por API Gateway")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/products")
def get_products():
    return [{"id": 1, "nombre": "Producto A", "precio": 100}]

@app.get("/orders")
def get_orders():
    return [{"id_pedido": 101, "estado": "pendiente"}]