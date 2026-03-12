'use client';

import { useState } from 'react';
import { Button } from '@singchronize/ui';
import { FavoriteFolderCard } from '@/entities/library/ui';
import type { FavoriteFolderUiType } from '@/entities/library/model/types';
import FavoriteFolderDetail from './FavoriteFolderDetail';

import {
  MOCK_FAVORITE_FOLDERS,
  MOCK_FAVORITE_SONGS,
} from '@/entities/library/model/mock';

const LibraryFavoriteList = () => {
  const [selectedFolder, setSelectedFolder] = useState<FavoriteFolderUiType | null>(null);

  const folders = MOCK_FAVORITE_FOLDERS;
  const songs = MOCK_FAVORITE_SONGS;

  if (selectedFolder) {
    return <FavoriteFolderDetail folder={selectedFolder} songs={songs} />;
  }

  return (
    <section className='flex flex-col'>
      <Button variant='normal' className='my-6 w-fit'>
        찜 폴더 추가하기
      </Button>

      <p className='typo-24b text-gray-100'>{folders.length}개</p>

      <ul className='mt-2 flex flex-col gap-2'>
        {folders.map((folder) => (
          <li key={folder.id}>
            <FavoriteFolderCard
              folder={folder}
              onClick={() => setSelectedFolder(folder)}
              onRenameClick={() => {}}
              onDeleteClick={() => {}}
            />
          </li>
        ))}
      </ul>
    </section>
  );
};

export default LibraryFavoriteList;
