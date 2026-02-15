#!/usr/bin/env python
"""FastAPI OpenAPI 스펙을 contracts/openapi.yaml로 추출하는 스크립트.

서버를 실행하지 않고 app.openapi()를 호출하여 YAML 파일을 생성합니다.
database.py가 PostgreSQL 전용이므로 DB 관련 모듈을 mock하여 우회합니다.

사용법: python scripts/export_openapi.py
"""
import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

# 프로젝트 루트 / 백엔드 경로 설정
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
OUT_PATH = ROOT_DIR / "contracts" / "openapi.yaml"

# Settings()가 import 시점에 DATABASE_URL을 요구하므로 더미 값 설정
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://dummy:dummy@localhost/dummy")
os.environ.setdefault("SECRET_KEY", "dummy-secret-for-export")

# backend 디렉터리를 sys.path에 추가
sys.path.insert(0, str(BACKEND_DIR))

# database.py가 import 시 즉시 엔진을 생성하므로, mock 모듈로 교체
# OpenAPI 스펙 추출에는 실제 DB 연결이 필요 없음
from sqlalchemy.orm import declarative_base  # noqa: E402

_mock_db = types.ModuleType("app.database")
_mock_db.Base = declarative_base()
_mock_db.get_db = MagicMock()
_mock_db.init_db = MagicMock()
_mock_db.engine = MagicMock()
_mock_db.AsyncSessionLocal = MagicMock()
sys.modules["app.database"] = _mock_db


def main():
    from main import app  # noqa: E402

    spec = app.openapi()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        import yaml

        with open(OUT_PATH, "w", encoding="utf-8") as f:
            yaml.dump(spec, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print(f"OpenAPI spec -> {OUT_PATH}")

    except ImportError:
        json_path = OUT_PATH.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        print(f"PyYAML not installed -> JSON: {json_path}")


if __name__ == "__main__":
    main()
