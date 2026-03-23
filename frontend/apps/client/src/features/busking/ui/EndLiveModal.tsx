'use client';

import { Button } from '@singchronize/ui';
import { cn } from '@/shared/lib/cn';
import { BaseModal } from '@/shared/components';

type EndLiveModalProps = {
  onClose: () => void;
  onConfirm: () => void;
  thumbnail?: string;
};

const EndLiveModal = ({ onClose, onConfirm, thumbnail }: EndLiveModalProps) => {
  return (
    <BaseModal
      onClose={onClose}
      className={cn(
        'relative p-10 flex flex-col justify-center items-center w-full max-w-198 max-h-178 h-[70vh] rounded-20',
        'bg-bg bg-[radial-gradient(50%_50%_at_50%_50%,rgba(240,48,58,0.17)_0%,rgba(22,22,22,0.17)_100%)]',
        'bg-size-[130%_280%] bg-position-[50%_0%]'
      )}
    >
      <div className='flex flex-col gap-9 w-103'>
        {/* 제목 */}
        <h2 className='typo-32b text-white text-center'>라이브 버스킹을 종료할까요?</h2>

        {/* 썸네일 */}
        <div className='w-full aspect-video rounded-10 overflow-hidden bg-gray-700'>
          {thumbnail && (
            <img
              src={thumbnail}
              alt='busking thumbnail'
              className='size-full object-cover'
            />
          )}
        </div>

        {/* 안내 문구 */}
        <ul className='self-center flex flex-col'>
          <li className='typo-16r text-gray-200 before:content-["•"] before:mr-2'>
            라이브를 종료하면 방송이 즉시 종료됩니다.
          </li>
          <li className='typo-16r text-gray-200 before:content-["•"] before:mr-2'>
            종료된 방송은 다시 이어서 진행할 수 없습니다.
          </li>
        </ul>
      </div>

      {/* 종료 후 리포트 버튼 */}
      <Button variant={'accent'} className='mt-[6vh]' onClick={onConfirm}>
        라이브 버스킹 종료 후 리포트 받기
      </Button>
    </BaseModal>
  );
};

export default EndLiveModal;
