import { toSongUi } from '@/entities/song/model/mapper';
import type { ArchiveSectionAPiType, ArchiveSectionUiType } from './types';
import { getArchiveHistoryTitle } from './utils';

export const toArchiveSectionUi = (
  raw: ArchiveSectionAPiType
): ArchiveSectionUiType => ({
  id: raw.rec_id,
  title: getArchiveHistoryTitle(raw.date),
  recordingUrl: raw.recording_url,
  songs: raw.songs.map(toSongUi),
});
