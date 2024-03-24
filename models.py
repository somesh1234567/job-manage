from database import Base
from sqlalchemy import Column, Integer, LargeBinary, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import BYTEA
from datetime import datetime

class Users(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    normal_password = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)
    phone_number = Column(String)
    resume = Column(LargeBinary)

class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    normal_password = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)

class Jobs(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    company = Column(String)
    company_url = Column(String)
    location = Column(String)
    description = Column(String)
    date_posted = Column(DateTime)
    is_active = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("employee.id"))

class Apply(Base):
    __tablename__ = "apply"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    user_id = Column(Integer, ForeignKey("student.id"))
    date_applied = Column(DateTime, default=datetime.now())
    is_active = Column(Boolean, default=True)
