'use client';

import { useState } from 'react';
import { InputField, Button, TextAreaField } from '@singchronize/ui';
import { BackButton, BaseModal, SelectChip } from '@/shared/components';
import { IcPlus } from '@/shared/assets/icons';
import { SongListItem } from '@/entities/song/ui';
import type { SongUiType } from '@/entities/song/model/types';
import { HISTORY_TAG_OPTIONS, HistoryTagKeyType } from '@/entities/library/model/tags';
import type { HistoryItemUiType } from '@/entities/library';

import { useSearchMusic } from '@/entities/song';
import { useCreateHistory, useUpdateHistory } from '@/entities/library';

type AddHistoryModalProps = {
  onClose: () => void;
  initialHistory?: HistoryItemUiType;
};

type Step = 'search' | 'form';

const AddHistoryModal = ({ onClose, initialHistory }: AddHistoryModalProps) => {
  const isEditMode = Boolean(initialHistory);

  const [step, setStep] = useState<Step>(isEditMode ? 'form' : 'search');

  const [query, setQuery] = useState('');
  const [selectedSong, setSelectedSong] = useState<SongUiType | null>(
    initialHistory
      ? {
          id: initialHistory.historyId, // 수정 모드에서는 songId 대신 historyId 사용
          title: initialHistory.title,
          artist: initialHistory.artist,
          thumbnail: initialHistory.thumbnail,
        }
      : null,
  );
  const [memo, setMemo] = useState(initialHistory?.memo ?? '');
  const [selectedTags, setSelectedTags] = useState<Set<HistoryTagKeyType>>(
    () => new Set(initialHistory?.tags ?? []),
  );

  const { mutate: createHistory, isPending: isCreating } = useCreateHistory();
  const { mutate: updateHistory, isPending: isUpdating } = useUpdateHistory();
  const isPending = isCreating || isUpdating;

  const { data: searchedItems = [] } = useSearchMusic(query);

  const toggleTag = (key: HistoryTagKeyType) => {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleSelectSong = (song: SongUiType) => {
    setSelectedSong(song);
    setStep('form');
  };

  const handleBackToSearch = () => {
    setStep('search');
    setSelectedSong(null);
    setSelectedTags(new Set());
  };

  const handleSave = () => {
    if (!selectedSong) return;
    if (isEditMode && initialHistory) {
      updateHistory(
        {
          archiveId: initialHistory.historyId,
          body: { tags: Array.from(selectedTags), memo: memo || null },
        },
        { onSuccess: onClose },
      );
    } else {
      createHistory(
        {
          song_id: String(selectedSong.id),
          tags: Array.from(selectedTags),
          memo: memo || null,
        },
        { onSuccess: onClose },
      );
    }
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

          <div className='pb-4 flex flex-col gap-4 overflow-y-auto min-h-0 scrollbar-hide'>
            {searchedItems.map((song) => (
              <div key={song.id}>
                <SongListItem
                  variant='list3'
                  title={song.title}
                  artist={song.artist}
                  thumbnail={song.thumbnail ?? ''}
                  rightSlot={
                    <button
                      className='inline-flex items-center justify-center text-gray-300'
                      onClick={() => handleSelectSong(song)}
                    >
                      <IcPlus />
                    </button>
                  }
                />
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className='pt-21 flex flex-col h-full'>
          {!isEditMode && (
            <BackButton
              className='absolute top-10 left-10'
              onClick={handleBackToSearch}
            />
          )}

          <div className='flex flex-1 flex-col gap-7 overflow-y-scroll scrollbar-hide'>
            <div className='flex flex-col gap-3'>
              <h2 className='typo-24b text-gray-100'>선택한 노래</h2>
              {selectedSong && (
                <SongListItem
                  variant='list3'
                  title={selectedSong.title}
                  artist={selectedSong.artist}
                  thumbnail={selectedSong.thumbnail ?? ''}
                  rightSlot={<></>}
                />
              )}
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
              onClick={handleSave}
              disabled={!selectedSong || selectedTags.size === 0 || isPending}
            >
              {isEditMode ? '수정하기' : '저장하기'}
            </Button>
          </div>
        </div>
      )}
    </BaseModal>
  );
};

export default AddHistoryModal;
