import base64
from datetime import date
import logging
from typing import Annotated
from fastapi import HTTPException, UploadFile, File, APIRouter, Depends, Request, Response, Form
from database import SessionLocal
import models
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette import status
from starlette.responses import RedirectResponse
from .users import get_current_user
from logger import logger

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
    applied_job_ids = [job.id for job in db.query(models.Apply).filter(models.Apply.user_id == user['id']).all()]
    remaining_jobs = db.query(models.Jobs).filter(models.Jobs.id.notin_(applied_job_ids)).all()
    return templates.TemplateResponse("jobs.html", {"request": request, "all_jobs": remaining_jobs, "user": user})

@router.get("/apply/{job_id}")
async def apply_for_job(request: Request, job_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None or user["role"] != "student":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    apply_model = models.Apply()
    apply_model.job_id = job_id
    apply_model.user_id = user['id']
    db.add(apply_model)
    db.commit()
    return RedirectResponse(url="/jobs", status_code=status.HTTP_302_FOUND)


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
    return templates.TemplateResponse("create-job.html", {"request": request, "user": user})


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

# edit a posted job
@router.get("/edit-job/{job_id}", response_class=HTMLResponse)
async def edit_job(request: Request, job_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None or user["role"] != "employee":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    job = db.query(models.Jobs).filter(models.Jobs.id == job_id).first()
    return templates.TemplateResponse("edit-job.html", {"request": request, "job": job, "user": user})

@router.post("/edit-job/{job_id}", response_class=HTMLResponse)
async def edit_job_commit(request: Request, job_id: int, title: str = Form(...), description: str = Form(...),db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None or user["role"] != "employee":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    job_model = db.query(models.Jobs).filter(models.Jobs.id == job_id).first()
    job_model.title = title
    job_model.description = description
    db.add(job_model)
    db.commit()
    return RedirectResponse(url="/jobs/job-details", status_code=status.HTTP_302_FOUND)

@router.get("/display-details/{job_id}", response_class=HTMLResponse)
async def display_pdf(request: Request, job_id: int,  db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None or user["role"] != "employee":
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    db_model = db.query(models.Apply).filter(models.Apply.job_id == job_id).all()
    details = []
    for i in db_model:
        student_details = db.query(models.Users).filter(models.Users.id == i.user_id).first()
        details.append({
            "first_name": student_details.first_name,
            "last_name": student_details.last_name,
            "resume": base64.b64encode(student_details.resume).decode('utf-8')
        })
    # logger.info(f"Student details with resume: {details}")

    return templates.TemplateResponse("applied-jobs.html", {"request": request, "student_details": details, "user": user})
    