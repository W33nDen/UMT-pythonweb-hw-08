from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import Base, engine
from app.routers import contacts, auth, users
from app.routers.users import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Contacts REST API",
    description="REST API for storing and managing contacts with Authentication, JWT, and Cloudinary.",
    version="1.1.0",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure SlowAPI Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(contacts.router)


@app.get("/", tags=["health"])
def health_check() -> dict[str, str]:
    return {"message": "Contacts API is running"}
