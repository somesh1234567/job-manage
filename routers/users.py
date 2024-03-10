from typing import Annotated, Optional
from fastapi import HTTPException, UploadFile, File, APIRouter, Depends, Request, Response, Form
from pydantic import BaseModel
from database import SessionLocal
import models
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import timedelta, datetime
from starlette import status

router = APIRouter()

SECRET_KEY = 'da06e3b904d7357d55b6fc97f72dbab8fc37b5b2ee4eda7a0ea001f6703394dd'
ALGORITHM = 'HS256'

templates = Jinja2Templates(directory="templates")

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")

class LoginResponse(BaseModel):
  access_token: str
  role: Optional[str] = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password):
    return bcrypt_context.hash(password)

def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str, db):
    student = db.query(models.Users).filter(models.Users.username == username).first()
    if student and verify_password(password, student.hashed_password):
        return student
    employee = db.query(models.Employee).filter(models.Employee.username == username).first()
    if employee and verify_password(password, employee.hashed_password):
        return employee
    return False

# function to create a JWT token for the user
def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# function to decode a JWT token and return the current user
# async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get('sub')
#         user_id: int = payload.get('id')
#         user_role: str = payload.get('role')
#         if username is None or user_id is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
#         return {'username': username, 'id': user_id, 'role': user_role}
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            # raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
            await logout(request)
        return {'username': username, 'id': user_id, 'role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

# endpoint to create a token after user is authenticated
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return False
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=60))
    return user.role, token

@router.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        # response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

        user_role, token = await login_for_access_token(form_data=form, db=db)

        if user_role == 'student':
            # response = JSONResponse(content={'access_token': token, 'role': user_role})
            # response.set_cookie(key="access_token", value=token, httponly=True)
            response = RedirectResponse(url="/jobs", status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="access_token", value=token, httponly=True)
            return response
        elif user_role == 'employee':
            response = RedirectResponse(url="/jobs/job-details", status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="access_token", value=token, httponly=True)
            return response
        else:
            msg = "Invalid Credentials"
            return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    
@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    msg = "Logout Successful"
    response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    response.delete_cookie(key="access_token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("user.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, username: str = Form(...), firstname: str = Form(...), lastname: str = Form(...),
                        phoneno: str = Form(None, description="Required for student only"), email: str = Form(...), password: str = Form(...),
                        password2: str = Form(...), file: UploadFile = File(...), role: str = Form(...), db: Session = Depends(get_db)):
    validation1 = db.query(models.Users).filter(models.Users.username == username).first()

    validation2 = db.query(models.Users).filter(models.Users.email == email).first()

    if password != password2 or validation1 is not None or validation2 is not None:
        msg = "Username or Email already exists"
        return templates.TemplateResponse("user.html", {"request": request, "msg": msg})
    
    if role == "employee":
        user_model = models.Employee()
        user_model.username = username
        user_model.first_name = firstname
        user_model.last_name = lastname
        user_model.email = email
        user_model.role = role
        user_model.normal_password = password

        hash_password = get_password_hash(password)
        user_model.hashed_password = hash_password
        user_model.is_active = True

        db.add(user_model)
        db.commit()

        msg = "User Registered Successfully"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    else:
        user_model = models.Users()
        user_model.username = username
        user_model.first_name = firstname
        user_model.last_name = lastname
        user_model.phone_number = phoneno
        user_model.email = email
        user_model.resume = file.file.read()
        user_model.role = role
        user_model.normal_password = password

        hash_password = get_password_hash(password)
        user_model.hashed_password = hash_password
        user_model.is_active = True

        db.add(user_model)
        db.commit()

        msg = "User Registered Successfully"
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
