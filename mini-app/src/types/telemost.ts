// Типы для Telemost API

export interface TeleMostCreateRoomRequest {
  user_id: number | null;
}

export interface TeleMostCreateRoomResponse {
  ok: boolean;
  url?: string;
  error?: string;
}

export interface VideoCallData {
  url: string;
  created_at: string;
}

export interface NotificationData {
  message: string;
  type: 'success' | 'error' | 'info';
}

export interface TelegramWebAppData {
  action: 'video_call_created';
  url: string;
}

// Константы
export const BUILD_VERSION = "1.1.0";

export const API_ENDPOINTS = {
  CREATE_ROOM: '/bot/telemost/api/telemost/create',
} as const;
