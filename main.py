from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from tasks.routers import router as tasks_router
from notes.routers import router as notes_router
from exceptions import BaseAppException


app = FastAPI()
app.include_router(tasks_router)
app.include_router(notes_router)


@app.exception_handler(BaseAppException)
async def base_app_exc_handler(request: Request, exc: BaseAppException):
    logger.error(exc.msg)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.msg}
    )

