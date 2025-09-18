import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cell } from '@telegram-apps/telegram-ui';
import { Page } from '@/components/Page';
import { teleMostAPI } from '@/services/telemostAPI';
import { telegramService } from '@/services/telegramService';
import { useNotification } from '@/components/Notification/NotificationContext';
import './TeleMostHomePage.css';
import logo from '@/logo.png';

export const TeleMostHomePage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { showNotification } = useNotification();

  const handleCreateRoom = async () => {
    if (isLoading) return;

    setIsLoading(true);
    try {
      const userId = telegramService.getUserId(); // Получаем ID пользователя из Telegram
      const response = await teleMostAPI.createRoom(userId);  // Создаем комнату через API
      if (response.ok && response.url) {
        showNotification('Meeting created', 'success');  // Показываем уведомление об успехе
                // Отправляем данные боту
        telegramService.sendDataToBot({
          action: 'video_call_created',
          url: response.url
        });
        
        // Переходим на страницу результата
        navigate('/result', { 
          state: { 
            videoCallUrl: response.url 
          } 
        });
      } else {
        throw new Error('Failed to create meeting');
      }
    } catch (error) {
      console.error('Error creating room:', error);
      showNotification('Failed to create meeting', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Page back={false}>
      <div className="telemost-home">
 
        <div className="telemost-home__header">
          <img src={logo} alt="Telemost" className="telemost-home__logo-icon" />
          <h1 className="telemost-home__title">
            Telemost
          </h1>
          <p className="telemost-home__subtitle">
            click-and-join video call
          </p>
        </div>

        {/* Основная кнопка */}
        
          <Cell
            className="telemost-home__create-button"
            onClick={handleCreateRoom}
            disabled={isLoading}
          >
            <div className="telemost-home__button-content">
              
              <svg width="72" height="48" viewBox="0 0 72 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <g clip-path="url(#clip0_2493_6742)">
              <path d="M46.4849 14.5582V33.407C46.4849 37.4399 44.1036 39.7586 40.005 39.7586H25.1109C25.6346 38.4094 25.9142 36.9489 25.9142 35.4328C25.9142 28.5323 20.2383 22.8587 13.3381 22.8571V14.5617C13.3381 10.5409 15.8609 8.22234 19.818 8.22234H40.1655C44.2641 8.22234 46.4849 10.5409 46.4849 14.5582ZM60.8754 13.9571V34.1099C60.8754 35.7738 59.8227 36.8933 58.2629 36.8933C57.47 36.8933 56.6381 36.4603 55.8663 35.7891L49.2695 30.0999V17.9515L55.8663 12.278C56.6416 11.6067 57.4665 11.1738 58.2629 11.1738C59.8227 11.1738 60.8754 12.2933 60.8754 13.9571Z" fill="#04060B"/>
              <path d="M23.1934 35.4328C23.1934 40.8079 18.6819 45.2949 13.3347 45.2949C7.94053 45.2949 3.47614 40.8393 3.47614 35.4328C3.47614 30.0229 7.94053 25.5777 13.3347 25.5777C18.7481 25.5777 23.1934 30.0229 23.1934 35.4328ZM12.0352 30.4995V34.121H8.39451C7.61873 34.121 7.09501 34.6325 7.09501 35.4362C7.09501 36.2208 7.62906 36.7357 8.39451 36.7357H12.0352V40.3834C12.0352 41.1523 12.5501 41.6795 13.3347 41.6795C14.1228 41.6795 14.6342 41.1523 14.6342 40.3834V36.7357H18.2785C19.0474 36.7357 19.5745 36.2208 19.5745 35.4362C19.5745 34.6325 19.0474 34.121 18.2785 34.121H14.6342V30.4995C14.6342 29.7238 14.1228 29.2 13.3347 29.2C12.5501 29.2 12.0352 29.7341 12.0352 30.4995Z" fill="#04060B"/>
              </g>
              <defs>
              <clipPath id="clip0_2493_6742">
              <rect width="70.4895" height="48" fill="white" transform="translate(0.755249)"/>
              </clipPath>
              </defs>
              </svg>
                <h2>New video call</h2>
                <p>It will start right now,<br/>send the link to the friends.</p>
             
            </div>
          </Cell>
       
      </div>
    </Page>
  );
};
