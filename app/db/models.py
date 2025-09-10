import enum
from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, Enum, JSON, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    analyses = relationship("AnalysisLog", back_populates="user")
    otps = relationship("OtpVerification", back_populates="user")

class OtpPurpose(str, enum.Enum):
    SIGNUP = "signup"
    PASSWORD_RESET = "password_reset"

class OtpVerification(Base):
    __tablename__ = "otp_verification"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    otp_code = Column(String(10), nullable=False)
    expiry = Column(DateTime(timezone=True), nullable=False)
    purpose = Column(Enum(OtpPurpose), nullable=False)
    user = relationship("User", back_populates="otps")

class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    companies = relationship("Company", back_populates="country")

class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True, nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
    ticker_symbol = Column(String(20), unique=True, index=True)
    industry = Column(String(100))
    description = Column(Text)
    country = relationship("Country", back_populates="companies")
    analyses = relationship("AnalysisLog", back_populates="company")

class AnalysisLog(Base):
    __tablename__ = "analysis_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    result_json = Column(JSON, nullable=True)
    status = Column(String(20), default='pending') # pending, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="analyses")
    company = relationship("Company", back_populates="analyses")