'use client';

import { useMemo } from 'react';
import { Button, InputField } from '@singchronize/ui';
import { cn } from '@/shared/lib/cn';
import { IcCheck, IcPlus } from '@/shared/assets/icons';
import { SortableSongList } from '@/features/ranking';
import { SongListItem } from '@/entities/song/ui';
import type { SongUiType } from '@/entities/song/model/types';

import { MOCK_SONG_LIST } from '@/entities/song/model/mock';

const MIN_SETLIST = 3;
const MAX_SETLIST = 5;

type LiveStartStep2Props = {
  keyword: string;
  selectedSongs: SongUiType[];
  onKeywordChange: (value: string) => void;
  onToggleSong: (song: SongUiType) => void;
  onSetlistChange: (songs: SongUiType[]) => void;
  onStart: () => void;
};

export const LiveStartStep2 = ({
  keyword,
  selectedSongs,
  onKeywordChange,
  onToggleSong,
  onSetlistChange,
  onStart,
}: LiveStartStep2Props) => {
  const selectedIds = useMemo(
    () => new Set(selectedSongs.map((s) => s.id)),
    [selectedSongs]
  );

  const searchedSongs = useMemo(() => {
    const normalized = keyword.trim().toLowerCase();
    if (!normalized) return MOCK_SONG_LIST;
    return MOCK_SONG_LIST.filter(
      (song) =>
        song.title.toLowerCase().includes(normalized) ||
        song.artist.toLowerCase().includes(normalized)
    );
  }, [keyword]);

  const canStart = selectedSongs.length >= MIN_SETLIST;

  return (
    <div className='flex flex-col h-full'>
      <div className='flex flex-1 gap-25 min-h-0 overflow-hidden'>
        {/* 셋리스트 선택 */}
        <section className='flex flex-1 flex-col min-w-0'>
          <div className='mb-8'>
            <h2 className='typo-28b text-white'>셋리스트 선택</h2>
            <p className='typo-16r text-gray-200'>
              최소 3곡에서 최대 5곡까지 선택할 수 있어요
            </p>
          </div>

          <InputField
            value={keyword}
            onChange={(e) => onKeywordChange(e.target.value)}
            placeholder='라이브 버스킹에서 부를 노래를 검색하세요'
          />

          <div className='mt-7 flex flex-1 flex-col gap-4 overflow-y-auto min-h-0 scrollbar-hide'>
            {searchedSongs.length === 0 ? (
              <div className='py-20 text-center typo-16r text-gray-400'>
                검색 결과가 없습니다
              </div>
            ) : (
              searchedSongs.map((song) => {
                const selected = selectedIds.has(song.id);
                const disabled = !selected && selectedSongs.length >= MAX_SETLIST;

                return (
                  <SongListItem
                    key={song.id}
                    variant='list3'
                    thumbnail={song.thumbnail}
                    title={song.title}
                    artist={song.artist}
                    onClick={disabled ? undefined : () => onToggleSong(song)}
                    selected={selected}
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
                        aria-label={selected ? '선택 해제' : '곡 선택'}
                      >
                        {selected ? <IcCheck /> : <IcPlus />}
                      </button>
                    }
                  />
                );
              })
            )}
          </div>
        </section>

        {/* 셋리스트 순서 */}
        <section className='flex flex-1 flex-col min-w-0'>
          <div className='mb-8'>
            <h2 className='typo-28b text-white'>셋리스트 순서</h2>
            <p className='typo-16r text-gray-200'>
              곡을 드래그해 셋리스트 순서를 확정해주세요
            </p>
          </div>

          <div className='flex-1 overflow-y-auto min-h-0 scrollbar-hide'>
            <SortableSongList initialSongs={selectedSongs} onChange={onSetlistChange} />
          </div>
        </section>
      </div>

      <div className='py-7 flex justify-center shrink-0'>
        <Button variant={'accent'} onClick={onStart} disabled={!canStart}>
          라이브 버스킹 시작하기
        </Button>
      </div>
    </div>
  );
};
