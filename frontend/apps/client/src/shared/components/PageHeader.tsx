'use client';

import { IcBack } from '../assets/icons';
import { useNavigate } from '../lib/navigation';

interface PageHeaderProps {
  title: string;
  subText?: string;
}

const PageHeader = ({ title, subText }: PageHeaderProps) => {
  const { back } = useNavigate();

  return (
    <div className='flex justify-center items-center relative'>
      <button type='button' className='absolute top-0 left-15.5' onClick={back}>
        <IcBack />
      </button>
      <div className='flex flex-col items-center'>
        <h1 className='typo-32b text-gray-100'>{title}</h1>
        {subText && <p className='typo-14r text-gray-500'>{subText}</p>}
      </div>
    </div>
  );
};

export default PageHeader;
