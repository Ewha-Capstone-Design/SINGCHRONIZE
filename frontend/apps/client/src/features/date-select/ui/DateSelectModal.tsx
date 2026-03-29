'use client';

import { useState } from 'react';
import { Button } from '@singchronize/ui';
import { Calendar } from '@/shared/components';

type DateSelectModalProps = {
  selected?: Date;
  onClose: () => void;
  onConfirm: (date: Date) => void;
};

const DateSelectModal = ({ selected, onClose, onConfirm }: DateSelectModalProps) => {
  const [date, setDate] = useState<Date | undefined>(selected);

  const handleConfirm = () => {
    if (!date) return;
    onConfirm(date);
    onClose();
  };

  return (
    <div className='px-4 py-5 flex flex-col gap-1 w-fit bg-gray-800 rounded-10'>
      <Calendar selected={date} onSelect={setDate} />

      <div className='flex justify-end'>
        <Button variant='normal' size={'medium'} disabled={!date} onClick={handleConfirm}>
          선택 완료
        </Button>
      </div>
    </div>
  );
};

export default DateSelectModal;
