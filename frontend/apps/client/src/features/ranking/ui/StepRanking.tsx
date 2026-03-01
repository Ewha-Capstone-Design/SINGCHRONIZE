import { Button } from '@singchronize/ui';
import SortableSongList from './SortableSongList';
import { toSongUi } from '@/entities/song/model/mapper';

import { MOCK_SONGS } from '@/entities/song/model/mock';

const StepRanking = ({ onNext }: { onNext: () => void }) => {
  // TODO: 쿼리 훅으로 교체
  const songs = MOCK_SONGS.map(toSongUi);

  return (
    <div className='mt-[4vh] mb-[8vh] flex flex-col justify-center h-full'>
      <div className='flex flex-col gap-[6vh] justify-between items-center w-[500] max-h-171.5 h-full'>
        <div className='flex items-center h-[92]'>
          <p className='typo-32b text-center whitespace-pre-line'>
            {'더 정확한 추천을 위해\n취향에 맞게 노래를 정렬해 주세요!'}
          </p>
        </div>

        <SortableSongList initialSongs={songs} />

        <Button variant='normal' onClick={onNext}>
          정렬 완료하기
        </Button>
      </div>
    </div>
  );
};

export default StepRanking;
