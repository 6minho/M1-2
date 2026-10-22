"""data/jpy_krw.csv 를 Firestore 'data' 컬렉션에 일괄 업로드.

실행 (backend 폴더에서):  python -m scripts.seed_data
이미 데이터가 있으면 중복을 막기 위해 --reset 옵션으로 기존 문서를 지운 뒤 넣는다.
"""
import csv
import sys
from pathlib import Path

from app import config
from app.firebase import get_db

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "jpy_krw.csv"


def main():
    db = get_db()
    col = db.collection(config.DATA_COLLECTION)

    existing = list(col.limit(1).stream())
    if existing and "--reset" not in sys.argv:
        print("이미 데이터가 있습니다. 다시 넣으려면 --reset 옵션을 붙이세요.")
        return
    if "--reset" in sys.argv:
        for doc in col.stream():
            doc.reference.delete()
        print("기존 데이터 삭제 완료")

    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    batch = db.batch()
    for i, row in enumerate(rows, 1):
        batch.set(col.document(), {"date": row["date"], "value": float(row["value"]), "memo": row["memo"]})
        if i % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    print(f"{len(rows)}개 업로드 완료")


if __name__ == "__main__":
    main()
