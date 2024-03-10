from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import models
from database import engine
from database import SessionLocal
from routers import users, jobs
from starlette.staticfiles import StaticFiles

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(users.router)
app.include_router(jobs.router)