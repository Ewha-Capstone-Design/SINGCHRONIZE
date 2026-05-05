'use client';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@singchronize/ui';
import { IcMore } from '@/shared/assets/icons';
import { useBlockSong, useBlockSinger } from '@/entities/user';

type SongBlockMenuProps = {
  songId: string;
  singerId?: number;
};

const SongBlockMenu = ({ songId, singerId }: SongBlockMenuProps) => {
  const { mutate: blockSong } = useBlockSong();
  const { mutate: blockSinger } = useBlockSinger();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type='button'
          aria-label='더보기'
          className='inline-flex items-center justify-center'
        >
          <IcMore />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align='end' onClick={(e) => e.stopPropagation()}>
        <DropdownMenuItem onSelect={() => blockSong({ song_id: songId })}>
          곡 차단하기
        </DropdownMenuItem>
        {singerId !== undefined && (
          <DropdownMenuItem onSelect={() => blockSinger({ singer_id: singerId })}>
            가수 차단하기
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default SongBlockMenu;
