from fastapi import FastAPI
from .router import router
from .database import engine, Base

# FastAPI Application entry point.
app = FastAPI(title="Medical System - Patient Registration")

# Root endpoint for basic health check.
@app.get("/")
async def root():
    return {"status": "ok", "message": "Medical System API is running"}

# Include the patients router. Why? To keep routes organized.
app.include_router(router)

# Startup event to create database tables.
# Why? Ensures the application is ready to use immediately in a demo environment.
# Note: In a real production environment, use Alembic for migrations.
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
