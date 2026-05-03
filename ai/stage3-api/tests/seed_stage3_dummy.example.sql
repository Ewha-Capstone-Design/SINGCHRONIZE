-- 로컬/스테이징에서 stage3-api 동작 확인용 더미 시드 예시.
-- 실제 스키마·RLS·UUID에 맞게 수정 후 실행하세요.

-- INSERT INTO user_vocal_profiles (user_id, vocal_repr_embedding) VALUES
--   ('00000000-0000-0000-0000-000000000001', '[0.1,0.2,0.3]'::vector);

-- INSERT INTO wishlist_items (user_id, song_id, created_at) VALUES
--   ('00000000-0000-0000-0000-000000000002', 'song-uuid-1', now());

-- INSERT INTO song_features (song_id, song_repr_embedding) VALUES
--   ('song-uuid-1', '[0.1,0.2,0.3]'::vector);
