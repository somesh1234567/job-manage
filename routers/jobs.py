from datetime import date
from typing import Annotated
from fastapi import HTTPException, UploadFile, File, APIRouter, Depends, Request, Response, Form
from database import SessionLocal
import models
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette import status
from starlette.responses import RedirectResponse
from .users import get_current_user

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)

templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/", response_class=HTMLResponse)
async def register(request: Request,db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None or user["role"] != "student":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    all_jobs = db.query(models.Jobs).all()
    return templates.TemplateResponse("jobs.html", {"request": request, "all_jobs": all_jobs, "user": user})

@router.get("/job-details", response_class=HTMLResponse)
async def see_job_details(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None or user["role"] != "employee":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    jobs = db.query(models.Jobs).filter(models.Jobs.owner_id == user['id']).all()
    return templates.TemplateResponse("job-postings.html", {"request": request, "jobs": jobs, "user": user})

@router.get("/create-job", response_class=HTMLResponse)
async def create_job(request: Request):
    user = await get_current_user(request)
    if user is None or user["role"] != "employee":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("create-job.html", {"request": request})


@router.post("/create-job", response_class=HTMLResponse)
async def create_new_job(request: Request, title: str = Form(...), compname: str = Form(...), compurl: str = Form(...),
                         location: str = Form(...), description: str = Form(...), jobdate: date = Form(...) ,db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None or user["role"] != "employee":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    job_model = models.Jobs()
    job_model.title = title
    job_model.company = compname
    job_model.company_url = compurl
    job_model.location = location
    job_model.description = description
    job_model.date_posted = jobdate
    job_model.is_active = True
    job_model.owner_id = user['id']

    db.add(job_model)
    db.commit()
    return RedirectResponse(url="/jobs/job-details", status_code=status.HTTP_302_FOUND)