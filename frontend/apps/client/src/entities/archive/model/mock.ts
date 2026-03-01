import type { ArchiveSectionAPiType } from '../model/types';

export const MOCK_ARCHIVE_HISTORY: ArchiveSectionAPiType = {
  rec_id: 'rec-20260110',
  date: '2026.02.28',
  recording_url: 'https://example.com/recordings/rec-20260110.mp3',
  songs: [
    {
      id: 'song-1',
      title: '밤편지',
      artist: '아이유',
      album_cover: 'https://picsum.photos/seed/nightletter/200/200',
    },
    {
      id: 'song-2',
      title: '사건의 지평선',
      artist: '윤하',
      album_cover: 'https://picsum.photos/seed/eventhorizon/200/200',
    },
  ],
};
