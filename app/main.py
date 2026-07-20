from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.core import config


def create_app() -> FastAPI:
    application = FastAPI(
        title=config.APP_TITLE,
        description=config.APP_DESCRIPTION,
        version=__version__,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)
    return application


app = create_app()
