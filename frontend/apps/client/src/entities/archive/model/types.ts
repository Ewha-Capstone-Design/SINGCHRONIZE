import type { SongApiType, SongUiType } from '@/entities/song/model/types';

export type ArchiveSectionAPiType = {
  rec_id: string;
  date: string;
  recording_url?: string;
  songs: SongApiType[];
};

export type ArchiveSectionUiType = {
  id: string;
  title: string;
  recordingUrl?: string;
  songs: SongUiType[];
};
