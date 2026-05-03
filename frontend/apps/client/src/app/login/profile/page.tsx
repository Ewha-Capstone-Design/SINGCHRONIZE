'use client';

import { useRef, useState } from 'react';
import { InputField, Button } from '@singchronize/ui';
import { useNavigate } from '@/shared/lib/navigation';
import { cn } from '@/shared/lib/cn';
import { IcLogo, IcPlus, IcProfile } from '@/shared/assets/icons';
import { AppImage } from '@/shared/components';
import { useOnboardingStep1 } from '@/entities/user';

const ProfilePage = () => {
  const { go, ROUTES } = useNavigate();
  const { mutateAsync: onboardingStep1, isPending } = useOnboardingStep1();

  const fileRef = useRef<HTMLInputElement | null>(null);
  const fileObjRef = useRef<File | null>(null);

  const [nickname, setNickname] = useState('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const openPicker = () => {
    fileRef.current?.click();
  };

  const onPickFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    fileObjRef.current = file;
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const isValid = nickname.trim().length >= 2 && nickname.trim().length <= 10;

  const handleNext = async () => {
    const formData = new FormData();
    formData.append('nickname', nickname.trim());
    if (fileObjRef.current) {
      formData.append('profile_image', fileObjRef.current);
    }
    await onboardingStep1(formData);
    go(ROUTES.login.taste);
  };

  return (
    <main className='flex flex-col items-center'>
      <div className='flex flex-col items-center gap-8'>
        <IcLogo />
        <h1 className='typo-38b text-center text-white'>프로필을 설정해주세요</h1>
      </div>

      <section className='mt-[8vh] flex flex-col items-center gap-12 w-full'>
        <div className='relative'>
          <div
            className={cn(
              'relative w-44 h-44 overflow-hidden rounded-full',
              'bg-gray-800',
            )}
          >
            {previewUrl ? (
              <AppImage
                src={previewUrl}
                alt='프로필 미리보기'
                fill
                className='object-cover'
              />
            ) : (
              <IcProfile />
            )}
          </div>

          <button
            type='button'
            onClick={openPicker}
            className={cn(
              'absolute -bottom-1 -right-1',
              'flex h-10 w-10 items-center justify-center rounded-full',
              'bg-white text-black',
            )}
          >
            <IcPlus />
          </button>

          <input
            ref={fileRef}
            type='file'
            accept='image/jpeg,image/png,image/webp,image/gif'
            className='hidden'
            onChange={onPickFile}
          />
        </div>

        <InputField
          value={nickname}
          onChange={(e) => setNickname(e.target.value)}
          placeholder='어떻게 불러드리면 좋을까요?'
          maxLength={10}
          message='2자 이상 10자 이하로 입력해주세요'
        />

        <div className='flex justify-center w-full'>
          <Button
            variant={'primary'}
            disabled={!isValid || isPending}
            onClick={handleNext}
          >
            다음으로 넘어가기
          </Button>
        </div>
      </section>
    </main>
  );
};

export default ProfilePage;
