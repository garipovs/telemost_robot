import { 
  TeleMostCreateRoomRequest, 
  TeleMostCreateRoomResponse, 
  API_ENDPOINTS 
} from '@/types/telemost';

class TeleMostAPIService {
  constructor() {
    // Используем относительные пути, так как приложение будет на том же домене
  }

  async createRoom(userId: number | null): Promise<TeleMostCreateRoomResponse> {
    try {
      const request: TeleMostCreateRoomRequest = {
        user_id: userId
      };

      const response = await fetch(API_ENDPOINTS.CREATE_ROOM, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: TeleMostCreateRoomResponse = await response.json();
      
      if (!data.ok || !data.url) {
        throw new Error(data.error || 'Backend did not return URL');
      }

      return data;
    } catch (error) {
      console.error('Error creating room:', error);
      throw error;
    }
  }
}

export const teleMostAPI = new TeleMostAPIService();
