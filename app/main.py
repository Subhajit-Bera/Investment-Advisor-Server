from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, companies, analysis

app = FastAPI(title="AI Investment Advisor")

# CORS middleware
origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(companies.router, prefix="/api/data", tags=["Company Data"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["AI Analysis"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Investment Advisor API"}