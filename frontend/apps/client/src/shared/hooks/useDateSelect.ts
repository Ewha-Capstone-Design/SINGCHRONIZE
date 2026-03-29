import { useState } from 'react';

const useDateSelect = (initialDate?: Date) => {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(initialDate);

  const handleConfirm = (date: Date) => {
    setSelectedDate(date);
  };

  return { selectedDate, handleConfirm };
};

export default useDateSelect;
