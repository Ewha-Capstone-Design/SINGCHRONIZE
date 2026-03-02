'use client';

import { useMemo, useState } from 'react';
import { BaseModal, SelectChip } from '@/shared/components';
import { InputField, Button, TextAreaField } from '@singchronize/ui';
import { SongListItem } from '@/entities/song/ui';
import { IcBack, IcPlus } from '@/shared/assets/icons';
import { HISTORY_TAG_OPTIONS, HistoryTagKeyType } from '@/entities/library/model/tags';

type AddHistoryModalProps = {
  onClose: () => void;
};

type Step = 'search' | 'form';

type SelectedSong = {
  id: string | number;
  title: string;
  artist: string;
  thumbnail?: string;
};

const AddHistoryModal = ({ onClose }: AddHistoryModalProps) => {
  const [step, setStep] = useState<Step>('search');
  const [query, setQuery] = useState('');
  const [selectedSong, setSelectedSong] = useState<SelectedSong | null>(null);

  const [memo, setMemo] = useState('');
  const [selectedTags, setSelectedTags] = useState<Set<HistoryTagKeyType>>(
    () => new Set()
  );

  const toggleTag = (key: HistoryTagKeyType) => {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // TODO: 검색 결과/아카이브를 API로 교체
  const archiveItems = useMemo<SelectedSong[]>(
    () => [
      { id: 1, title: '밤편지', artist: '아이유', thumbnail: '' },
      { id: 2, title: 'The Action', artist: 'BOYNEXTDOOR', thumbnail: '' },
    ],
    []
  );

  const handleSelectSong = (song: SelectedSong) => {
    setSelectedSong(song);
    setStep('form');
  };

  const handleBackToSearch = () => {
    setStep('search');
    setSelectedSong(null);
    setSelectedTags(new Set());
  };

  return (
    <BaseModal
      onClose={onClose}
      className='relative px-25 flex flex-col w-full max-w-226 max-h-178 h-[70vh] bg-bg rounded-20'
    >
      {step === 'search' ? (
        <div className='pt-14.5 flex flex-col gap-7 h-full'>
          <div className='flex flex-col gap-7'>
            <h2 className='typo-32b text-white'>보컬기록 추가하기</h2>
            <InputField
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='노래 제목이나 가수를 입력해주세요'
            />
          </div>

          <div className='flex flex-col gap-3 min-h-0'>
            <p className='typo-20b text-white'>아카이브</p>

            <div className='flex flex-col gap-4 overflow-y-auto min-h-0'>
              {archiveItems.map((song) => (
                <button
                  key={song.id}
                  type='button'
                  className='text-left'
                  onClick={() => handleSelectSong(song)}
                >
                  <SongListItem
                    variant='list3'
                    title={song.title}
                    artist={song.artist}
                    thumbnail={song.thumbnail ?? ''}
                    rightSlot={
                      <span className='inline-flex items-center justify-center'>
                        <IcPlus />
                      </span>
                    }
                  />
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className='pt-21 flex flex-col h-full'>
          <button
            type='button'
            className='absolute top-10 left-10'
            onClick={handleBackToSearch}
          >
            <IcBack />
          </button>

          <div className='flex flex-1 flex-col gap-7 overflow-y-scroll scrollbar-hide'>
            <div className='flex flex-col gap-3'>
              <h2 className='typo-24b text-gray-100'>선택한 노래</h2>
              {selectedSong ? (
                <SongListItem
                  variant='list3'
                  title={selectedSong.title}
                  artist={selectedSong.artist}
                  thumbnail={selectedSong.thumbnail ?? ''}
                  rightSlot={<></>}
                />
              ) : null}
            </div>

            <div className='flex flex-col gap-3'>
              <div>
                <h2 className='typo-24b text-gray-200'>평가하기</h2>
                <p className='typo-14r text-gray-500'>여러 개 선택할 수 있어요!</p>
              </div>

              <div className='flex flex-wrap items-center gap-x-2 gap-y-3 w-105'>
                {HISTORY_TAG_OPTIONS.map((opt) => (
                  <SelectChip
                    key={opt.key}
                    label={opt.label}
                    selected={selectedTags.has(opt.key)}
                    onClick={() => toggleTag(opt.key)}
                  />
                ))}
              </div>
            </div>

            <div className='flex flex-col gap-3'>
              <div className='flex gap-1'>
                <h2 className='typo-24b text-gray-200'>메모하기</h2>
                <h2 className='typo-24b text-gray-400'>(선택)</h2>
              </div>
              <TextAreaField
                value={memo}
                onChange={(e) => setMemo(e.target.value)}
                placeholder='부르면서 느낀 점을 적어보세요'
              />
            </div>
          </div>

          <div className='py-7 mx-auto'>
            <Button
              variant='normal'
              onClick={() => {
                // TODO: 저장 API 연결
                onClose();
              }}
              disabled={!selectedSong || selectedTags.size === 0}
            >
              저장하기
            </Button>
          </div>
        </div>
      )}
    </BaseModal>
  );
};

export default AddHistoryModal;
