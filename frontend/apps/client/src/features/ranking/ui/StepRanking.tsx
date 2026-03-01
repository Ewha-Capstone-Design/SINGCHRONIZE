import { Button } from '@singchronize/ui';
import SortableSongList from './SortableSongList';
import { SongType } from '@/entities/song/model/types';

// MOCK: 임시 데이터
const mockSongs: SongType[] = [
  { id: '1', title: 'Song A', artist: 'Artist A', album_cover: '' },
  { id: '2', title: 'Song B', artist: 'Artist B', album_cover: '' },
  { id: '3', title: 'Song C', artist: 'Artist C', album_cover: '' },
];

const StepRanking = ({ onNext }: { onNext: () => void }) => {
  return (
    <div className='mt-[4vh] mb-[8vh] flex flex-col justify-center h-full'>
      <div className='flex flex-col gap-[6vh] justify-between items-center w-[500] max-h-171.5 h-full'>
        <div className='flex items-center h-[92]'>
          <p className='typo-32b text-center whitespace-pre-line'>
            {'더 정확한 추천을 위해\n취향에 맞게 노래를 정렬해 주세요!'}
          </p>
        </div>

        <SortableSongList initialSongs={mockSongs} />

        <Button variant='normal' onClick={onNext}>
          정렬 완료하기
        </Button>
      </div>
    </div>
  );
};

export default StepRanking;
