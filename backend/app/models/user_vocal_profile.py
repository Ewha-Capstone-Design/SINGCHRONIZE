"""UserVocalProfile 모델 — AI 워커가 채우는 보컬 프로필"""
from sqlalchemy import Column, Float, Integer, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.sql import func

from app.database import Base


class UserVocalProfile(Base):
    """
    AI 워커(vocal_analysis_worker)가 분석 완료 후 UPSERT하는 테이블.
    백엔드는 존재 여부 확인 및 조회만 담당.
    vocal_repr_embedding(vector(192))은 pgvector 전용이라 ORM 미매핑.
    user_id가 PK (테이블에 id 컬럼 없음).
    """
    __tablename__ = "user_vocal_profiles"

    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    latest_analysis_job_id = Column(Uuid, nullable=True)
    latest_recording_id = Column(Uuid, nullable=True)

    # 음역대 (AI 워커 집계)
    observed_lowest_hz = Column(Float, nullable=True)
    observed_highest_hz = Column(Float, nullable=True)
    observed_lowest_note = Column(Text, nullable=True)
    observed_highest_note = Column(Text, nullable=True)
    observed_range_semitones = Column(Float, nullable=True)

    stable_lowest_hz = Column(Float, nullable=True)
    stable_highest_hz = Column(Float, nullable=True)
    stable_lowest_note = Column(Text, nullable=True)
    stable_highest_note = Column(Text, nullable=True)
    stable_range_semitones = Column(Float, nullable=True)
    stable_tessitura_low_hz = Column(Float, nullable=True)
    stable_tessitura_high_hz = Column(Float, nullable=True)
    stable_tessitura_low_note = Column(Text, nullable=True)
    stable_tessitura_high_note = Column(Text, nullable=True)

    # 레이더 차트 중앙값
    radar_median_avg = Column(Float, nullable=True)
    radar_median_pitch_stability = Column(Float, nullable=True)
    radar_median_rhythm_stability = Column(Float, nullable=True)
    radar_median_high_note_stability = Column(Float, nullable=True)
    radar_median_dynamic_control = Column(Float, nullable=True)
    radar_median_vocal_clarity = Column(Float, nullable=True)

    # 음색 요약
    latest_timbre_summary = Column(Text, nullable=True)
    latest_best_genre = Column(Text, nullable=True)

    # 프로필 집계 메타
    profile_jobs_fetched = Column(Integer, nullable=True)
    profile_valid_range_sessions = Column(Integer, nullable=True)

    # 스코어링용 컬럼 (추천 1차에서 사용)
    f0_p2 = Column(Float, nullable=True)
    f0_p5 = Column(Float, nullable=True)
    f0_p25 = Column(Float, nullable=True)
    f0_p50 = Column(Float, nullable=True)
    f0_p75 = Column(Float, nullable=True)
    f0_p95 = Column(Float, nullable=True)
    f0_p98 = Column(Float, nullable=True)
    voiced_ratio = Column(Float, nullable=True)
    timbre_brightness = Column(Float, nullable=True)
    timbre_roughness = Column(Float, nullable=True)
    timbre_body = Column(Float, nullable=True)
    timbre_clarity = Column(Float, nullable=True)
    timbre_warmth = Column(Float, nullable=True)
    timbre_f0_mean = Column(Float, nullable=True)
    timbre_formant_f1 = Column(Float, nullable=True)
    timbre_formant_f2 = Column(Float, nullable=True)
    timbre_spectral_centroid = Column(Float, nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
