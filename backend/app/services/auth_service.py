from sqlmodel import Session, select

from app.auth.jwt_handler import create_access_token
from app.auth.password_handler import hash_password, verify_password
from app.models.user import User
from app.schemas.auth_schema import UserCreate, UserLogin


def register_user(session: Session, payload: UserCreate) -> User:
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise ValueError("User already exists")

    user = User(email=str(payload.email), password_hash=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login_user(session: Session, payload: UserLogin) -> str:
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise ValueError("Invalid email or password")
    return create_access_token(user.id)
