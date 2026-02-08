type SegmentedProgressProps = {
  total?: number; // 기본 4
  filled: number; // 채워질 개수
};

const SegmentedProgress = ({ total = 4, filled }: SegmentedProgressProps) => {
  return (
    <div className='flex items-center gap-[13]'>
      {Array.from({ length: total }).map((_, i) => {
        const isFilled = i < filled;

        return (
          <div
            key={i}
            className='relative h-1 flex-1 overflow-hidden rounded-[50px] bg-gray-800'
          >
            <div
              className='
                  absolute left-0 top-0 h-full bg-gray-300
                  transition-[width] duration-700 ease-out
                '
              style={{ width: isFilled ? '100%' : '0%' }}
            />
          </div>
        );
      })}
    </div>
  );
};

export default SegmentedProgress;
