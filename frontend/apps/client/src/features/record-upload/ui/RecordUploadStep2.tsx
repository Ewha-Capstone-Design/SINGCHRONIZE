'use client';

import { useMemo, useRef } from 'react';
import { Button, InputField } from '@singchronize/ui';
import { cn } from '@/shared/lib/cn';
import { useModal, useClickOutside } from '@/shared/hooks';
import { IcCheck, IcPlus } from '@/shared/assets/icons';
import { DateSelectButton, DateSelectModal } from '@/features/date-select';
import { SongListItem } from '@/entities/song/ui';
import type { SongUiType } from '@/entities/song/model/types';

import { MOCK_SONG_LIST } from '@/entities/song/model/mock';

const MAX_SETLIST = 5;

type RecordUploadStep2Props = {
  keyword: string;
  selectedSongs: SongUiType[];
  endDate?: Date;
  onKeywordChange: (value: string) => void;
  onToggleSong: (song: SongUiType) => void;
  onSetlistChange: (songs: SongUiType[]) => void;
  onEndDateChange: (date: Date) => void;
  onSubmit: () => void;
};

export const RecordUploadStep2 = ({
  keyword,
  selectedSongs,
  endDate,
  onKeywordChange,
  onToggleSong,
  onSetlistChange,
  onEndDateChange,
  onSubmit,
}: RecordUploadStep2Props) => {
  const selectedIds = useMemo(
    () => new Set(selectedSongs.map((s) => s.id)),
    [selectedSongs]
  );

  const { open: isDateOpen, openModal: openDate, closeModal: closeDate } = useModal();
  const dateWrapperRef = useRef<HTMLDivElement>(null);
  useClickOutside(dateWrapperRef, closeDate);

  const searchedSongs = useMemo(() => {
    const normalized = keyword.trim().toLowerCase();
    if (!normalized) return MOCK_SONG_LIST;
    return MOCK_SONG_LIST.filter(
      (song) =>
        song.title.toLowerCase().includes(normalized) ||
        song.artist.toLowerCase().includes(normalized)
    );
  }, [keyword]);

  const canSubmit = selectedSongs.length >= 1;

  return (
    <div className='flex flex-col h-full'>
      <div className='flex flex-1 gap-25 min-h-0 overflow-hidden'>
        {/* 노래 선택 */}
        <section className='flex flex-1 flex-col min-w-0'>
          <div className='mb-8'>
            <h2 className='typo-28b text-white'>노래 선택</h2>
            <p className='typo-16r text-gray-200'>1곡 선택할 수 있어요</p>
          </div>

          <InputField
            value={keyword}
            onChange={(e) => onKeywordChange(e.target.value)}
            placeholder='라이브 버스킹에서 부를 노래를 검색하세요'
          />

          <div className='mt-7 flex flex-1 flex-col gap-4 overflow-y-auto min-h-0 scrollbar-hide'>
            {searchedSongs.map((song) => {
              const selected = selectedIds.has(song.id);
              const disabled = !selected && selectedSongs.length >= MAX_SETLIST;

              return (
                <SongListItem
                  key={song.id}
                  variant='list3'
                  thumbnail={song.thumbnail}
                  title={song.title}
                  artist={song.artist}
                  selected={selected}
                  onClick={disabled ? undefined : () => onToggleSong(song)}
                  rightSlot={
                    <button
                      type='button'
                      disabled={disabled}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (!disabled) onToggleSong(song);
                      }}
                      className={cn(
                        'text-white',
                        disabled && 'cursor-not-allowed opacity-40'
                      )}
                    >
                      {selected ? <IcCheck /> : <IcPlus />}
                    </button>
                  }
                />
              );
            })}
          </div>
        </section>

        {/* 녹음 파일 업로드 + 투표 종료 시점 */}
        <section className='flex flex-1 flex-col min-w-0 gap-21'>
          <div className='flex flex-col gap-7'>
            <div>
              <h2 className='typo-28b text-white'>녹음 파일 업로드</h2>
              <p className='typo-16r text-gray-200'>음성 녹음 파일만 가능해요</p>
            </div>
            <Button variant='normal' className='w-fit'>
              파일 선택하기
            </Button>
          </div>

          <div className='flex flex-col gap-7'>
            <div>
              <h2 className='typo-28b text-white'>투표 종료 시점</h2>
              <p className='typo-16r text-gray-200'>
                투표를 언제까지 받을지 날짜를 설정해주세요
              </p>
            </div>

            <div ref={dateWrapperRef} className='relative w-fit'>
              <DateSelectButton
                selected={endDate}
                isOpen={isDateOpen}
                onClick={isDateOpen ? closeDate : openDate}
              />
              {isDateOpen && (
                <div className='absolute left-0 top-full mt-2 z-100 w-max'>
                  <DateSelectModal
                    selected={endDate}
                    onClose={closeDate}
                    onConfirm={(date) => {
                      onEndDateChange(date);
                      closeDate();
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        </section>
      </div>

      <div className='py-7 flex justify-center shrink-0'>
        <Button variant='accent' disabled={!canSubmit} onClick={onSubmit}>
          녹음 버스킹 업로드하기
        </Button>
      </div>
    </div>
  );
};
