'use client';

type SelectionCounterProps = {
  minSelect: number;
  selectedCount: number;
};

const SelectionCounter = ({ minSelect, selectedCount }: SelectionCounterProps) => {
  return (
    <p className='typo-16r text-gray-400'>
      최소 {minSelect}명을 선택해주세요 ({selectedCount}/{minSelect})
    </p>
  );
};

export default SelectionCounter;
