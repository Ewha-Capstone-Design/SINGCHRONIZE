import { Button } from '@singchronize/ui';
import SortableSongList from './SortableSongList';
import { SongType } from '@/entities/song/model/types';

// 임시 데이터
const mockSongs: SongType[] = [
  { id: '1', title: 'Song A', artist: 'Artist A', album_cover: '' },
  { id: '2', title: 'Song B', artist: 'Artist B', album_cover: '' },
  { id: '3', title: 'Song C', artist: 'Artist C', album_cover: '' },
];

const StepRanking = ({ onNext }: { onNext: () => void }) => {
  return (
    <div className='my-[8vh] mx-auto flex flex-col gap-[6vh] items-center justify-center w-[500]'>
      <p className='text-32b text-center whitespace-pre-line'>
        {'더 정확한 추천을 위해\n취향에 맞게 노래를 정렬해 주세요!'}
      </p>

      <SortableSongList initialSongs={mockSongs} />

      <Button variant='normal' onClick={onNext}>
        정렬 완료하기
      </Button>
    </div>
  );
};

export default StepRanking;
