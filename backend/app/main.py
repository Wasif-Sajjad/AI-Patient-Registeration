import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import patients, voice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice_ai_patient_registration")

app = FastAPI(title="Voice AI Patient Registration API", version="0.1.0")

# Loosen this for production — allow the Next.js dashboard origin only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
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
