import { LoginGradientBg } from './_components';

const LoginLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className='relative w-full min-h-dvh text-white'>
      <LoginGradientBg />
      <div className='relative py-[13vh] flex justify-center w-full min-h-dvh'>
        {children}
      </div>
    </div>
  );
};

export default LoginLayout;
