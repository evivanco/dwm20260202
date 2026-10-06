from datetime import datetime, timedelta, timezone
import os
import secrets

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Servicio de autenticacion - Libre & Rico",
    description="Emite y valida los tokens de los usuarios"
)

USUARIOS = {
    "ana": {"password": "1234", "user_id": "USR-001", "roles": ["cliente"]},
    "pedro": {"password": "5678", "user_id": "USR-002", "roles": ["cliente"]},
    "admin": {"password": "admin123", "user_id": "USR-003", "roles": ["cliente", "admin"]},
}

SESIONES = {}

MINUTOS_DE_VIDA = 15

AUTH_INTROSPECTION_SECRET = os.getenv(
    "AUTH_INTROSPECTION_SECRET",
    "demo-introspection-secret"
)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenRequest(BaseModel):
    token: str


def verificar_gateway(x_gateway_auth_secret: str = Header(default="")):
    if not secrets.compare_digest(x_gateway_auth_secret, AUTH_INTROSPECTION_SECRET):
        raise HTTPException(status_code=403, detail="Gateway no autorizado")


@app.get("/health")
def health():
    return {"status": "OK", "service": "auth"}


@app.post("/login")
def login(request: LoginRequest):
    usuario = USUARIOS.get(request.username)

    if usuario is None or usuario["password"] != request.password:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    access_token = secrets.token_urlsafe(32)
    expira = datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_DE_VIDA)

    SESIONES[access_token] = {
        "user_id": usuario["user_id"],
        "username": request.username,
        "roles": usuario["roles"],
        "expires_at": expira,
    }

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": MINUTOS_DE_VIDA * 60,
    }


@app.post("/introspect")
def introspect(request: TokenRequest, x_gateway_auth_secret: str = Header(default="")):
    verificar_gateway(x_gateway_auth_secret)

    sesion = SESIONES.get(request.token)
    if sesion is None:
        return {"active": False}

    if datetime.now(timezone.utc) > sesion["expires_at"]:
        SESIONES.pop(request.token, None)
        return {"active": False}

    return {
        "active": True,
        "user_id": sesion["user_id"],
        "username": sesion["username"],
        "roles": sesion["roles"],
        "expires_at": sesion["expires_at"].isoformat(),
    }


@app.post("/logout")
def logout(request: TokenRequest, x_gateway_auth_secret: str = Header(default="")):
    verificar_gateway(x_gateway_auth_secret)
    SESIONES.pop(request.token, None)
    return {"message": "Sesion finalizada"}