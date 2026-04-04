-- Supabase SQL Editor / psql용 예시: 3차 추천을 수동 검증할 때만 사용.
-- 1) 아래 UUID·곡 ID를 실제 users / songs FK에 맞게 바꿉니다.
-- 2) vocal_repr_embedding 은 192차원 pgvector 리터럴이어야 합니다 (여기서는 짧은 예시 대신 주석 처리).
--
-- 시나리오: target_user 와 비슷한 임베딩의 neighbor_a 가 song_pop 을 위시 → target에 song_pop 이 상위로.

-- 예시 (실행 전 수정 필수):
/*
INSERT INTO user_vocal_profiles (user_id, vocal_repr_embedding, updated_at)
VALUES
  ('TARGET-USER-UUID', '[...192 floats...]'::vector, now()),
  ('NEIGHBOR-A-UUID',  '[...same or very close to target...]'::vector, now()),
  ('NEIGHBOR-B-UUID',  '[...orthogonal...]'::vector, now())
ON CONFLICT (user_id) DO UPDATE SET
  vocal_repr_embedding = EXCLUDED.vocal_repr_embedding,
  updated_at = now();

INSERT INTO wishlist_items (user_id, song_id, created_at)
VALUES
  ('NEIGHBOR-A-UUID', 'SONG-POP-UUID', now() - interval '1 hour'),
  ('NEIGHBOR-B-UUID', 'SONG-OTHER-UUID', now() - interval '1 hour');

INSERT INTO song_features (song_id, song_repr_embedding, ...)
VALUES
  ('SONG-POP-UUID',   '[...close to target vocal embedding...]'::vector, ...),
  ('SONG-OTHER-UUID', '[...low compatibility...]'::vector, ...)
ON CONFLICT (song_id) DO UPDATE SET song_repr_embedding = EXCLUDED.song_repr_embedding;
*/

-- 검증: stage3-api 실행 후
-- curl -s localhost:8000/stage3/similar-voice-picks -H 'Content-Type: application/json' \
--   -d '{"user_id":"TARGET-USER-UUID","period":"week","limit":10}'
