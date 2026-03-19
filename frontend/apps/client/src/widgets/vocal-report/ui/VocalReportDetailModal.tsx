'use client';

import { BaseModal } from '@/shared/components';

type VocalReportDetailModalProps = {
  title: string;
  chart: React.ReactNode;
  description: string;
  onClose: () => void;
};

const VocalReportDetailModal = ({
  title,
  chart,
  description,
  onClose,
}: VocalReportDetailModalProps) => {
  return (
    <BaseModal
      onClose={onClose}
      className='relative px-[12vw] lg:px-45 flex flex-col justify-center w-full max-w-198 max-h-178 h-[70vh] bg-bg rounded-20'
    >
      <div className='flex flex-col gap-6 overflow-y-auto'>
        <h2 className='typo-28b text-white text-center'>{title}</h2>
        <div className='w-full'>{chart}</div>
        <p className='typo-16r text-gray-300 text-center leading-relaxed whitespace-pre-line'>
          {description}
        </p>
      </div>
    </BaseModal>
  );
};

export default VocalReportDetailModal;
