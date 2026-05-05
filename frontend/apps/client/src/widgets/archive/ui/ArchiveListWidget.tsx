'use client';

import { useRef } from 'react';
import { useModal, useClickOutside } from '@/shared/hooks';
import { cn } from '@/shared/lib/cn';
import { DateSelectButton, DateSelectModal } from '@/features/date-select';
import { ArchiveSection } from '@/entities/archive/ui';

import { ArchiveSectionUiType } from '@/entities/archive';

type ArchiveListWidgetProps = {
  groups: ArchiveSectionUiType[];
  selectedDate: Date | null;
  onDateConfirm: (date: Date) => void;
  isDetail?: boolean;
};

const ArchiveListWidget = ({
  groups,
  selectedDate,
  onDateConfirm,
  isDetail = false,
}: ArchiveListWidgetProps) => {
  const { open: isOpen, openModal, closeModal } = useModal();
  const wrapperRef = useRef<HTMLDivElement>(null);

  useClickOutside(wrapperRef, closeModal, isOpen);

  return (
    <section className='px-8 py-6 flex flex-col gap-4'>
      <div className='flex justify-between items-center'>
        {!isDetail && <p className='typo-28b text-gray-200'>전체</p>}

        <div ref={wrapperRef} className='relative'>
          <DateSelectButton
            selected={selectedDate ?? undefined}
            isOpen={isOpen}
            onClick={isOpen ? closeModal : openModal}
          />

          {isOpen && (
            <div
              className={cn(
                'absolute top-full mt-3 z-50 w-max',
                isDetail ? 'left-0' : 'right-0',
              )}
            >
              <DateSelectModal
                selected={selectedDate ?? undefined}
                onClose={closeModal}
                onConfirm={(date) => {
                  onDateConfirm(date);
                  closeModal();
                }}
              />
            </div>
          )}
        </div>
      </div>

      <div className='flex flex-col gap-4'>
        {groups.map((group) => (
          <ArchiveSection key={group.id} group={group} />
        ))}
      </div>
    </section>
  );
};

export default ArchiveListWidget;
