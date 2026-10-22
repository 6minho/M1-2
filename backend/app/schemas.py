"""Pydantic 모델: 요청 데이터 검증 + 응답 형태 정의."""
import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------- 환율 데이터 ----------
class DataCreate(BaseModel):
    date: dt.date = Field(..., description="기준일 (YYYY-MM-DD)", examples=["2026-10-22"])
    value: float = Field(..., gt=0, lt=10000, description="100엔당 원화 환율", examples=[839.62])
    memo: str = Field("", max_length=200, description="메모", examples=["엔화 약세 지속"])


class DataUpdate(BaseModel):
    date: Optional[dt.date] = None
    value: Optional[float] = Field(None, gt=0, lt=10000)
    memo: Optional[str] = Field(None, max_length=200)


class DataItem(BaseModel):
    id: str
    date: str
    value: float
    memo: str = ""


class Metrics(BaseModel):
    average: float
    max: float
    max_date: str
    min: float
    min_date: str
    latest: float
    latest_date: str
    change_rate: float = Field(..., description="기간 전체 변화율(%)")


class Summary(BaseModel):
    unit: str = "원 / 100엔"
    period: str
    count: int
    metrics: Optional[Metrics] = None
    trend: str
    monthly_average: dict[str, float] = {}


# ---------- 대화 ----------
class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class ConversationCreate(BaseModel):
    title: str = Field("새 대화", max_length=100)
    messages: list[Message] = Field(default_factory=list)


class ConversationListItem(BaseModel):
    """목록 응답에는 messages를 포함하지 않는다. (전체는 GET /api/conversations/{id})"""
    id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str


class Conversation(ConversationListItem):
    messages: list[Message]


# ---------- 채팅 ----------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, examples=["요즘 엔화 사도 될까?"])
    conversation_id: Optional[str] = Field(None, description="이어서 대화할 경우 기존 대화 ID")


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    summary: Summary
