from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.db import models
from app.db.session import get_db, SessionLocal
from app.services.ai_workflow import run_analysis
import json

router = APIRouter()

def run_ai_task(analysis_log_id: int, company_ticker: str, db: Session):
    try:
        print(f"Starting AI task for log {analysis_log_id}")
        result = run_analysis(company_ticker)
        
        log = db.query(models.AnalysisLog).filter(models.AnalysisLog.id == analysis_log_id).first()
        if log:
            log.status = 'completed'
            log.result_json = json.loads(json.dumps(result))
            db.commit()
        print(f"Completed AI task for log {analysis_log_id}")

    except Exception as e:
        print(f"AI task failed for log {analysis_log_id}: {e}")
        log = db.query(models.AnalysisLog).filter(models.AnalysisLog.id == analysis_log_id).first()
        if log:
            log.status = 'failed'
            db.commit()
    finally:
        db.close()


@router.post("/start-analysis")
async def start_company_analysis(ticker: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.ticker_symbol == ticker).first()
    if not company:
        company = models.Company(name=ticker, ticker_symbol=ticker)
        db.add(company)
        db.commit()
        db.refresh(company)

    new_log = models.AnalysisLog(company_id=company.id, status='pending')
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    # Pass a new session to the background task
    background_tasks.add_task(run_ai_task, new_log.id, company.ticker_symbol, SessionLocal())

    return {"analysis_id": new_log.id}


@router.get("/analysis-status/{analysis_id}")
def get_analysis_status(analysis_id: int, db: Session = Depends(get_db)):
    log = db.query(models.AnalysisLog).filter(models.AnalysisLog.id == analysis_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "analysis_id": log.id,
        "status": log.status,
        "result": log.result_json if log.status == 'completed' else None
    }