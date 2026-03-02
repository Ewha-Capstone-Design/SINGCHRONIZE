'use client';

import { useMemo, useState } from 'react';
import { Button } from '@singchronize/ui';
import { SelectChip } from '@/shared/components';
import { cn } from '@/shared/lib/cn';
import { nextSelectedWithAll } from '@/shared/lib/selection';
import { HistoryItem } from '@/entities/library/ui';
import { HISTORY_FILTER_OPTIONS, HistoryTagType } from '@/entities/library/model/tags';
import { useModal } from '@/shared/hooks';
import { AddHistoryModal } from '@/features/add-history/ui';

import { MOCK_HISTORY_ITEMS } from '@/entities/library/model/mock';

type TagKey = 'all' | HistoryTagType;

const LibraryHistoryList = () => {
  const [selected, setSelected] = useState<Set<TagKey>>(() => new Set(['all']));
  const { open: isAddModalOpen, openModal, closeModal } = useModal(false);

  const toggleTag = (key: TagKey) => {
    setSelected((prev) => nextSelectedWithAll(prev, key));
  };

  // TODO: 추후에 API로 교체
  const items = useMemo(() => {
    if (selected.has('all')) return MOCK_HISTORY_ITEMS;

    const selectedTags = Array.from(selected) as HistoryTagType[];
    return MOCK_HISTORY_ITEMS.filter((item) =>
      selectedTags.some((tag) => (item.tags ?? []).includes(tag))
    );
  }, [selected]);

  const handleAddClick = () => {
    openModal();
  };

  return (
    <>
      <section className='mt-4 mb-6 flex flex-col gap-6'>
        <div className={cn('w-full flex items-center justify-between gap-6')}>
          <div className={cn('flex items-center gap-2 overflow-x-auto scrollbar-hide')}>
            {HISTORY_FILTER_OPTIONS.map((opt) => (
              <SelectChip
                key={opt.key}
                label={opt.label}
                selected={selected.has(opt.key)}
                onClick={() => toggleTag(opt.key)}
              />
            ))}
          </div>

          <Button variant='normal' onClick={handleAddClick}>
            보컬기록 추가하기
          </Button>
        </div>

        <div className='flex flex-col gap-6'>
          {items.map((item) => (
            <HistoryItem key={item.historyId} item={item} />
          ))}
        </div>
      </section>

      {isAddModalOpen && <AddHistoryModal onClose={closeModal} />}
    </>
  );
};

export default LibraryHistoryList;
