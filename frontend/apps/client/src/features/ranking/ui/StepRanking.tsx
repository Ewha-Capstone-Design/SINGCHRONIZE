import { useState } from 'react';
import { Button } from '@singchronize/ui';
import SortableSongList from './SortableSongList';
import { openYoutubeSearch } from '@/shared/lib/openYoutubeSearch';
import type { SongUiType } from '@/entities/song/model/types';

type StepRankingProps = {
  songs: SongUiType[];
  onNext: (sortedSongIds: string[]) => void;
};

const StepRanking = ({ songs, onNext }: StepRankingProps) => {
  const [sortedSongs, setSortedSongs] = useState<SongUiType[]>(songs);

  return (
    <div className='mt-[4vh] mb-[8vh] flex flex-col justify-center h-full'>
      <div className='flex flex-col gap-[6vh] justify-between items-center w-[500] max-h-171.5 h-full'>
        <div className='flex items-center h-[92]'>
          <p className='typo-32b text-center whitespace-pre-line'>
            {'더 정확한 추천을 위해\n취향에 맞게 노래를 정렬해 주세요!'}
          </p>
        </div>

        <SortableSongList
          initialSongs={sortedSongs}
          variant='play'
          onChange={setSortedSongs}
          onPlay={(song) => openYoutubeSearch(song.artist, song.title)}
        />

        <Button variant='normal' onClick={() => onNext(sortedSongs.map((s) => String(s.id)))}>
          정렬 완료하기
        </Button>
      </div>
    </div>
  );
};

export default StepRanking;
