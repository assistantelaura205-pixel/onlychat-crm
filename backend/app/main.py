import asyncio

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .auth import (create_token, current_user, hash_password, require_membership,
                   verify_password)
from .database import Base, engine, get_db
from .models import Agency, Membership, User
from .routers import accounts, agencies, conversations, dashboard, vault
from .schemas import (AgencyOut, LoginIn, RegisterIn, TokenOut, UserOut)
from .telegram_manager import manager
from .ws import hub

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OnlyChat CRM API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    hub.loop = asyncio.get_event_loop()


@app.get("/api/health")
def health():
    return {"ok": True, "telegram_ready": manager.ready}


# --- Auth ---
@app.post("/api/auth/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(400, "Email déjà utilisé")
    user = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    agency = Agency(name=body.agency_name)
    db.add(agency)
    db.flush()
    db.add(Membership(user_id=user.id, agency_id=agency.id, role="owner"))
    db.commit()
    return TokenOut(access_token=create_token(user.id))


@app.post("/api/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Identifiants invalides")
    return TokenOut(access_token=create_token(user.id))


@app.get("/api/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


app.include_router(agencies.router)
app.include_router(accounts.router)
app.include_router(conversations.router)
app.include_router(vault.router)
app.include_router(dashboard.router)


@app.websocket("/ws/{agency_id}")
async def websocket_endpoint(ws: WebSocket, agency_id: int):
    await hub.connect(agency_id, ws)
    try:
        while True:
            await ws.receive_text()  # keepalive
    except WebSocketDisconnect:
        hub.disconnect(agency_id, ws)
