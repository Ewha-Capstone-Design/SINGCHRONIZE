import { useMemo, useState } from 'react';
import type { SongUiType } from '@/entities/song/model/types';
import type { ArtistUiType } from '@/entities/artist/model/types';

import { MOCK_SONG_LIST } from '@/entities/song/model/mock';
import { MOCK_ALL_ARTISTS } from '@/entities/artist/model/mock';

export const useBlockedItems = (type: 'song' | 'artist') => {
  const [query, setQuery] = useState('');

  // TODO: API로 교체
  // song:   const { data } = useQuery(fetchBlockedSongs())
  //         const blockedItems: SongUiType[] = data.map(toSongUi)
  // artist: const { data } = useQuery(fetchBlockedArtists())
  //         const blockedItems: ArtistUiType[] = data.map(toArtistUi)
  const blockedItems = type === 'song' ? MOCK_SONG_LIST : MOCK_ALL_ARTISTS;

  const filteredItems = useMemo(() => {
    const q = query.trim();
    if (!q) return blockedItems;

    if (type === 'song') {
      return (blockedItems as SongUiType[]).filter((item) =>
        `${item.title} ${item.artist}`.includes(q)
      );
    }

    return (blockedItems as ArtistUiType[]).filter((item) => item.name.includes(q));
  }, [query, blockedItems, type]);

  const normalizedItems = useMemo(() => {
    return filteredItems.map((item) =>
      type === 'song'
        ? {
            id: (item as SongUiType).id,
            thumbnail: (item as SongUiType).thumbnail,
            title: (item as SongUiType).title,
            artist: (item as SongUiType).artist,
          }
        : {
            id: (item as ArtistUiType).id,
            thumbnail: (item as ArtistUiType).imageUrl ?? '',
            title: (item as ArtistUiType).name,
            artist: undefined,
          }
    );
  }, [filteredItems, type]);

  return { query, setQuery, normalizedItems };
};
