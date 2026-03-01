-- Supabase RPC 함수 생성: save_song_features
-- 이 함수를 Supabase SQL Editor에서 실행하면 psycopg2 연결 없이도 supabase-py로 저장 가능

CREATE OR REPLACE FUNCTION save_song_features(
    p_song_id uuid,
    p_embedding text,  -- '[1,2,3]' 형식의 문자열 (pgvector로 변환)
    p_f0_p5 float,
    p_f0_p25 float,
    p_f0_p50 float,
    p_f0_p75 float,
    p_f0_p95 float,
    p_voiced_ratio float,
    p_timbre_brightness float,
    p_timbre_roughness float,
    p_timbre_body float,
    p_timbre_clarity float,
    p_timbre_warmth float,
    p_timbre_f0_mean float,
    p_timbre_formant_f1 float,
    p_timbre_formant_f2 float,
    p_timbre_spectral_centroid float,
    p_features_s3_key text DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER  -- service_role 키로 실행 가능하도록
AS $$
BEGIN
    INSERT INTO song_features (
        song_id,
        song_repr_embedding,
        f0_p5, f0_p25, f0_p50, f0_p75, f0_p95,
        voiced_ratio,
        timbre_brightness, timbre_roughness, timbre_body,
        timbre_clarity, timbre_warmth, timbre_f0_mean,
        timbre_formant_f1, timbre_formant_f2, timbre_spectral_centroid,
        features_s3_key,
        created_at, updated_at
    ) VALUES (
        p_song_id,
        p_embedding::vector(192),  -- 문자열을 vector 타입으로 변환
        p_f0_p5, p_f0_p25, p_f0_p50, p_f0_p75, p_f0_p95,
        p_voiced_ratio,
        p_timbre_brightness, p_timbre_roughness, p_timbre_body,
        p_timbre_clarity, p_timbre_warmth, p_timbre_f0_mean,
        p_timbre_formant_f1, p_timbre_formant_f2, p_timbre_spectral_centroid,
        p_features_s3_key,
        NOW(), NOW()
    )
    ON CONFLICT (song_id) DO UPDATE SET
        song_repr_embedding = EXCLUDED.song_repr_embedding,
        f0_p5 = EXCLUDED.f0_p5,
        f0_p25 = EXCLUDED.f0_p25,
        f0_p50 = EXCLUDED.f0_p50,
        f0_p75 = EXCLUDED.f0_p75,
        f0_p95 = EXCLUDED.f0_p95,
        voiced_ratio = EXCLUDED.voiced_ratio,
        timbre_brightness = EXCLUDED.timbre_brightness,
        timbre_roughness = EXCLUDED.timbre_roughness,
        timbre_body = EXCLUDED.timbre_body,
        timbre_clarity = EXCLUDED.timbre_clarity,
        timbre_warmth = EXCLUDED.timbre_warmth,
        timbre_f0_mean = EXCLUDED.timbre_f0_mean,
        timbre_formant_f1 = EXCLUDED.timbre_formant_f1,
        timbre_formant_f2 = EXCLUDED.timbre_formant_f2,
        timbre_spectral_centroid = EXCLUDED.timbre_spectral_centroid,
        features_s3_key = EXCLUDED.features_s3_key,
        updated_at = NOW();
END;
$$;

-- 함수 권한 설정 (service_role 키로 실행 가능하도록)
GRANT EXECUTE ON FUNCTION save_song_features TO service_role;
GRANT EXECUTE ON FUNCTION save_song_features TO authenticated;
GRANT EXECUTE ON FUNCTION save_song_features TO anon;

