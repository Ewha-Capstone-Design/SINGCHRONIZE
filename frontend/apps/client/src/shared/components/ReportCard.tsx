import type { ReactNode } from 'react';
import { cn } from '@/shared/lib/cn';
import { IcArrowRight } from '../assets/icons';

type ReportCardProps = {
  title: string;
  description?: string;
  onClick?: () => void;
  hideArrow?: boolean;
  className?: string;
  children: ReactNode;
};

const ReportCard = ({
  title,
  description,
  onClick,
  hideArrow = false,
  className,
  children,
}: ReportCardProps) => {
  return (
    <section
      className={cn(
        'p-6 flex flex-col h-full md:h-90 bg-bg border border-gray-600 rounded-20',
        className
      )}
    >
      <header className='flex items-start justify-between gap-4'>
        <div className='flex flex-col gap-0.5 min-w-0'>
          <h3 className='typo-20sb text-white'>{title}</h3>
          {description ? <p className='typo-14r text-gray-400'>{description}</p> : null}
        </div>

        {!hideArrow ? (
          <button type='button' className='shrink-0' onClick={onClick}>
            <IcArrowRight />
          </button>
        ) : null}
      </header>

      <div className='flex-1'>{children}</div>
    </section>
  );
};

export default ReportCard;
