import type { ComponentType } from 'react';

import { TeleMostHomePage } from '@/pages/TeleMostHomePage/TeleMostHomePage';
import { VideoCallResultPage } from '@/pages/VideoCallResultPage/VideoCallResultPage';

interface Route {
  path: string;
  Component: ComponentType;
  title?: string;
}

export const routes: Route[] = [
  { path: '/', Component: TeleMostHomePage, title: 'Telemost' },
  { path: '/result', Component: VideoCallResultPage, title: 'Video Call Created' },
];
