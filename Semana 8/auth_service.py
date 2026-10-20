import secrets
import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

app = FastAPI(title="Auth Service")
TOKEN_LIFETIME_MINUTES = 15
OUT_INTROSPECTION_SECRET = os.getenv("OUT_INTROSPECTION_SECRET")

if not OUT_INTROSPECTION_SECRET:
    raise RuntimeError("OUT_INTROSPECTION_SECRET no está configurado")

# Base de datos simulada
USERS = {
    "Ana": {"password": "123", "user_id": 1, "roles": ["user"]},
    "Pedro": {"password": "123", "user_id": 2, "roles": ["user"]},
    "Ernesto": {"password": "123", "user_id": 3, "roles": ["user", "admin"]}
}
sessions = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class IntrospectionRequest(BaseModel):
    token: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "Authentication Service"}

@app.post("/login")
def login(req: LoginRequest):
    user = USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="credenciales incorrectas")
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_LIFETIME_MINUTES)
    
    sessions[token] = {
        "user_id": user["user_id"],
        "username": req.username,
        "roles": user["roles"],
        "expires_at": expires_at
    }
    return {"access_token": token, "token_type": "bearer", "expires_in": TOKEN_LIFETIME_MINUTES * 60}

@app.post("/introspect")
def introspect(req: IntrospectionRequest, x_gateway_secret: str = Header(None)):
    if not x_gateway_secret or not secrets.compare_digest(x_gateway_secret, OUT_INTROSPECTION_SECRET):
        raise HTTPException(status_code=403, detail="gateway no autorizado")
    
    session = sessions.get(req.token)
    if not session:
        return {"active": False}
    
    if datetime.now(timezone.utc) > session["expires_at"]:
        sessions.pop(req.token, None)
        return {"active": False}
        
    return {
        "active": True,
        "user_id": session["user_id"],
        "username": session["username"],
        "roles": session["roles"],
        "expires_at": session["expires_at"].isoformat()
    }

@app.post("/logout")
def logout(req: IntrospectionRequest, x_gateway_secret: str = Header(None)):
    if not x_gateway_secret or not secrets.compare_digest(x_gateway_secret, OUT_INTROSPECTION_SECRET):
        raise HTTPException(status_code=403, detail="gateway no autorizado")
    sessions.pop(req.token, None)
    return {"message": "sesión finalizada"}