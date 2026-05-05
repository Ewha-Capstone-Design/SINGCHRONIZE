'use client';

import { BaseModal } from '@/shared/components';
import { FavoriteFolderCover } from '@/entities/library/ui';
import { useFolders } from '@/entities/library';

type FolderSelectModalProps = {
  onSelect: (folderId: string) => void;
  onClose: () => void;
};

const FolderSelectModal = ({ onSelect, onClose }: FolderSelectModalProps) => {
  const { data: folders = [] } = useFolders();

  return (
    <BaseModal
      onClose={onClose}
      className='relative px-10 flex flex-col w-full max-w-140 bg-bg rounded-20'
    >
      <div className='pt-12 pb-8 flex flex-col gap-6'>
        <h2 className='typo-24b text-white px-4'>폴더 선택</h2>

        <div className='flex flex-col max-h-120 overflow-y-auto scrollbar-hide'>
          {folders.map((folder) => (
            <button
              key={folder.id}
              type='button'
              onClick={() => onSelect(folder.id)}
              className='flex items-center gap-6 px-4 py-4 rounded-10 hover:bg-gray-800 transition-colors text-left'
            >
              <FavoriteFolderCover images={folder.coverImages} className='size-14' />
              <div className='flex flex-col min-w-0'>
                <span className='typo-18m text-gray-100 truncate'>{folder.name}</span>
                <span className='typo-14r text-gray-400'>{folder.songCount}곡</span>
              </div>
            </button>
          ))}

          {folders.length === 0 && (
            <p className='px-4 py-6 typo-16r text-gray-500 text-center'>
              생성된 폴더가 없어요
            </p>
          )}
        </div>
      </div>
    </BaseModal>
  );
};

export default FolderSelectModal;
