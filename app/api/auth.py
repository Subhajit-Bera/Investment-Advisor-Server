from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pytz

from app.db import models
from app.db.session import get_db, SessionLocal
from app.schemas import schemas
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.services.email_service import generate_otp, send_otp_email

router = APIRouter()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = models.User(name=user_data.name, email=user_data.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    otp = generate_otp()
    expiry_time = datetime.now(pytz.utc) + timedelta(minutes=5)
    new_otp = models.OtpVerification(user_id=new_user.id, otp_code=otp, expiry=expiry_time, purpose='signup')
    db.add(new_otp)
    db.commit()

    await send_otp_email(new_user.email, otp)
    
    return {"message": "User created. OTP sent to email for verification."}

@router.post("/verify-otp")
def verify_otp(data: schemas.OtpVerify, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp_record = db.query(models.OtpVerification).filter(
        models.OtpVerification.user_id == user.id,
        models.OtpVerification.otp_code == data.otp,
        models.OtpVerification.purpose == 'signup'
    ).order_by(models.OtpVerification.id.desc()).first()

    if not otp_record or otp_record.expiry < datetime.now(pytz.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    db.delete(otp_record)
    db.commit()

    return {"message": "Email verified successfully. You can now log in."}

@router.post("/login")
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, samesite="lax", secure=True)
    response.set_cookie(key="refresh_token", value=f"Bearer {refresh_token}", httponly=True, samesite="lax", secure=True)
    
    return schemas.UserResponse.from_orm(user)