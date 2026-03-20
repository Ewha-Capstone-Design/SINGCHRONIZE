"""OpenAI situation classifier — classifies songs into 8 situation labels"""
import asyncio
import json
import logging
from typing import Optional

from openai import AsyncOpenAI, RateLimitError, APIError

logger = logging.getLogger(__name__)

SITUATION_LABELS = [
    "회식하며 즐길 때",
    "가족과 함께할 때",
    "친구랑 놀 때",
    "연인과 함께할 때",
    "공연을 준비할 때",
    "신나게 놀고 싶을 때",
    "감성에 젖고 싶을 때",
    "엔딩곡이 필요할 때",
]

_SYSTEM_PROMPT = """\
You are a Korean karaoke song situation classifier.
Given only the song title, artist, and genre, select the single most fitting label from the 8 options below.

=== Label Criteria ===

1. "회식하며 즐길 때"  (Company dinner / drinking party)
   - Songs that adults (30s+) love to sing at company dinners or office drinking gatherings
   - Trot, 7080 hits, classic crowd-pleasers that liven up group settings
   - Familiar across generations; great for raising the group mood together

2. "가족과 함께할 때"  (Family time)
   - Wholesome, warm songs suitable for all ages (children to grandparents)
   - Family outings, holiday gatherings, road trips — clean and heartwarming
   - Pure, cheerful, feel-good atmosphere

3. "친구랑 놀 때"  (Hanging out with friends)
   - K-pop, pop, or hip-hop enjoyed by younger crowds (teens~20s) in casual hangouts
   - Light and fun; fits house parties or outings more than nightclubs
   - Less formal than a company dinner, less intense than a club rave

4. "연인과 함께할 때"  (Romantic moment with a partner)
   - Love songs centered on affection, excitement, or longing between partners
   - Sweet, romantic atmosphere — dates, night drives, confessions
   - The emotion is clearly about romance between two people

5. "공연을 준비할 때"  (Preparing for a performance / showstopper)
   - Songs that showcase vocal ability: high notes, runs, dramatic delivery
   - Ideal for impressing an audience at karaoke or on stage
   - Dramatic arc; the kind of song that earns applause

6. "신나게 놀고 싶을 때"  (Party / dance mode)
   - Trendy dance-pop, EDM, or hip-hop with a hard beat for clubs or mid-party hype
   - High-energy songs that keep the party going — does NOT have to be universally known
   - Newer or niche tracks are fine here; energy and beat matter most

7. "감성에 젖고 싶을 때"  (Emotional / melancholic mood)
   - Quiet ballads about sadness, longing, loneliness, or finding comfort
   - Best listened to alone late at night or when feeling reflective
   - NOT romance-focused — the core emotion is grief, nostalgia, or solace

8. "엔딩곡이 필요할 때"  (The grand finale / closing anthem)
   - A universally beloved classic hit that EVERYONE at the party already knows by heart
   - Used to close a karaoke session or party with a massive group sing-along (떼창)
   - Think: concert encore, festival finale — impactful, triumphant, crowd-wide
   - The longer the song has been loved and the more widely it is known, the stronger the fit
   - Must feel like a grand, triumphant GROUP ending, NOT a quiet wind-down

=== How to distinguish similar labels ===
- "신나게" vs "엔딩곡": "신나게" = trendy mid-party banger (niche OK); "엔딩곡" = timeless anthem everyone sings together to close the night
- "연인" vs "감성": "연인" = romance/love theme; "감성" = sadness/loneliness/comfort theme
- "회식" vs "친구": "회식" = older adult crowd (30s+); "친구" = younger crowd (teens~20s)
- "엔딩곡" vs "공연": "엔딩곡" = everyone sings together; "공연" = one person shows off their skills

=== Golden Examples ===

Input: Title: 사랑의 배터리 | Artist: 박상민 | Genre: 발라드
Output: {"label": "회식하며 즐길 때", "reason": "30-40대 직장인 회식 단골 노래로 누구나 따라부를 수 있는 국민 발라드입니다."}

Input: Title: 가족사진 | Artist: 성시경 | Genre: 발라드
Output: {"label": "가족과 함께할 때", "reason": "가족을 주제로 한 따뜻하고 건전한 노래로 세대를 초월해 함께 들을 수 있습니다."}

Input: Title: FIRE | Artist: BTS | Genre: 힙합
Output: {"label": "친구랑 놀 때", "reason": "10-20대가 친구들과 어울릴 때 신나게 즐길 수 있는 아이돌 힙합입니다."}

Input: Title: 사랑을 했다 | Artist: IKON | Genre: 발라드 힙합
Output: {"label": "연인과 함께할 때", "reason": "연인에 대한 사랑과 그리움을 담은 달콤한 러브송입니다."}

Input: Title: 거짓말이야 | Artist: 임창정 | Genre: 발라드
Output: {"label": "공연을 준비할 때", "reason": "고음과 감정 표현이 필요한 노래로 노래방에서 실력을 보여주기에 적합합니다."}

Input: Title: TOMBOY | Artist: (여자)아이들 | Genre: 댄스
Output: {"label": "신나게 놀고 싶을 때", "reason": "강한 비트의 트렌디한 걸그룹 댄스곡으로 파티나 클럽에서 즐기기 좋습니다."}

Input: Title: 야생화 | Artist: 박효신 | Genre: 발라드
Output: {"label": "감성에 젖고 싶을 때", "reason": "혼자 듣기 좋은 서정적인 발라드로 그리움과 위로의 감성을 전달합니다."}

Input: Title: 아파트 | Artist: 로이킨 & 핑클 | Genre: 댄스
Output: {"label": "엔딩곡이 필요할 때", "reason": "노래방 마지막 곡으로 모두가 함께 떼창하는 국민 댄스곡입니다."}

=== Rules ===
- Choose EXACTLY ONE label from the 8 options.
- Copy the label name EXACTLY as written above (Korean text, no changes).
- Respond ONLY in this JSON format:
{"label": "<exact label name>", "reason": "<1-2 sentences in Korean explaining the choice>"}
"""


class SituationClassifier:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self._client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def classify(
        self,
        title: str,
        artist: str,
        genre: Optional[str],
        max_retries: int = 3,
    ) -> dict:
        """노래 정보를 받아 상황 라벨 분류 결과 반환.

        Returns:
            {"label": "...", "reason": "..."}
        Raises:
            ValueError: 라벨이 유효하지 않거나 JSON 파싱 실패
            APIError:   재시도 초과 시
        """
        user_content = f"Title: {title}\nArtist: {artist}\nGenre: {genre or 'unknown'}"

        last_exc: Exception | None = None
        response = None

        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self.model,
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                )
                break
            except RateLimitError as e:
                wait = 2 ** attempt * 5  # 5s → 10s → 20s
                logger.warning("Rate limit. %ds 후 재시도 (%d/%d)...", wait, attempt + 1, max_retries)
                await asyncio.sleep(wait)
                last_exc = e
            except APIError as e:
                logger.warning("OpenAI API 오류: %s. 재시도 (%d/%d)...", e, attempt + 1, max_retries)
                await asyncio.sleep(2 ** attempt)
                last_exc = e
        else:
            raise last_exc

        raw = response.choices[0].message.content
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {raw}") from e

        label = result.get("label", "")
        if label not in SITUATION_LABELS:
            raise ValueError(f"유효하지 않은 라벨: '{label}'")

        return {"label": label, "reason": result.get("reason", "")}
