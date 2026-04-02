'use client';

import { useMemo, useState } from 'react';
import { Button } from '@singchronize/ui';
import { SelectChip } from '@/shared/components';
import { cn } from '@/shared/lib/cn';
import { nextSelectedWithAll } from '@/shared/lib/selection';
import { useModal } from '@/shared/hooks';
import { AddHistoryModal } from '@/features/add-history';
import { HistoryItem } from '@/entities/library/ui';
import { HISTORY_FILTER_OPTIONS, HistoryTagType } from '@/entities/library/model/tags';

import { useHistory, useDeleteHistory } from '@/entities/library';

type TagKey = 'all' | HistoryTagType;

const LibraryHistoryList = () => {
  const [selected, setSelected] = useState<Set<TagKey>>(() => new Set(['all']));
  const { open: isAddModalOpen, openModal, closeModal } = useModal(false);

  const { data: allItems = [] } = useHistory();
  const { mutate: deleteHistory } = useDeleteHistory();

  const toggleTag = (key: TagKey) => {
    setSelected((prev) => nextSelectedWithAll(prev, key));
  };

  const items = useMemo(() => {
    if (selected.has('all')) return allItems;
    const selectedTags = Array.from(selected) as HistoryTagType[];
    return allItems.filter((item) =>
      selectedTags.some((tag) => (item.tags ?? []).includes(tag)),
    );
  }, [selected, allItems]);

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

          <Button variant='normal' onClick={openModal}>
            보컬기록 추가하기
          </Button>
        </div>

        <div className='flex flex-col gap-6'>
          {items.map((item) => (
            <HistoryItem
              key={item.historyId}
              item={item}
              onDeleteClick={(historyId) => deleteHistory(historyId)}
            />
          ))}
        </div>
      </section>

      {isAddModalOpen && <AddHistoryModal onClose={closeModal} />}
    </>
  );
};

export default LibraryHistoryList;
