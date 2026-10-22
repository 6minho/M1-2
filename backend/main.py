"""엔화 AI 비서 - FastAPI 진입점.

실행: uvicorn main:app --reload
문서: http://127.0.0.1:8000/docs
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config
from app.routers import chat, conversations, data

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="엔화 AI 비서 API",
    description="100엔당 원화 환율 시계열 데이터를 분석하고, 요약을 GPT 시스템 프롬프트에 주입해 대화하는 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    # 환경 변수 누락 등 설정 오류
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/", tags=["health"])
def root():
    return {"service": "엔화 AI 비서 API", "docs": "/docs"}


@app.get("/health", tags=["health"], summary="헬스 체크 (콜드스타트 깨우기용)")
def health():
    return {"status": "ok"}
