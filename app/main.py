import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import health, water, air, waste

app = FastAPI(title="EcoPulse API", version="0.1.0")

app.include_router(health.router)
app.include_router(water.router)
app.include_router(air.router)
app.include_router(waste.router)

# Serve the EcoPulse multi-themed frontend
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# AWS Lambda Handler (Mangum adapter)
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    handler = None
