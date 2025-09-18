import React from 'react';
import { useNotification } from './NotificationContext';
import './NotificationToast.css';

export const NotificationToast: React.FC = () => {
  const { notification, hideNotification } = useNotification();

  if (!notification) {
    return null;
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'info':
      default:
        return '🔗';
    }
  };

  return (
    <div 
      className={`notification-toast notification-toast--${notification.type}`}
      onClick={hideNotification}
    >
      <span className="notification-toast__icon">
        {getIcon(notification.type)}
      </span>
      <span className="notification-toast__message">
        {notification.message}
      </span>
    </div>
  );
};
