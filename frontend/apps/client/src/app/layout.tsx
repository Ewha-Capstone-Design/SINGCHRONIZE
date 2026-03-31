import type { Metadata } from 'next';
import Script from 'next/script';
import { metadataConfig } from './metadata';
import './global.css';
import { Providers } from './providers';
import { TooltipProvider } from '@singchronize/ui';

export const metadata: Metadata = metadataConfig;

const RootLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <html lang='ko'>
      <body className='h-screen bg-bg scrollbar-hide'>
        <Script
          src='https://t1.kakaocdn.net/kakao_js_sdk/2.7.2/kakao.min.js'
          strategy='beforeInteractive'
        />
        <Providers>
          <TooltipProvider delayDuration={0}>{children}</TooltipProvider>
        </Providers>
      </body>
    </html>
  );
};

export default RootLayout;
