from fastapi import FastAPI

app = FastAPI(title="Backend 2", description="Segundo sistema independiente")

@app.get("/productos")
def get_productos():
    return [{"nombre": "Laptop", "precio": 850000}]