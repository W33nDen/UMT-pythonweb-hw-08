from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import contacts


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Contacts REST API",
    description="REST API for storing and managing contacts.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(contacts.router)


@app.get("/", tags=["health"])
def health_check() -> dict[str, str]:
    return {"message": "Contacts API is running"}

