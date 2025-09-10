from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# User & Auth
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    class Config:
        from_attributes = True

class OtpVerify(BaseModel):
    email: EmailStr
    otp: str

# Company & Country
class CompanyResponse(BaseModel):
    id: int
    name: str
    ticker_symbol: Optional[str] = None
    industry: Optional[str] = None
    country_code: Optional[str] = None
    class Config:
        from_attributes = True

# Analysis
class AnalysisResponse(BaseModel):
    id: int
    company_id: int
    status: str
    result: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            dict: lambda v: v.get('result_json') if v and 'result_json' in v else v
        }