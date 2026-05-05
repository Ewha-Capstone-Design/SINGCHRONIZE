import { useMemo, useState } from 'react';
import {
  useBlockedSingers,
  useBlockedSongs,
  useUnblockSinger,
  useUnblockSong,
} from '@/entities/user';

export const useBlockedItems = (type: 'song' | 'artist') => {
  const [query, setQuery] = useState('');

  const blockedSongQuery = useBlockedSongs();
  const blockedSingerQuery = useBlockedSingers();

  const { mutate: unblockSong, isPending: isUnblockSongPending } = useUnblockSong();
  const { mutate: unblockSinger, isPending: isUnblockSingerPending } = useUnblockSinger();

  const rawItems = useMemo(() => {
    if (type === 'song') {
      return (blockedSongQuery.data?.blocked_songs ?? []).map((item) => ({
        id: item.song_id,
        thumbnail: item.album_cover ?? undefined,
        title: item.title,
        artist: item.artist,
      }));
    }
    return (blockedSingerQuery.data?.blocked_singers ?? []).map((item) => ({
      id: String(item.singer_id),
      thumbnail: item.photo_url ?? undefined,
      title: item.name, // 가수명이 title로 들어가서 artist는 undefined로 처리
      artist: undefined as string | undefined,
    }));
  }, [type, blockedSongQuery.data, blockedSingerQuery.data]);

  const normalizedItems = useMemo(() => {
    const q = query.trim();
    if (!q) return rawItems;
    return rawItems.filter((item) => `${item.title} ${item.artist ?? ''}`.includes(q));
  }, [query, rawItems]);

  const unblock = (id: string) => {
    if (type === 'song') unblockSong(id);
    else unblockSinger(Number(id));
  };

  const isLoading =
    type === 'song'
      ? blockedSongQuery.isLoading || isUnblockSongPending
      : blockedSingerQuery.isLoading || isUnblockSingerPending;

  return { query, setQuery, normalizedItems, unblock, isLoading };
};
