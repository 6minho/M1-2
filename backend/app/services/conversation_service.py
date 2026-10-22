"""대화 기록 저장/조회/삭제."""
from datetime import datetime, timezone
from typing import Optional

from app import config
from app.firebase import get_db
from app.schemas import Conversation, ConversationCreate, ConversationListItem, Message


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _col():
    return get_db().collection(config.CONVERSATION_COLLECTION)


def _to_conv(doc) -> Conversation:
    d = doc.to_dict()
    msgs = d.get("messages", [])
    return Conversation(
        id=doc.id,
        title=d.get("title", "새 대화"),
        message_count=len(msgs),
        created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
        messages=[Message(**m) for m in msgs],
    )


def create_conversation(payload: ConversationCreate) -> Conversation:
    now = _now()
    body = {
        "title": payload.title,
        "messages": [m.model_dump() for m in payload.messages],
        "created_at": now,
        "updated_at": now,
    }
    _, ref = _col().add(body)
    return _to_conv(ref.get())


def list_conversations() -> list[ConversationListItem]:
    docs = _col().order_by("updated_at", direction="DESCENDING").stream()
    result = []
    for doc in docs:
        c = _to_conv(doc)
        result.append(ConversationListItem(**c.model_dump(exclude={"messages"})))
    return result


def get_conversation(conv_id: str) -> Optional[Conversation]:
    doc = _col().document(conv_id).get()
    return _to_conv(doc) if doc.exists else None


def append_messages(conv_id: str, messages: list[Message]) -> Optional[Conversation]:
    ref = _col().document(conv_id)
    doc = ref.get()
    if not doc.exists:
        return None
    current = doc.to_dict().get("messages", [])
    current.extend(m.model_dump() for m in messages)
    ref.update({"messages": current, "updated_at": _now()})
    return _to_conv(ref.get())


def delete_conversation(conv_id: str) -> bool:
    ref = _col().document(conv_id)
    if not ref.get().exists:
        return False
    ref.delete()
    return True
