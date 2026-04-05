'use client';

import { useState } from 'react';
import { InputField, Button } from '@singchronize/ui';
import { BaseModal } from '@/shared/components';
import { IcCheck, IcPlus } from '@/shared/assets/icons';
import { SongListItem } from '@/entities/song/ui';
import type { SongUiType } from '@/entities/song/model/types';

import { useSearchMusic } from '@/entities/song';
import { useCreateFolder, useAddWishlistItem } from '@/entities/library';
import useDebounce from '@/shared/hooks/useDebounce';

type AddFolderModalProps = {
  onClose: () => void;
};

const AddFolderModal = ({ onClose }: AddFolderModalProps) => {
  const [folderTitle, setFolderTitle] = useState('');
  const [query, setQuery] = useState('');
  const [selectedSongs, setSelectedSongs] = useState<SongUiType[]>([]);

  const { mutate: createFolder, isPending: isCreatingFolder } = useCreateFolder();
  const { mutate: addWishlistItem } = useAddWishlistItem();

  const debouncedQuery = useDebounce(query);
  const { data: searchedItems = [] } = useSearchMusic(debouncedQuery);

  const toggle = (song: SongUiType) => {
    const id = String(song.id);
    setSelectedSongs((prev) =>
      prev.some((s) => String(s.id) === id)
        ? prev.filter((s) => String(s.id) !== id)
        : [...prev, song],
    );
  };

  const handleSave = async () => {
    if (!folderTitle.trim()) return;

    createFolder(
      { name: folderTitle },
      {
        onSuccess: (createdFolder) => {
          // 선택된 곡들을 폴더에 추가
          selectedSongs.forEach((song) => {
            addWishlistItem({
              song_data: {
                name: song.title,
                artist: song.artist,
                album_image: song.thumbnail ?? null,
                uri: String(song.id),
              } as unknown as Record<string, never>,
              folder_id: createdFolder.id,
            });
          });
          onClose();
        },
      },
    );
  };

  return (
    <BaseModal
      onClose={onClose}
      className='relative px-25 flex flex-col w-full max-w-198 max-h-178 h-[70vh] bg-bg rounded-20'
    >
      <div className='pt-14.5 flex flex-col gap-13.5 flex-1 overflow-y-auto scrollbar-hide'>
        <div className='flex flex-col gap-4'>
          <h2 className='typo-28b text-white'>찜 폴더 제목</h2>
          <InputField
            value={folderTitle}
            onChange={(e) => setFolderTitle(e.target.value)}
            placeholder='폴더 제목을 입력해주세요'
          />
        </div>

        <div className='flex flex-col gap-4'>
          <h2 className='typo-28b text-white'>찜 폴더에 곡 추가</h2>
          <InputField
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='노래 제목이나 가수를 입력해주세요'
          />

          <div className='flex flex-col gap-4'>
            {searchedItems.map((song) => {
              const isSelected = selectedSongs.some(
                (s) => String(s.id) === String(song.id),
              );
              return (
                <SongListItem
                  key={song.id}
                  variant='list3'
                  thumbnail={song.thumbnail}
                  title={song.title}
                  artist={song.artist}
                  selected={isSelected}
                  rightSlot={
                    <button
                      type='button'
                      onClick={() => toggle(song)}
                      aria-label={isSelected ? '선택 해제' : '선택'}
                      className='flex items-center justify-center w-8 h-8'
                    >
                      {isSelected ? (
                        <IcCheck className='text-brand' />
                      ) : (
                        <IcPlus className='text-gray-300' />
                      )}
                    </button>
                  }
                />
              );
            })}
          </div>
        </div>
      </div>

      <div className='py-7 flex justify-center shrink-0'>
        <Button
          variant='primary'
          onClick={handleSave}
          disabled={!folderTitle.trim() || isCreatingFolder}
        >
          저장하기
        </Button>
      </div>
    </BaseModal>
  );
};

export default AddFolderModal;
