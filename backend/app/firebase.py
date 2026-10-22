"""Firestore 클라이언트 초기화 (앱 전체에서 1회)."""
import json

import firebase_admin
from firebase_admin import credentials, firestore

from app import config

_db = None


def get_db():
    global _db
    if _db is not None:
        return _db

    if not firebase_admin._apps:
        if config.FIREBASE_SERVICE_ACCOUNT_JSON:
            cred = credentials.Certificate(json.loads(config.FIREBASE_SERVICE_ACCOUNT_JSON))
        elif config.FIREBASE_SERVICE_ACCOUNT_PATH:
            cred = credentials.Certificate(config.FIREBASE_SERVICE_ACCOUNT_PATH)
        else:
            raise RuntimeError(
                "Firebase 인증 정보가 없습니다. FIREBASE_SERVICE_ACCOUNT_JSON 또는 "
                "FIREBASE_SERVICE_ACCOUNT_PATH 환경 변수를 설정하세요."
            )
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db
