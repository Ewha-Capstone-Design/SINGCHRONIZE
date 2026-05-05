'use client';

import { useRef, useState } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  InputField,
} from '@singchronize/ui';
import { IcMore } from '@/shared/assets/icons';
import { cn } from '@/shared/lib/cn';
import type { FavoriteFolderUiType } from '../model/types';
import FavoriteFolderCover from './FavoriteFolderCover';

interface FavoriteFolderCardProps {
  folder: FavoriteFolderUiType;
  onClick?: () => void;
  onRenameSubmit?: (folderId: string, newName: string) => void;
  onDeleteClick?: (folderId: string) => void;
}

const FavoriteFolderCard = ({
  folder,
  onClick,
  onRenameSubmit,
  onDeleteClick,
}: FavoriteFolderCardProps) => {
  const [isRenaming, setIsRenaming] = useState(false);
  const [nameInput, setNameInput] = useState(folder.name);
  const inputRef = useRef<HTMLInputElement>(null);

  const startRenaming = () => {
    setNameInput(folder.name);
    setIsRenaming(true);
    setTimeout(() => inputRef.current?.select(), 0);
  };

  const submitRename = () => {
    const trimmed = nameInput.trim();
    if (trimmed && trimmed !== folder.name) {
      onRenameSubmit?.(folder.id, trimmed);
    }
    setIsRenaming(false);
  };

  return (
    <article
      onClick={isRenaming ? undefined : onClick}
      className={cn(
        'px-10 py-7 flex flex-1 items-center justify-between gap-10',
        'rounded-10 border-2 border-gray-800 bg-gray-900 cursor-pointer',
        isRenaming && 'cursor-default',
      )}
    >
      <div className='flex flex-1 items-center gap-10 min-w-0'>
        <FavoriteFolderCover images={folder.coverImages} />

        <div className='flex flex-col gap-2 min-w-0 flex-1'>
          {isRenaming ? (
            <InputField
              ref={inputRef}
              value={nameInput}
              onChange={(e) => setNameInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') submitRename();
                if (e.key === 'Escape') setIsRenaming(false);
              }}
              onBlur={submitRename}
              onClick={(e) => e.stopPropagation()}
              className='typo-24b'
            />
          ) : (
            <h3 className='truncate typo-24b text-gray-100'>{folder.name}</h3>
          )}
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
            onClick={(e) => e.stopPropagation()}
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
          onCloseAutoFocus={(e) => {
            if (isRenaming) {
              e.preventDefault();
              inputRef.current?.focus();
            }
          }}
        >
          <DropdownMenuItem
            onClick={(e) => {
              e.stopPropagation();
              startRenaming();
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
