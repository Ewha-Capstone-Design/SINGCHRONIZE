import type { ReactNode } from 'react';
import { cn } from '@/shared/lib/cn';
import { IcArrowRight } from '../assets/icons';

type InsightCardProps = {
  title: string;
  description?: string;
  onClick?: () => void;
  right?: ReactNode;
  className?: string;
  children: ReactNode;
};

const InsightCard = ({
  title,
  description,
  onClick,
  right,
  className,
  children,
}: InsightCardProps) => {
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

        <button className='shrink-0' onClick={onClick}>
          {right ?? <IcArrowRight />}
        </button>
      </header>

      <div className='flex-1'>{children}</div>
    </section>
  );
};

export default InsightCard;
