import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import patients, voice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice_ai_patient_registration")

app = FastAPI(title="Voice AI Patient Registration API", version="0.1.0")

# Parse allowed origins: supports "*" or a comma-separated list of domains.
_raw_origins = settings.allowed_origins.strip()
_allowed_origins = ["*"] if _raw_origins == "*" else [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_raw_origins != "*",  # credentials only when not wildcard
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(patients.router)
app.include_router(voice.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"data": None, "error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"data": None, "error": exc.errors()},
    )


@app.get("/health")
async def health():
    return {"data": {"status": "ok"}, "error": None}
