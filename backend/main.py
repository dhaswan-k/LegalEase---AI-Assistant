"""FastAPI application entry point for LegalEase AI."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routes import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="LegalEase AI",
    description="AI-assisted legal document drafting API. Drafts are for informational and drafting "
    "assistance only and should be reviewed by a qualified legal professional.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", summary="Service status", tags=["Health"])
def home():
    return {"status": "running", "service": "LegalEase AI"}


@app.get("/health", summary="Health check", tags=["Health"])
def health():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for err in exc.errors():
        field = str(err["loc"][-1]) if err.get("loc") else "request"
        msg = str(err.get("msg", "Invalid value")).replace("Value error, ", "")
        errors[field] = msg
    return JSONResponse(
        status_code=422,
        content={"success": False, "detail": "Validation failed.", "errors": errors},
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "detail": "An unexpected server error occurred."},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
