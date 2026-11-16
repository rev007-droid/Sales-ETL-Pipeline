"""
main.py
-------
FastAPI entry point for SalesPulse.
"""

# import standard os
import os
# import async contextmanager
from contextlib import asynccontextmanager
# import fastapi components
from fastapi import FastAPI, Request, status
# import cors middleware
from fastapi.middleware.cors import CORSMiddleware
# import json response
from fastapi.responses import JSONResponse

# import settings instance
from backend.app.config import settings
# import database initializer
from backend.app.database import init_db, SessionLocal
# import sales model
from backend.app.models import SalesTransaction
# import etl runner
from backend.app.services.etl_service import execute_etl_pipeline

# import api routers
from backend.app.routers import (
    health, # health check
    dashboard, # analytics endpoints
    sales, # sales data
    upload, # upload file
    etl, # etl pipeline
    reports, # quality reports
    exports # download csv
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # build db schema
    init_db()
    yield # run app lifespan


# create fastapi app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade Sales Data ETL & Analytics Platform backend API.",
    lifespan=lifespan
)

# setup cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"], # allowed hosts
    allow_credentials=True, # allow cookies
    allow_methods=["*"], # allow all methods
    allow_headers=["*"], # allow all headers
)


# catch global exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # import http exception
    from fastapi.exceptions import HTTPException
    # pass explicit exceptions
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail} # return detail
        )

    # mask production errors
    if settings.ENVIRONMENT == "development":
        error_detail = str(exc) # full error dev
    else:
        error_detail = "An internal server error occurred. Please contact the administrator." # masked prod

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_detail} # return error response
    )


# register health routes
app.include_router(health.router, prefix=settings.API_PREFIX)
# register dashboard routes
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
# register sales routes
app.include_router(sales.router, prefix=settings.API_PREFIX)
# register upload routes
app.include_router(upload.router, prefix=settings.API_PREFIX)
# register etl routes
app.include_router(etl.router, prefix=settings.API_PREFIX)
# register report routes
app.include_router(reports.router, prefix=settings.API_PREFIX)
# register export routes
app.include_router(exports.router, prefix=settings.API_PREFIX)


# define root endpoint
@app.get("/", tags=["Root"])
def root():
    return {
        "service": "SalesPulse API", # app name
        "version": settings.VERSION, # app version
        "docs_url": "/docs", # swagger docs
        "health_url": f"{settings.API_PREFIX}/health" # health probe
    }


# local dev entrypoint
if __name__ == "__main__":
    # import uvicorn server
    import uvicorn
    # run server process
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
