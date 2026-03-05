'use client';

import { useMemo, useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { SelectChip } from '@/shared/components';
import { SongListItem } from '@/entities/song/ui';
import type { RecommendSongType, RecommendTab } from '../model/types';

type PanelKind = 'situation' | 'genre';

type RecommendPanelProps = {
  kind: PanelKind;
  title: string;
  description: string;
  tabs: RecommendTab<RecommendSongType>[];
  className?: string;
};

const RecommendPanel = ({
  kind,
  title,
  description,
  tabs,
  className,
}: RecommendPanelProps) => {
  const [selectedKey, setSelectedKey] = useState(() => tabs[0]?.key ?? '');

  const activeTab = useMemo(() => {
    const found = tabs.find((t) => t.key === selectedKey);
    return found ?? tabs[0] ?? null;
  }, [selectedKey, tabs]);

  if (!activeTab) return null;

  const isEmpty = activeTab.items.length === 0;
  const emptyMessage =
    kind === 'situation'
      ? '상황별 추천 곡이 아직 없어요'
      : '장르별 추천 곡이 아직 없어요';

  return (
    <section
      className={cn(
        'px-6 py-18.5 flex flex-col gap-11 h-full bg-bg border border-gray-600 rounded-20',
        className
      )}
    >
      <header className='text-center'>
        <h2 className='typo-24b text-white'>{title}</h2>
        <p className='mt-1 typo-16r text-gray-400'>{description}</p>
      </header>

      <div className='flex flex-1 flex-col gap-4'>
        <div className='flex gap-2'>
          {tabs.map((tab) => (
            <SelectChip
              key={tab.key}
              label={tab.label}
              selected={tab.key === activeTab.key}
              onClick={() => setSelectedKey(tab.key)}
            />
          ))}
        </div>

        <div className='flex-1'>
          {isEmpty ? (
            <div className='h-full w-full grid place-items-center'>
              <p className='typo-20r text-gray-500'>{emptyMessage}</p>
            </div>
          ) : (
            <ol className='flex flex-col gap-4'>
              {activeTab.items.map((item, index) => {
                const rank = item.rank ?? index + 1;

                return (
                  <li key={String(item.id)}>
                    <SongListItem
                      variant='list2'
                      rank={rank}
                      thumbnail={item.thumbnail}
                      title={item.title}
                      artist={item.artist}
                      tag={item.tag}
                      bpm={item.bpm}
                      musicKey={item.musicKey}
                      matchRate={item.matchRate}
                      isLiked={item.isLiked}
                    />
                  </li>
                );
              })}
            </ol>
          )}
        </div>
      </div>
    </section>
  );
};

export default RecommendPanel;
