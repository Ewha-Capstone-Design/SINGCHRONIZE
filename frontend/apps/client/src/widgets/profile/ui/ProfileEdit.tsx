'use client';

import { useState } from 'react';
import { InputField, Button } from '@singchronize/ui';
import { IcBack } from '@/shared/assets/icons';
import { useNavigate } from '@/shared/lib/navigation';
import { ArtistCard } from '@/entities/artist/ui';
import { EditFavoriteArtistsModal } from '@/features/edit-favorite-artists';
import SnsAccountItem from './SnsAccountItem';

import { MOCK_PROFILE, MOCK_SNS_ACCOUNTS } from '@/entities/user/model/mock';
import { MOCK_ALL_ARTISTS } from '@/entities/artist/model/mock';

const ProfileEdit = () => {
  const { back } = useNavigate();

  const profile = MOCK_PROFILE;
  const artists = MOCK_ALL_ARTISTS.slice(0, 3);

  const [nickname, setNickname] = useState(profile.nickname);
  const [bio, setBio] = useState(profile.bio);

  const [isEditArtistsModalOpen, setIsEditArtistsModalOpen] = useState(false);

  return (
    <div className='min-h-screen text-white'>
      <div className='pt-12 pb-5 px-13 flex items-center gap-13'>
        <button type='button' onClick={back}>
          <IcBack />
        </button>
        <h1 className='typo-24b text-white'>프로필 수정하기</h1>
      </div>

      <div className='px-[10vw] py-10 flex gap-16'>
        {/* 프로필 이미지 */}
        <div className='flex flex-col items-center shrink-0'>
          <div className='size-38.5 rounded-full overflow-hidden bg-gray-800'>
            {profile.profileImage ? (
              <img
                src={profile.profileImage}
                alt={profile.nickname}
                className='size-full object-cover'
              />
            ) : (
              <div className='size-full bg-gray-700' />
            )}
          </div>
          <Button variant='normal' size={'medium'} className='mt-5 mb-2 w-fit'>
            사진 설정하기
          </Button>
          <p className='typo-16r text-gray-600'>JPG, PNG 파일 (최대 5MB)</p>
        </div>

        {/* 폼 */}
        <div className='flex-1 flex flex-col gap-12'>
          {/* 프로필 정보 */}
          <section className='flex flex-col gap-3'>
            <h2 className='typo-24b text-gray-100'>프로필 정보</h2>
            <div className='flex flex-col gap-2'>
              <label className='typo-16m text-gray-300'>닉네임</label>
              <InputField
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
              />
            </div>
            <div className='flex flex-col gap-2'>
              <label className='typo-16m text-gray-300'>소개</label>
              <InputField
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder='100자 이내로 입력해주세요'
                maxLength={100}
              />
            </div>
          </section>

          {/* SNS 계정 연동 */}
          <section className='flex flex-col gap-3'>
            <h2 className='typo-24b text-gray-100'>SNS 계정 연동</h2>
            <div className='flex flex-col gap-2'>
              {MOCK_SNS_ACCOUNTS.map((account) => (
                <SnsAccountItem
                  key={account.id}
                  provider={account.provider}
                  email={account.email}
                  connected={account.connected}
                  onConnect={() => {}}
                />
              ))}
            </div>
          </section>

          {/* 선호하는 가수 */}
          <section className='flex flex-col gap-3'>
            <div className='flex items-center justify-between'>
              <h2 className='typo-24b text-gray-100'>선호하는 가수</h2>
              <button
                type='button'
                className='typo-16r text-gray-300 hover:text-white transition-colors'
                onClick={() => setIsEditArtistsModalOpen(true)}
              >
                수정하기
              </button>
            </div>
            <div className='flex gap-4'>
              {artists.map((artist) => (
                <ArtistCard
                  key={artist.id}
                  artist={artist}
                  isSelected={true}
                  onToggle={() => {}}
                />
              ))}
            </div>
          </section>

          {/* 저장 */}
          <div className='flex justify-center py-4'>
            <Button
              onClick={() => {
                /* TODO: 저장 API */
              }}
            >
              저장하기
            </Button>
          </div>
        </div>
      </div>

      {isEditArtistsModalOpen && (
        <EditFavoriteArtistsModal
          initialSelectedIds={artists.map((a) => a.id)}
          onClose={() => setIsEditArtistsModalOpen(false)}
          onConfirm={(artists) => {
            /* TODO: 저장 */
          }}
        />
      )}
    </div>
  );
};

export default ProfileEdit;
