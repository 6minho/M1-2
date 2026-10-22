from fastapi import APIRouter, HTTPException

from app.schemas import Conversation, ConversationCreate, ConversationListItem
from app.services import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=Conversation, status_code=201, summary="대화 저장")
def create_conversation(payload: ConversationCreate):
    return conversation_service.create_conversation(payload)


@router.get(
    "",
    response_model=list[ConversationListItem],
    summary="대화 목록 조회 (messages 미포함, 최신순)",
)
def list_conversations():
    return conversation_service.list_conversations()


@router.get("/{conv_id}", response_model=Conversation, summary="특정 대화 전체 messages 조회")
def get_conversation(conv_id: str):
    conv = conversation_service.get_conversation(conv_id)
    if conv is None:
        raise HTTPException(404, "대화를 찾을 수 없습니다.")
    return conv


@router.delete("/{conv_id}", summary="대화 삭제")
def delete_conversation(conv_id: str):
    if not conversation_service.delete_conversation(conv_id):
        raise HTTPException(404, "대화를 찾을 수 없습니다.")
    return {"deleted": conv_id}
