'use client';

import { ArchiveSection } from '@/entities/archive/ui';
import { ArchiveSectionUiType } from '@/entities/archive/model/types';

type ArchiveListWidgetProps = {
  groups: ArchiveSectionUiType[];
  isDetail?: boolean;
};

const ArchiveListWidget = ({ groups, isDetail = false }: ArchiveListWidgetProps) => {
  return (
    <section className='px-8 py-6 flex flex-col gap-4'>
      {!isDetail && <p className='typo-28b text-gray-200'>전체</p>}

      <div className='flex flex-col gap-4'>
        {groups.map((group) => (
          <ArchiveSection key={group.id} group={group} />
        ))}
      </div>
    </section>
  );
};

export default ArchiveListWidget;
