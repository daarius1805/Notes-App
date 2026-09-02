from typing import Generator

import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.database import engine
from app.models.user import User
from app.config import settings

security = HTTPBearer()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    try:
        if not settings.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is not configured")

        jwks_client = jwt.PyJWKClient(f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json")
        signing_key = jwks_client.get_signing_key_from_jwt(credentials.credentials)
        
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id or not email:
            raise ValueError("Token is missing the Supabase user identity")
    except (ValueError, jwt.InvalidTokenError, jwt.PyJWKClientError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid credentials: {str(exc)}") from exc

    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        user = User(id=user_id, email=email)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user
