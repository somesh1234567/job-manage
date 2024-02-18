from fastapi import UploadFile, File, APIRouter, Depends, Request, Response, Form
from database import SessionLocal
import models
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext

router = APIRouter()

templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_password_hash(password):
    return bcrypt_context.hash(password)

def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("user.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, username: str = Form(...), firstname: str = Form(...), lastname: str = Form(...),
                        phoneno: str = Form(...), email: str = Form(...), password: str = Form(...),
                        password2: str = Form(...), file: UploadFile = File(...), role: str = Form(...), db: Session = Depends(get_db)):
    validation1 = db.query(models.Users).filter(models.Users.username == username).first()

    validation2 = db.query(models.Users).filter(models.Users.email == email).first()

    if password != password2 or validation1 is not None or validation2 is not None:
        msg = "Username or Email already exists"
        return templates.TemplateResponse("user.html", {"request": request, "msg": msg})
    
    user_model = models.Users()
    user_model.username = username
    user_model.first_name = firstname
    user_model.last_name = lastname
    user_model.phone_number = phoneno
    user_model.email = email
    user_model.resume = file.file.read()
    user_model.role = role

    hash_password = get_password_hash(password)
    user_model.hashed_password = hash_password
    user_model.is_active = True

    db.add(user_model)
    db.commit()

    msg = "User Registered Successfully"
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
