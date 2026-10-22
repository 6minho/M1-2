"""AI 채팅: 데이터 요약을 시스템 프롬프트에 주입(컨텍스트 주입)한 뒤 GPT 호출."""
from openai import OpenAI

from app import config
from app.schemas import ChatResponse, ConversationCreate, Message, Summary
from app.services import conversation_service, data_service

HISTORY_LIMIT = 10  # 토큰 절약: 이전 대화는 최근 10개 메시지만 전달

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        _client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)
    return _client


def build_system_prompt(s: Summary) -> str:
    if not s.metrics:
        return "당신은 엔화 환율 비서입니다. 아직 저장된 데이터가 없다고 안내하세요."

    m = s.metrics
    monthly = ", ".join(f"{k}: {v}원" for k, v in s.monthly_average.items())
    return f"""당신은 사용자의 엔화(JPY) 환율 데이터를 분석해 주는 'AI 엔화 비서'입니다.

[사용자 데이터 요약]
- 단위: {s.unit}
- 데이터 기간: {s.period}
- 총 레코드: {s.count}개
- 주요 지표: 평균 {m.average}원, 최고 {m.max}원({m.max_date}), 최저 {m.min}원({m.min_date})
- 최신 값: {m.latest}원({m.latest_date}), 기간 전체 변화율 {m.change_rate:+}%
- 최근 트렌드: {s.trend}
- 월별 평균: {monthly}

규칙:
1. 위 데이터를 근거로 숫자를 들어 한국어로 짧고 친절하게 답하세요.
2. 데이터에 없는 미래 환율은 단정하지 말고, 추세 해석과 참고 사항으로만 말하세요.
3. 투자·환전 판단은 사용자 몫이며 이 답변은 참고용이라고 필요할 때 짧게 덧붙이세요."""


def chat(message: str, conversation_id: str | None) -> ChatResponse:
    # 1) 데이터 요약 조회
    summary = data_service.get_summary()

    # 2) 요약을 시스템 프롬프트에 삽입 + 이전 대화 이어붙이기
    history: list[Message] = []
    if conversation_id:
        conv = conversation_service.get_conversation(conversation_id)
        if conv is None:
            raise LookupError("대화를 찾을 수 없습니다.")
        history = conv.messages[-HISTORY_LIMIT:]

    messages = [{"role": "system", "content": build_system_prompt(summary)}]
    messages += [m.model_dump() for m in history]
    messages.append({"role": "user", "content": message})

    # 3) GPT API 호출
    completion = _get_client().chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        max_completion_tokens=config.OPENAI_MAX_TOKENS,
    )
    reply = (completion.choices[0].message.content or "").strip()

    # 4) 대화 자동 저장
    new_msgs = [Message(role="user", content=message), Message(role="assistant", content=reply)]
    if conversation_id:
        conversation_service.append_messages(conversation_id, new_msgs)
    else:
        title = message if len(message) <= 30 else message[:30] + "…"
        conversation_id = conversation_service.create_conversation(
            ConversationCreate(title=title, messages=new_msgs)
        ).id

    return ChatResponse(reply=reply, conversation_id=conversation_id, summary=summary)
