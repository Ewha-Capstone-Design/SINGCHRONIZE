'use client';

import { Button } from '@singchronize/ui';
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
      className='relative flex flex-col items-center gap-6 w-120 bg-gray-900 rounded-20 px-10 pt-12 pb-10'
    >
      {/* 제목 */}
      <h2 className='typo-24b text-white'>라이브 버스킹을 종료할까요?</h2>

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
      <ul className='self-start flex flex-col gap-1'>
        <li className='typo-14r text-gray-400 before:content-["•"] before:mr-2'>
          라이브를 종료하면 방송이 즉시 종료됩니다.
        </li>
        <li className='typo-14r text-gray-400 before:content-["•"] before:mr-2'>
          종료된 방송은 다시 이어서 진행할 수 없습니다.
        </li>
      </ul>

      {/* 종료 후 리포트 버튼 */}
      <Button variant={'accent'} onClick={onConfirm}>
        라이브 버스킹 종료 후 리포트 받기
      </Button>
    </BaseModal>
  );
};

export default EndLiveModal;
