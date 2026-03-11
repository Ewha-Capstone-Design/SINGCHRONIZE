'use client';

import { Button } from '@singchronize/ui';
import { SongListItem } from '@/entities/song/ui';
import type {
  FavoriteFolderUiType,
  FavoriteSongUiType,
} from '@/entities/library/model/types';
import { cn } from '@/shared/lib/cn';

interface FavoriteFolderDetailProps {
  folder: FavoriteFolderUiType;
  songs: FavoriteSongUiType[];
}

const FavoriteFolderDetail = ({ folder, songs }: FavoriteFolderDetailProps) => {
  return (
    <div className='flex flex-col'>
      <Button variant='normal' className='my-6 w-fit'>
        찜 추가하기
      </Button>

      <h2 className='typo-24b text-gray-100'>{folder.name}</h2>

      <ul
        className={cn(
          'mt-2 px-10 py-7 flex flex-col gap-4',
          'rounded-10 border-2 border-gray-800 bg-gray-900'
        )}
      >
        {songs.map((song) => (
          <li key={song.itemId}>
            <SongListItem
              variant='list3'
              thumbnail={song.thumbnail}
              title={song.title}
              artist={song.artist}
              isLiked={song.isLiked}
              onLikeClick={() => {}}
              onMoreClick={() => {}}
            />
          </li>
        ))}
      </ul>
    </div>
  );
};

export default FavoriteFolderDetail;
