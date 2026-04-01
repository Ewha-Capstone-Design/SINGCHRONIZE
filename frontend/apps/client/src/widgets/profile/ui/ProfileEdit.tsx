'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { InputField, Button } from '@singchronize/ui';
import { BackButton } from '@/shared/components';
import { useThumbnail } from '@/shared/hooks';
import { ArtistCard } from '@/entities/artist/ui';
import { EditFavoriteArtistsModal } from '@/features/edit-favorite-artists';
import SnsAccountItem from './SnsAccountItem';
import type { ArtistUiType } from '@/entities/artist/model/types';

import {
  useMe,
  useUpdateMe,
  useUpdateProfile,
  useOnboardingStep2,
} from '@/entities/user';
import { toSnsAccountsUiType } from '@/entities/user';

type ProfileFormState = {
  nickname: string;
  bio: string;
  favoriteArtists: ArtistUiType[];
};

const EMPTY_FORM: ProfileFormState = {
  nickname: '',
  bio: '',
  favoriteArtists: [],
};

const ProfileEdit = () => {
  const { data: userData, isLoading, error } = useMe();
  const { mutate: updateMe, isPending: isUpdatingMe } = useUpdateMe();
  const { mutate: updateProfile, isPending: isUpdatingProfile } = useUpdateProfile();
  const { mutate: updateFavoriteSingers, isPending: isUpdatingFavorites } =
    useOnboardingStep2();

  const [form, setForm] = useState<ProfileFormState>(EMPTY_FORM);
  const [isEditArtistsModalOpen, setIsEditArtistsModalOpen] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { thumbnail, preview, handleThumbnailChange, clearThumbnail } = useThumbnail();

  useEffect(() => {
    if (!userData) return;

    setForm({
      nickname: userData.nickname,
      bio: userData.bio ?? '',
      favoriteArtists: userData.favorite_singers.map((singer) => ({
        id: singer.singer_id,
        name: singer.name,
        imageUrl: singer.photo_url ?? null,
      })),
    });

    clearThumbnail();
  }, [userData, clearThumbnail]);

  const snsAccounts = useMemo(() => {
    return toSnsAccountsUiType(userData?.linked_providers ?? []);
  }, [userData?.linked_providers]);

  const handleNicknameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;

    setForm((prev) => ({
      ...prev,
      nickname: value,
    }));
  };

  const handleBioChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;

    setForm((prev) => ({
      ...prev,
      bio: value,
    }));
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const previewUrl = URL.createObjectURL(file);
    handleThumbnailChange(file, previewUrl);
  };

  const isSameArtistIds = (prevIds: number[], nextIds: number[]) => {
    if (prevIds.length !== nextIds.length) return false;

    const sortedPrevIds = [...prevIds].sort((a, b) => a - b);
    const sortedNextIds = [...nextIds].sort((a, b) => a - b);

    return sortedPrevIds.every((id, index) => id === sortedNextIds[index]);
  };

  const handleArtistsConfirm = (selectedArtists: ArtistUiType[]) => {
    setForm((prev) => ({
      ...prev,
      favoriteArtists: selectedArtists,
    }));

    setIsEditArtistsModalOpen(false);
  };

  const handleSave = () => {
    if (!userData) return;

    const trimmedNickname = form.nickname.trim();
    const trimmedBio = form.bio.trim();

    const isNicknameChanged = trimmedNickname !== userData.nickname;
    const isBioChanged = trimmedBio !== (userData.bio ?? '');
    const isImageChanged = !!thumbnail?.file;

    const originalArtistIds = userData.favorite_singers.map((artist) => artist.singer_id);
    const selectedArtistIds = form.favoriteArtists.map((artist) => artist.id);
    const isFavoriteArtistsChanged = !isSameArtistIds(
      originalArtistIds,
      selectedArtistIds,
    );

    if (isNicknameChanged) {
      updateMe({
        nickname: trimmedNickname,
      });
    }

    if (isBioChanged || isImageChanged) {
      const formData = new FormData();

      if (isBioChanged) {
        formData.append('bio', trimmedBio);
      }

      if (thumbnail?.file) {
        formData.append('profile_image', thumbnail.file);
      }

      updateProfile(formData);
    }

    if (isFavoriteArtistsChanged) {
      updateFavoriteSingers(selectedArtistIds);
    }
  };

  if (isLoading) {
    return <div className='min-h-screen flex items-center justify-center text-white' />;
  }

  if (error || !userData) {
    return (
      <div className='min-h-screen flex items-center justify-center text-white'>
        오류가 발생했습니다.
      </div>
    );
  }

  const profileImageSrc = preview ?? userData.profile_img ?? null;

  return (
    <div className='min-h-screen text-white'>
      <div className='pt-12 pb-5 px-13 flex items-center gap-13'>
        <BackButton />
        <h1 className='typo-24b text-white'>프로필 수정하기</h1>
      </div>

      <div className='px-[10vw] py-10 flex gap-16'>
        {/* 프로필 이미지 */}
        <div className='flex flex-col items-center shrink-0'>
          <div className='size-38.5 rounded-full overflow-hidden bg-gray-800'>
            {profileImageSrc ? (
              <img
                src={profileImageSrc}
                alt={form.nickname || '프로필 이미지'}
                className='size-full object-cover'
              />
            ) : (
              <div className='size-full bg-gray-700' />
            )}
          </div>

          <input
            ref={fileInputRef}
            type='file'
            accept='image/jpeg, image/png'
            className='hidden'
            onChange={handleImageChange}
          />

          <Button
            variant='normal'
            size='medium'
            className='mt-5 mb-2 w-fit'
            onClick={() => fileInputRef.current?.click()}
          >
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
              <InputField value={form.nickname} onChange={handleNicknameChange} />
            </div>

            <div className='flex flex-col gap-2'>
              <label className='typo-16m text-gray-300'>소개</label>
              <InputField
                value={form.bio}
                onChange={handleBioChange}
                placeholder='100자 이내로 입력해주세요'
                maxLength={100}
              />
            </div>
          </section>

          {/* SNS 계정 연동 */}
          <section className='flex flex-col gap-3'>
            <h2 className='typo-24b text-gray-100'>SNS 계정 연동</h2>
            <div className='flex flex-col gap-2'>
              {snsAccounts.map((account) => (
                <SnsAccountItem
                  key={account.provider}
                  provider={account.provider}
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
              {form.favoriteArtists.map((artist) => (
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
              onClick={handleSave}
              disabled={isUpdatingMe || isUpdatingProfile || isUpdatingFavorites}
            >
              저장하기
            </Button>
          </div>
        </div>
      </div>

      {isEditArtistsModalOpen && (
        <EditFavoriteArtistsModal
          initialSelectedArtists={form.favoriteArtists}
          onClose={() => setIsEditArtistsModalOpen(false)}
          onConfirm={handleArtistsConfirm}
        />
      )}
    </div>
  );
};

export default ProfileEdit;
