-- user_vocal_profiles: song_features 와 동일 의미의 1차 추천용 컬럼 추가
-- (song_features 테이블은 변경하지 않음)
-- Supabase SQL Editor 에서 실행. pgvector 확장이 이미 있어야 함.

ALTER TABLE public.user_vocal_profiles
  ADD COLUMN IF NOT EXISTS vocal_repr_embedding vector(192);

ALTER TABLE public.user_vocal_profiles
  ADD COLUMN IF NOT EXISTS f0_p2 real,
  ADD COLUMN IF NOT EXISTS f0_p5 real,
  ADD COLUMN IF NOT EXISTS f0_p25 real,
  ADD COLUMN IF NOT EXISTS f0_p50 real,
  ADD COLUMN IF NOT EXISTS f0_p75 real,
  ADD COLUMN IF NOT EXISTS f0_p95 real,
  ADD COLUMN IF NOT EXISTS f0_p98 real,
  ADD COLUMN IF NOT EXISTS voiced_ratio real;

ALTER TABLE public.user_vocal_profiles
  ADD COLUMN IF NOT EXISTS timbre_brightness real,
  ADD COLUMN IF NOT EXISTS timbre_roughness real,
  ADD COLUMN IF NOT EXISTS timbre_body real,
  ADD COLUMN IF NOT EXISTS timbre_clarity real,
  ADD COLUMN IF NOT EXISTS timbre_warmth real,
  ADD COLUMN IF NOT EXISTS timbre_f0_mean real,
  ADD COLUMN IF NOT EXISTS timbre_formant_f1 real,
  ADD COLUMN IF NOT EXISTS timbre_formant_f2 real,
  ADD COLUMN IF NOT EXISTS timbre_spectral_centroid real;

COMMENT ON COLUMN public.user_vocal_profiles.vocal_repr_embedding IS
  'ECAPA 대표 임베딩 (song_features.song_repr_embedding 과 동일 차원·정규화)';
