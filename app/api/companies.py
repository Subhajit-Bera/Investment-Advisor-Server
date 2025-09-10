import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import models
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()
FMP_API_KEY = settings.FINANCIAL_MODELING_PREP_API_KEY

@router.get("/countries")
async def get_countries_from_db(db: Session = Depends(get_db)):
    countries = db.query(models.Country).all()
    if not countries:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://restcountries.com/v3.1/all?fields=name,cca2")
            if response.status_code == 200:
                country_data = response.json()
                for c in country_data:
                    country_exists = db.query(models.Country).filter(models.Country.code == c['cca2']).first()
                    if not country_exists:
                        new_country = models.Country(name=c['name']['common'], code=c['cca2'])
                        db.add(new_country)
                db.commit()
                countries = db.query(models.Country).order_by(models.Country.name).all()
    return countries

@router.get("/search-companies")
async def search_companies(query: str):
    if not query:
        return []
    url = f"https://financialmodelingprep.com/api/v3/search-ticker?query={query}&limit=10&apikey={FMP_API_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return [{"id": i, "name": c['name'], "ticker_symbol": c['symbol']} for i, c in enumerate(data)]
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch from FMP API")