import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { NotificationData } from '@/types/telemost';

interface NotificationContextType {
  showNotification: (message: string, type?: NotificationData['type']) => void;
  hideNotification: () => void;
  notification: NotificationData | null;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notification, setNotification] = useState<NotificationData | null>(null);

  const showNotification = useCallback((message: string, type: NotificationData['type'] = 'info') => {
    setNotification({ message, type });
    
    // Автоматически скрываем уведомление через 3 секунды
    setTimeout(() => {
      setNotification(null);
    }, 3000);
  }, []);

  const hideNotification = useCallback(() => {
    setNotification(null);
  }, []);

  const value: NotificationContextType = {
    showNotification,
    hideNotification,
    notification,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
