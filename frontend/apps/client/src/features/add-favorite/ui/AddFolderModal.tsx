'use client';

import { useState, useEffect } from 'react';
import { InputField, Button } from '@singchronize/ui';
import { BaseModal } from '@/shared/components';
import { IcCheck, IcPlus } from '@/shared/assets/icons';
import { SongListItem } from '@/entities/song/ui';
import { SongUiType } from '@/entities/song/model/types';

import { MOCK_SONG_LIST } from '@/entities/song/model/mock';

type AddFolderModalProps = {
  onClose: () => void;
};

const AddFolderModal = ({ onClose }: AddFolderModalProps) => {
  const [folderTitle, setFolderTitle] = useState('');
  const [query, setQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [songs, setSongs] = useState<SongUiType[]>([]);

  useEffect(() => {
    // TODO: 곡 목록 fetch API 호출
    setSongs(MOCK_SONG_LIST);
  }, []);

  const filteredSongs = songs.filter(
    (song) =>
      song.title.toLowerCase().includes(query.toLowerCase()) ||
      song.artist.toLowerCase().includes(query.toLowerCase())
  );

  const toggle = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleSave = async () => {
    // TODO: 폴더 생성 + 곡 추가 API 호출
    onClose();
  };

  return (
    <BaseModal
      onClose={onClose}
      className='relative px-25 flex flex-col w-full max-w-198 max-h-178 h-[70vh] bg-bg rounded-20'
    >
      <div className='pt-14.5 flex flex-col gap-13.5 h-full'>
        <div className='flex flex-col gap-4'>
          <h2 className='typo-28b text-white'>찜 폴더 제목</h2>
          <InputField
            value={folderTitle}
            onChange={(e) => setFolderTitle(e.target.value)}
            placeholder='폴더 제목을 입력해주세요'
          />
        </div>

        <div className='flex flex-1 flex-col gap-4 overflow-y-hidden'>
          <h2 className='typo-28b text-white'>찜 폴더에 곡 추가</h2>
          <InputField
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='노래 제목이나 가수를 입력해주세요'
          />

          <div className='flex flex-col gap-4'>
            {filteredSongs.map((song) => {
              const isSelected = selectedIds.includes(String(song.id));
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
                      onClick={() => toggle(String(song.id))}
                      aria-label={isSelected ? '선택 해제' : '선택'}
                      className='flex items-center justify-center w-8 h-8'
                    >
                      {isSelected ? (
                        <IcCheck className='text-primary' />
                      ) : (
                        <IcPlus className='text-gray-400' />
                      )}
                    </button>
                  }
                />
              );
            })}
          </div>
        </div>

        <div className='pb-7 flex justify-center'>
          <Button variant='primary' onClick={handleSave} disabled={!folderTitle.trim()}>
            저장하기
          </Button>
        </div>
      </div>
    </BaseModal>
  );
};

export default AddFolderModal;
