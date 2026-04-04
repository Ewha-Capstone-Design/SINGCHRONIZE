from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


PeriodLiteral = Literal["today", "week", "month"]


class RecommendRequest(BaseModel):
    user_id: str
    period: PeriodLiteral = "week"
    limit: int = Field(default=10, ge=1, le=100)
    interaction_since: Optional[datetime] = Field(
        None,
        description="이 시각(포함) 이후에 추가된 위시만 집계. 지정 시 period로 계산한 시작일은 쓰지 않음.",
    )
    interaction_until: Optional[datetime] = Field(
        None,
        description="이 시각(포함) 이전까지의 위시만 집계. 미지정 시 요청 시각(UTC)까지.",
    )

    @model_validator(mode="after")
    def check_window(self):
        if self.interaction_since is not None and self.interaction_until is not None:
            if self.interaction_until < self.interaction_since:
                raise ValueError("interaction_until 은 interaction_since 보다 이후여야 합니다.")
        return self


class RecommendItem(BaseModel):
    song_id: str
    score: float


class RecommendResponse(BaseModel):
    results: list[RecommendItem]
    meta: Optional[dict] = None
