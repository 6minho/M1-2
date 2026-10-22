from fastapi import APIRouter, HTTPException

from app.schemas import DataCreate, DataItem, DataUpdate, Summary
from app.services import data_service

router = APIRouter(prefix="/api/data", tags=["data"])


# /summary 를 /{id} 계열보다 먼저 선언
@router.get("/summary", response_model=Summary, summary="데이터 요약 (프롬프트 주입용)")
def get_summary():
    return data_service.get_summary()


@router.get("", response_model=list[DataItem], summary="데이터 목록 조회 (날짜순)")
def list_data():
    return data_service.list_data()


@router.post("", response_model=DataItem, status_code=201, summary="새 데이터 추가")
def create_data(payload: DataCreate):
    return data_service.create_data(payload)


@router.put("/{item_id}", response_model=DataItem, summary="데이터 수정")
def update_data(item_id: str, payload: DataUpdate):
    item = data_service.update_data(item_id, payload)
    if item is None:
        raise HTTPException(404, "데이터를 찾을 수 없습니다.")
    return item


@router.delete("/{item_id}", summary="데이터 삭제")
def delete_data(item_id: str):
    if not data_service.delete_data(item_id):
        raise HTTPException(404, "데이터를 찾을 수 없습니다.")
    return {"deleted": item_id}
