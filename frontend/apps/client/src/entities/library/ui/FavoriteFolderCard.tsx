'use client';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@singchronize/ui';
import { IcMore } from '@/shared/assets/icons';
import { cn } from '@/shared/lib/cn';
import type { FavoriteFolderUiType } from '../model/types';
import FavoriteFolderCover from './FavoriteFolderCover';

interface FavoriteFolderCardProps {
  folder: FavoriteFolderUiType;
  onClick?: () => void;
  onRenameClick?: (folderId: string) => void;
  onDeleteClick?: (folderId: string) => void;
}

const FavoriteFolderCard = ({
  folder,
  onClick,
  onRenameClick,
  onDeleteClick,
}: FavoriteFolderCardProps) => {
  return (
    <article
      onClick={onClick}
      className={cn(
        'px-10 py-7 flex flex-1 items-center justify-between gap-10',
        'rounded-10 border-2 border-gray-800 bg-gray-900 cursor-pointer'
      )}
    >
      <div className='flex flex-1 items-center gap-10'>
        <FavoriteFolderCover images={folder.coverImages} />

        <div className='flex flex-col gap-2 min-w-0'>
          <h3 className='truncate typo-24b text-gray-100'>{folder.name}</h3>
          <div className='flex flex-col gap-1'>
            <p className='typo-20r text-gray-400'>{folder.updatedAt}</p>
            <p className='typo-20r text-gray-400'>{folder.songCount}곡</p>
          </div>
        </div>
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type='button'
            aria-label='폴더 메뉴 열기'
            className='shrink-0'
            onClick={(e) => {
              e.stopPropagation();
            }}
          >
            <IcMore className='rotate-90' />
          </button>
        </DropdownMenuTrigger>

        <DropdownMenuContent
          side='bottom'
          align='end'
          sideOffset={12}
          alignOffset={-28}
          onClick={(e) => e.stopPropagation()}
        >
          <DropdownMenuItem
            onClick={(e) => {
              e.stopPropagation();
              onRenameClick?.(folder.id);
            }}
          >
            폴더 이름 변경하기
          </DropdownMenuItem>

          <DropdownMenuItem
            onClick={(e) => {
              e.stopPropagation();
              onDeleteClick?.(folder.id);
            }}
          >
            폴더 삭제하기
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </article>
  );
};

export default FavoriteFolderCard;
