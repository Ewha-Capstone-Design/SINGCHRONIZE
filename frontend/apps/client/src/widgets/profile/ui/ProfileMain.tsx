'use client';

import { useNavigate } from '@/shared/lib/navigation';
import { useModal } from '@/shared/hooks';
import { ProfileCard } from '@/entities/user/ui';
import { BlockedModal } from '@/features/block';
import SnsAccountItem from './SnsAccountItem';

import { MOCK_PROFILE, MOCK_SNS_ACCOUNTS } from '@/entities/user/model/mock';

const ProfileMain = () => {
  const { go, ROUTES } = useNavigate();
  const blockedSongModal = useModal();
  const blockedArtistModal = useModal();

  const profile = MOCK_PROFILE;
  const kakaoAccount = MOCK_SNS_ACCOUNTS.find((a) => a.provider === 'kakao');
  const naverAccount = MOCK_SNS_ACCOUNTS.find((a) => a.provider === 'naver');

  const myRecords = [
    { label: '나의 보컬 리포트', route: ROUTES.my.vocalReport },
    { label: '나의 온라인 버스킹', route: ROUTES.my.busking },
  ];

  const accountSettings = [
    { label: '차단한 곡 관리하기', action: blockedSongModal.openModal },
    { label: '차단한 가수 관리하기', action: blockedArtistModal.openModal },
    { label: '로그아웃 하기', action: null },
    { label: '탈퇴하기', action: null },
  ];

  return (
    <div className='min-h-screen text-white'>
      <div className='px-8 flex items-center h-101.5 bg-linear-to-b from-yellow-900/40 to-bg'>
        <ProfileCard profile={profile} />
      </div>

      <div className='px-8 pb-8 grid grid-cols-1 lg:grid-cols-3 gap-8'>
        {/* SNS 연동 */}
        <div className='flex flex-col gap-3'>
          {kakaoAccount?.connected && (
            <SnsAccountItem
              provider='kakao'
              email={kakaoAccount.email}
              connected={kakaoAccount.connected}
            />
          )}
          {naverAccount?.connected && (
            <SnsAccountItem
              provider='naver'
              email={naverAccount.email}
              connected={naverAccount.connected}
            />
          )}
        </div>

        {/* 내 기록 */}
        <div>
          <h2 className='mb-2 typo-28b text-white'>내 기록</h2>
          <div className='py-2 rounded-10 bg-gray-800 overflow-hidden'>
            {myRecords.map((item) => (
              <button
                key={item.label}
                type='button'
                onClick={() => go(item.route)}
                className='px-9 py-2 w-full h-16 text-left typo-16m text-gray-200 hover:text-gray-400 transition-colors'
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* 계정 설정 */}
        <div>
          <h2 className='mb-2 typo-28b text-white'>계정 설정</h2>
          <div className='py-2 rounded-10 bg-gray-800 overflow-hidden'>
            {accountSettings.map((item) => (
              <button
                key={item.label}
                type='button'
                onClick={item.action ?? undefined}
                className='px-9 py-2 w-full h-16 text-left typo-16m text-gray-200 hover:text-gray-400 transition-colors'
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {blockedSongModal.open && (
        <BlockedModal type='song' onClose={blockedSongModal.closeModal} />
      )}
      {blockedArtistModal.open && (
        <BlockedModal type='artist' onClose={blockedArtistModal.closeModal} />
      )}
    </div>
  );
};

export default ProfileMain;
