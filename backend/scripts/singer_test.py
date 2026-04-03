import os
import json
import asyncio
import httpx
import logging
import base64
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from openai import AsyncOpenAI
from sqlalchemy import select, or_
from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Singer


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# ── OpenAI: feat. 포함 이름을 1~2명의 가수명으로 정제 ────────────
async def fix_feat_name(name: str) -> list[str]:
    """
    feat. 포함된 이름을 AI로 정제해 실제 가수명 리스트로 반환.
    - 콜라보 곡이면 두 명: ["아이유", "오혁"]
    - 메인 아티스트만 의미 있으면 한 명: ["BTS"]
    """
    prompt = f"""\
You are a Korean music database expert.

This string is stored as a singer name but contains "feat." or similar: "{name}"

Extract the actual artist name(s). Rules:
- If both artists are well-known and equally important (collab) → return both names.
- If one is clearly the main artist and the other is just a feature → return only the main artist.
- Return ONLY the clean artist name(s), no feat./ft./featuring text.

Respond ONLY as JSON: {{"names": ["name1"]}} or {{"names": ["name1", "name2"]}}"""
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        names = [n.strip() for n in result.get("names", []) if n.strip()]
        return names if names else [name]
    except Exception as e:
        logger.error(f"OpenAI feat. 정제 실패 ({name}): {e}")
        return [name]


# ── OpenAI: 이름이 가수명인지 판별 + 노래 제목이면 가수명으로 수정 ──
async def validate_and_fix_singer_name(name: str) -> dict:
    """
    - 유효한 가수명 → {"action": "keep"}
    - 노래 제목/앨범명 → {"action": "fix", "corrected_name": "실제 가수명"}
    - 판단 불가/쓰레기 → {"action": "keep"}  (안전하게 유지)
    """
    prompt = f"""\
You are a Korean music database expert.

The following string was stored as an artist/singer name in a database: "{name}"

Task:
1. If this is already a valid singer/artist/group name → respond with action "keep".
2. If this looks like a SONG TITLE or ALBUM NAME → find the actual artist who sang/released it,
   and respond with action "fix" and the corrected artist name.
3. If you cannot determine → respond with action "keep".

Respond ONLY as JSON (no extra text):
{{"action": "keep"}} or {{"action": "fix", "corrected_name": "<actual artist name>"}}"""
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"OpenAI 검증 실패 ({name}): {e}")
        return {"action": "keep"}  # API 오류 시 안전하게 유지


# ── Spotify: 토큰 발급 ───────────────────────────────────────────
async def get_spotify_token(client: httpx.AsyncClient) -> str:
    auth_str = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_str.encode()).decode()
    res = await client.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth_base64}", "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"}
    )
    return res.json()["access_token"]


# ── Spotify: 사진 URL ────────────────────────────────────────────
async def fetch_spotify_photo(client: httpx.AsyncClient, token: str, singer_name: str):
    try:
        await asyncio.sleep(1.5)
        res = await client.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": singer_name, "type": "artist", "limit": 1}
        )
        items = res.json().get("artists", {}).get("items", [])
        if items and items[0].get("images"):
            return items[0]["images"][0]["url"]
    except Exception as e:
        logger.error(f"❌ Spotify 사진 실패 ({singer_name}): {e}")
    return None


# ── OpenAI: 성별 및 aliases ──────────────────────────────────────
async def ask_openai_info(singer_name: str):
    prompt = f"""
    아래 한국 가수의 정보를 JSON 형식으로 알려줘.
    가수 이름: {singer_name}

    응답 형식:
    {{
      "gender": "male" 또는 "female" 또는 "mixed",
      "aliases": "대표곡, 멤버이름, 또는 관련 키워드 3~4개"
    }}
    """
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"❌ OpenAI 호출 실패 ({singer_name}): {e}")
        return None


# ── 메인 ─────────────────────────────────────────────────────────
async def main():
    logger.info("🚀 [SINGCHRONIZE] 가수 DB 전체 보정 시작!")

    async with httpx.AsyncClient() as sp_client:
        spotify_token = await get_spotify_token(sp_client)

        async with AsyncSessionLocal() as db:

            # ════════════════════════════════════════════════════
            # STEP 0-A: feat. 제거 및 빈 이름 삭제
            # ════════════════════════════════════════════════════
            feat_targets_result = await db.execute(
                select(Singer).where(Singer.name.ilike("%feat%"))
            )
            feat_targets = feat_targets_result.scalars().all()
            logger.info(f"[STEP 0-A] feat. 포함 가수: {len(feat_targets)}명")

            for singer in feat_targets:
                names = await fix_feat_name(singer.name)
                original = singer.name
                singer.name = names[0]
                logger.info(f"  ✏️  feat. 정제: '{original}' → '{names[0]}'")

                # 두 명으로 분리된 경우 새 Singer 레코드 추가
                if len(names) == 2:
                    new_singer = Singer(name=names[1], gender="unknown")
                    db.add(new_singer)
                    logger.info(f"  ➕  콜라보 가수 추가: '{names[1]}'")

                await asyncio.sleep(0.1)

            await db.commit()
            logger.info("[STEP 0-A] 완료")

            # ════════════════════════════════════════════════════
            # STEP 0-B: OpenAI로 노래 제목/쓰레기 데이터 감지 및 삭제
            # ════════════════════════════════════════════════════
            all_singers_result = await db.execute(select(Singer))
            all_singers = all_singers_result.scalars().all()
            logger.info(f"[STEP 0-B] 전체 가수명 유효성 검사: {len(all_singers)}명")

            invalid_count = 0
            for i, singer in enumerate(all_singers, 1):
                result = await validate_and_fix_singer_name(singer.name)
                if result.get("action") == "fix":
                    corrected = result.get("corrected_name", "").strip()
                    if corrected:
                        logger.info(f"  ✏️  [{i}] 이름 수정: '{singer.name}' → '{corrected}'")
                        singer.name = corrected
                        invalid_count += 1
                    else:
                        logger.info(f"  ⚠️  [{i}] fix 요청이지만 corrected_name 없음, 유지: '{singer.name}'")
                else:
                    logger.info(f"  ✅ [{i}/{len(all_singers)}] '{singer.name}' — 유효")

                await asyncio.sleep(0.1)  # OpenAI rate limit 방지

                if i % 20 == 0:
                    await db.commit()
                    logger.info(f"  💾 중간 저장 ({i}명 처리)")

            await db.commit()
            logger.info(f"[STEP 0-B] 완료 — {invalid_count}명 삭제")

            # ════════════════════════════════════════════════════
            # STEP 1~2: 사진 없거나 gender unknown인 가수 보정
            # ════════════════════════════════════════════════════
            stmt = select(Singer).where(
                or_(
                    Singer.photo_url == None,
                    Singer.photo_url == "",
                    Singer.gender == "unknown"
                )
            )
            result = await db.execute(stmt)
            target_singers = result.scalars().all()

            total = len(target_singers)
            logger.info(f"[STEP 1~2] 사진/성별 보정 대상: {total}명")

            for i, singer in enumerate(target_singers, 1):
                if not singer.photo_url or "via.placeholder" in singer.photo_url:
                    photo = await fetch_spotify_photo(sp_client, spotify_token, singer.name)
                    if photo:
                        singer.photo_url = photo

                if singer.gender == "unknown":
                    info = await ask_openai_info(singer.name)
                    if info:
                        singer.gender = info.get("gender", "unknown")
                        if not singer.aliases:
                            singer.aliases = info.get("aliases", "")

                logger.info(f"  ✨ [{i}/{total}] {singer.name} 완료")

                if i % 10 == 0:
                    await db.commit()
                    logger.info("  💾 중간 저장 완료")

            await db.commit()
            logger.info("✅ 전체 보정 완료!")


if __name__ == "__main__":
    asyncio.run(main())
