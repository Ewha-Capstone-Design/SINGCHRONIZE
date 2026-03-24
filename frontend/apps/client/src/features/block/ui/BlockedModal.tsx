'use client';

import { InputField, Button } from '@singchronize/ui';
import { BaseModal } from '@/shared/components';
import { SongListItem } from '@/entities/song/ui';
import { useBlockedItems } from '../model/useBlockedItems';

type BlockedModalProps = {
  type: 'song' | 'artist';
  onClose: () => void;
};

const CONFIG = {
  song: {
    title: '차단한 곡 관리하기',
    listTitle: '차단한 곡',
    placeholder: '노래 제목이나 가수를 입력해주세요',
    emptyText: '차단한 곡이 없어요',
  },
  artist: {
    title: '차단한 가수 관리하기',
    listTitle: '차단한 가수',
    placeholder: '가수를 입력해주세요',
    emptyText: '차단한 가수가 없어요',
  },
} as const;

const BlockedModal = ({ type, onClose }: BlockedModalProps) => {
  const config = CONFIG[type];
  const { query, setQuery, normalizedItems } = useBlockedItems(type);

  return (
    <BaseModal
      onClose={onClose}
      className='relative px-25 flex flex-col w-full max-w-226 max-h-178 h-[70vh] bg-bg rounded-20'
    >
      <div className='pt-14.5 flex flex-col gap-7 h-full'>
        <h2 className='typo-28b text-white'>{config.title}</h2>

        <InputField
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={config.placeholder}
        />

        <div className='flex flex-1 flex-col gap-3 overflow-y-hidden'>
          <h3 className='typo-24b text-gray-200'>{config.listTitle}</h3>

          {normalizedItems.length === 0 ? (
            <div className='flex flex-1 items-center justify-center'>
              <p className='typo-16r text-gray-400'>{config.emptyText}</p>
            </div>
          ) : (
            <div className='pb-7 flex flex-col gap-4 overflow-y-auto scrollbar-hide'>
              {normalizedItems.map((item) => (
                <SongListItem
                  key={item.id}
                  variant='list3'
                  thumbnail={item.thumbnail}
                  title={item.title}
                  artist={item.artist}
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

export default BlockedModal;
