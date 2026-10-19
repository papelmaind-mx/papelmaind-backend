from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from src.core.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)

class CurrentUser(BaseModel):
    user_id: UUID
    tenant_id: UUID
    role: str
    rel_id: UUID

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if not credentials:
        raise HTTPException(401, "Token requerido", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(401, "Token inválido o expirado")
    try:
        return CurrentUser(
            user_id=UUID(payload["sub"]),
            tenant_id=UUID(payload["tenant_id"]),
            role=payload["role"],
            rel_id=UUID(payload["rel_id"]),
        )
    except (KeyError, ValueError):
        raise HTTPException(401, "Claims incompletos")
