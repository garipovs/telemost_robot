import { 
  retrieveLaunchParams 
} from '@telegram-apps/sdk-react';
import { TelegramWebAppData } from '@/types/telemost';

class TelegramService {
  private initialized = false;

  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      // Разворачиваем приложение
      await this.expandApp();
      
      this.initialized = true;
      console.log('TelegramService initialized successfully');
    } catch (error) {
      console.error('Error initializing TelegramService:', error);
      throw error;
    }
  }

  private async expandApp(): Promise<void> {
    try {
      // Принудительно разворачиваем приложение через старый Telegram API
      if (window.Telegram?.WebApp) {
        const webApp = window.Telegram.WebApp;
        webApp.expand();
        
        // Множественные попытки разворачивания
        const forceExpand = () => {
          console.log('Current expanded state:', webApp.isExpanded);
          console.log('Viewport height:', webApp.viewportHeight);
          
          if (webApp.viewportHeight < 500) {
            console.log('Viewport too small, forcing expand...');
            webApp.expand();
          }
        };

        // Несколько попыток с разными интервалами
        setTimeout(forceExpand, 100);
        setTimeout(forceExpand, 500);
        setTimeout(forceExpand, 1000);
        setTimeout(forceExpand, 2000);
      } else {
        console.warn('Telegram WebApp is not available');
      }

    } catch (error) {
      console.error('Error expanding viewport:', error);
    }
  }

  getUserId(): number | null {
    try {
      // Используем старый Telegram API
      if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
        return window.Telegram.WebApp.initDataUnsafe.user.id;
      }
      return null;
    } catch (error) {
      console.error('Error getting user ID:', error);
      return null;
    }
  }

  sendDataToBot(data: TelegramWebAppData): void {
    try {
      if (window.Telegram?.WebApp?.sendData) {
        window.Telegram.WebApp.sendData(JSON.stringify(data));
        console.log('Data sent to bot:', data);
      } else {
        console.warn('SendData is not available');
      }
    } catch (error) {
      console.error('Error sending data to bot:', error);
    }
  }

  openLink(url: string): void {
    try {
      if (window.Telegram?.WebApp) {
        const webApp = window.Telegram.WebApp;
        const platform = retrieveLaunchParams().tgWebAppPlatform;
        
        if (platform === 'ios') {
          // Для iOS закрываем приложение и открываем через Telegram
          webApp.close();
          webApp.openTelegramLink(url);
        } else {
          // Для других платформ открываем во встроенном браузере
          webApp.openLink(url, { try_instant_view: true });
        }
      } else {
        // Fallback: открываем в новой вкладке
        window.open(url, '_blank');
      }
    } catch (error) {
      console.error('Error opening link:', error);
      // Fallback: открываем в новой вкладке
      window.open(url, '_blank');
    }
  }

  shareInTelegram(url: string, text: string = 'Come and chat!'): void {
    try {
      if (window.Telegram?.WebApp?.openTelegramLink) {
        const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
        window.Telegram.WebApp.openTelegramLink(shareUrl);
      } else {
        this.fallbackShare(url, text);
      }
    } catch (error) {
      console.error('Error sharing in Telegram:', error);
      this.fallbackShare(url, text);
    }
  }

  private fallbackShare(url: string, text: string): void {
    // Web Share API
    if (navigator.share) {
      navigator.share({ title: 'Video Call', text, url }).catch(() => {
        this.copyToClipboard(`${text} ${url}`);
      });
      return;
    }

    // Fallback: копируем в буфер обмена
    this.copyToClipboard(`${text} ${url}`);
  }

  async copyToClipboard(text: string): Promise<boolean> {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      return false;
    }
  }

  isDarkTheme(): boolean {
    try {
      return window.Telegram?.WebApp?.colorScheme === 'dark';
    } catch (error) {
      return false;
    }
  }

  isAvailable(): boolean {
    return !!window.Telegram?.WebApp;
  }
}

export const telegramService = new TelegramService();
