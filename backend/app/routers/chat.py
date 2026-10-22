import logging

from fastapi import APIRouter, HTTPException
from openai import OpenAIError

from app.schemas import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter(prefix="/api", tags=["chat"])
log = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse, summary="AI 채팅 (데이터 요약 컨텍스트 주입 + 자동 저장)")
def chat(req: ChatRequest):
    try:
        return chat_service.chat(req.message, req.conversation_id)
    except LookupError as e:
        raise HTTPException(404, str(e))
    except OpenAIError as e:
        log.exception("OpenAI 호출 실패")
        raise HTTPException(502, f"AI 응답 생성에 실패했습니다: {e.__class__.__name__}")
