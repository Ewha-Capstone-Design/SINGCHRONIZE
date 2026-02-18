import type { Metadata } from 'next';

export const metadataConfig: Metadata = {
  title: {
    default: 'SINGCHRONIZE',
    template: '%s | SINGCHRONIZE',
  },

  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
    shortcut: '/favicon.ico',
  },
};
