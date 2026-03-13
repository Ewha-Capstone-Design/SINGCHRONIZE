'use client';

import { useMemo, useState } from 'react';
import { InputField, Button } from '@singchronize/ui';
import { BaseModal } from '@/shared/components';
import { SongListItem } from '@/entities/song/ui';

import { MOCK_SONG_LIST } from '@/entities/song/model/mock';

type BlockedSongsModalProps = {
  onClose: () => void;
};

const BlockedSongsModal = ({ onClose }: BlockedSongsModalProps) => {
  const [query, setQuery] = useState('');

  // TODO: 실제 차단 목록 API로 교체
  const blockedSongs = MOCK_SONG_LIST;

  const filteredSongs = useMemo(() => {
    const q = query.trim();
    if (!q) return blockedSongs;
    return blockedSongs.filter((song) => `${song.title} ${song.artist}`.includes(q));
  }, [query, blockedSongs]);

  return (
    <BaseModal
      onClose={onClose}
      className='relative px-10 flex flex-col w-full max-w-226 max-h-178 h-[70vh] bg-bg rounded-20'
    >
      <div className='pt-14.5 flex flex-col gap-7 h-full'>
        <h2 className='typo-28b text-white'>차단한 곡 관리하기</h2>

        <InputField
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder='노래 제목이나 가수를 입력해주세요'
        />

        <div className='flex flex-1 flex-col gap-3 overflow-y-hidden'>
          <h3 className='typo-24b text-gray-200'>차단한 곡</h3>

          {filteredSongs.length === 0 ? (
            <div className='flex flex-1 items-center justify-center'>
              <p className='typo-16r text-gray-400'>차단한 곡이 없어요</p>
            </div>
          ) : (
            <div className='pb-7 flex flex-col gap-4 overflow-y-auto scrollbar-hide'>
              {filteredSongs.map((song) => (
                <SongListItem
                  key={song.id}
                  variant='list3'
                  thumbnail={song.thumbnail}
                  title={song.title}
                  artist={song.artist}
                  rightSlot={
                    <Button
                      variant='normal'
                      size='medium'
                      onClick={() => {
                        /* TODO: 차단 해제 API */
                      }}
                    >
                      차단 해제하기
                    </Button>
                  }
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </BaseModal>
  );
};

export default BlockedSongsModal;
