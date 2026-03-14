import { Button } from '@singchronize/ui';
import { useNavigate } from '@/shared/lib/navigation';
import type { ProfileUiType } from '../model/types';

interface ProfileCardProps {
  profile: ProfileUiType;
}

const ProfileCard = ({ profile }: ProfileCardProps) => {
  const { go, ROUTES } = useNavigate();

  return (
    <div className='flex gap-5 h-37.5'>
      <div className='size-37.5 rounded-full border-2 border-brand overflow-hidden shrink-0 bg-gray-800'>
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
      <div className='flex flex-col justify-between h-full'>
        <div>
          <h1 className='typo-38b text-white'>{profile.nickname}</h1>
          <p className='typo-20r text-gray-400'>{profile.bio}</p>
        </div>
        <Button variant={'normal'} onClick={() => go(ROUTES.my.edit)}>
          프로필 수정하기
        </Button>
      </div>
    </div>
  );
};

export default ProfileCard;
