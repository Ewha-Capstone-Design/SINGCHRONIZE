'use client';

import { cn } from '@/shared/lib/cn';
import { IcClose } from '@/shared/assets/icons';

type BaseModalProps = {
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
  overlayClassName?: string;
};

const BaseModal = ({
  onClose,
  children,
  className,
  overlayClassName,
}: BaseModalProps) => {
  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center bg-dim',
        overlayClassName
      )}
    >
      <div
        role='dialog'
        aria-modal='true'
        className={cn('relative', className)}
        onClick={(e) => e.stopPropagation()}
      >
        {children}

        <button className='absolute bottom-[-64] w-8 h-8' onClick={onClose}>
          <IcClose />
        </button>
      </div>
    </div>
  );
};

export default BaseModal;
