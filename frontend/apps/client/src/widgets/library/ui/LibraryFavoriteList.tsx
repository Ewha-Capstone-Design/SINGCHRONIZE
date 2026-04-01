'use client';

import { useState } from 'react';
import { Button } from '@singchronize/ui';
import { useModal } from '@/shared/hooks';
import { AddFolderModal } from '@/features/add-favorite';
import { FavoriteFolderCard } from '@/entities/library/ui';
import type { FavoriteFolderUiType } from '@/entities/library/model/types';
import FavoriteFolderDetail from './FavoriteFolderDetail';

import { useFolders, useDeleteFolder } from '@/entities/library';

const LibraryFavoriteList = () => {
  const { open: isAddModalOpen, openModal, closeModal } = useModal(false);
  const [selectedFolder, setSelectedFolder] = useState<FavoriteFolderUiType | null>(null);

  const { data: folders = [] } = useFolders();
  const { mutate: deleteFolder } = useDeleteFolder();

  if (selectedFolder) {
    return (
      <FavoriteFolderDetail
        folder={selectedFolder}
        onBack={() => setSelectedFolder(null)}
      />
    );
  }

  return (
    <section className='flex flex-col'>
      <Button variant='normal' className='my-6 w-fit' onClick={openModal}>
        찜 폴더 추가하기
      </Button>

      <p className='typo-24b text-gray-100'>{folders.length}개</p>

      <ul className='mt-2 flex flex-col gap-2'>
        {folders.map((folder) => (
          <li key={folder.id}>
            <FavoriteFolderCard
              folder={folder}
              onClick={() => setSelectedFolder(folder)}
              onRenameClick={() => {}} // TODO: 폴더 이름 변경 기능 논의 필요
              onDeleteClick={() => deleteFolder(folder.id)}
            />
          </li>
        ))}
      </ul>

      {isAddModalOpen && <AddFolderModal onClose={closeModal} />}
    </section>
  );
};

export default LibraryFavoriteList;
