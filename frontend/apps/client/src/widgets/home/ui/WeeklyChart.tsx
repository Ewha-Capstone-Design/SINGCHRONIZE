import { cn } from '@/shared/lib/cn';
import { SectionHeader } from '@/shared/components';
import { SongListItem } from '@/entities/song/ui';
import type { RankedSongType, SongUiType } from '@/entities/song/model/types';

type WeeklyChartProps = {
  items: RankedSongType[];
  onSongClick: (song: SongUiType) => void;
  className?: string;
};

const WeeklyChart = ({ items, onSongClick, className }: WeeklyChartProps) => {
  if (!items.length) return null;

  return (
    <section className={cn('flex flex-col gap-4', className)}>
      <SectionHeader
        title='이번 주 차트'
        description='가장 많이 찜한 노래를 알려줄게요!'
      />

      <div className='flex flex-col gap-3'>
        {items.map((song, index) => (
          <SongListItem
            key={song.id}
            variant='list4'
            rank={index + 1}
            title={song.title}
            artist={song.artist}
            thumbnail={song.thumbnail}
            likeCount={song.likeCount}
            isLiked={song.isLiked}
            onClick={() => onSongClick(song)}
          />
        ))}
      </div>
    </section>
  );
};

export default WeeklyChart;
