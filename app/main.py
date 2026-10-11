from fastapi import FastAPI
from mangum import Mangum
from app.api import health, water, air, waste

app = FastAPI(title="EcoPulse API", version="0.1.0")

app.include_router(health.router)
app.include_router(water.router)
app.include_router(air.router)
app.include_router(waste.router)

handler = Mangum(app)
