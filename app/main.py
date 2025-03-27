from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.database import init_db
from app.routes import auth_router, profile_router, roadmap_router
from app.database import Base, engine, init_db
from app.settings import settings


init_db()

app = FastAPI(debug=settings.DEBUG)
app = FastAPI(debug=True)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    session_cookie="session_id",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.PREFIX)
app.include_router(profile_router, prefix=settings.PREFIX)
app.include_router(roadmap_router, prefix=settings.PREFIX)
