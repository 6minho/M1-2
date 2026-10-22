"""환율 데이터 CRUD + 요약(시계열 분석) 로직."""
from collections import defaultdict
from statistics import mean
from typing import Optional

from app import config
from app.firebase import get_db
from app.schemas import DataCreate, DataItem, DataUpdate, Metrics, Summary

TREND_WINDOW = 20  # 최근 20영업일 vs 그 이전 20영업일 비교
FLAT_THRESHOLD = 0.5  # ±0.5% 이내면 보합


def _col():
    return get_db().collection(config.DATA_COLLECTION)


def _to_item(doc) -> DataItem:
    d = doc.to_dict()
    return DataItem(id=doc.id, date=d["date"], value=d["value"], memo=d.get("memo", ""))


def list_data() -> list[DataItem]:
    docs = _col().order_by("date").stream()
    return [_to_item(doc) for doc in docs]


def create_data(payload: DataCreate) -> DataItem:
    body = {"date": payload.date.isoformat(), "value": payload.value, "memo": payload.memo}
    _, ref = _col().add(body)
    return DataItem(id=ref.id, **body)


def update_data(item_id: str, payload: DataUpdate) -> Optional[DataItem]:
    ref = _col().document(item_id)
    if not ref.get().exists:
        return None
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "date" in changes:
        changes["date"] = changes["date"].isoformat()
    if changes:
        ref.update(changes)
    return _to_item(ref.get())


def delete_data(item_id: str) -> bool:
    ref = _col().document(item_id)
    if not ref.get().exists:
        return False
    ref.delete()
    return True


def build_summary(items: list[DataItem]) -> Summary:
    """시계열 → 요약 정보(기간, 개수, 통계, 추세, 월평균)."""
    if not items:
        return Summary(period="데이터 없음", count=0, trend="데이터 없음")

    items = sorted(items, key=lambda x: x.date)
    values = [i.value for i in items]
    hi = max(items, key=lambda x: x.value)
    lo = min(items, key=lambda x: x.value)
    first, last = items[0], items[-1]

    metrics = Metrics(
        average=round(mean(values), 2),
        max=hi.value, max_date=hi.date,
        min=lo.value, min_date=lo.date,
        latest=last.value, latest_date=last.date,
        change_rate=round((last.value - first.value) / first.value * 100, 2),
    )

    # 최근 추세: 최근 N개 평균 vs 직전 N개 평균
    if len(values) >= TREND_WINDOW * 2:
        recent = mean(values[-TREND_WINDOW:])
        before = mean(values[-TREND_WINDOW * 2:-TREND_WINDOW])
        diff = (recent - before) / before * 100
        label = "상승" if diff > FLAT_THRESHOLD else "하락" if diff < -FLAT_THRESHOLD else "보합"
        trend = f"{label} (최근 {TREND_WINDOW}영업일 평균이 직전 대비 {diff:+.2f}%)"
    else:
        diff = metrics.change_rate
        label = "상승" if diff > FLAT_THRESHOLD else "하락" if diff < -FLAT_THRESHOLD else "보합"
        trend = f"{label} (기간 전체 {diff:+.2f}%)"

    monthly = defaultdict(list)
    for i in items:
        monthly[i.date[:7]].append(i.value)
    monthly_average = {m: round(mean(v), 2) for m, v in sorted(monthly.items())}

    return Summary(
        period=f"{first.date} ~ {last.date}",
        count=len(items),
        metrics=metrics,
        trend=trend,
        monthly_average=monthly_average,
    )


def get_summary() -> Summary:
    return build_summary(list_data())
