from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import models
from database import engine
from database import SessionLocal
from routers import users

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(users.router)