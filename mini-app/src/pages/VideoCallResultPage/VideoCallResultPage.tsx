import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { initDataState, useSignal, postEvent } from '@telegram-apps/sdk-react';
import { Cell } from '@telegram-apps/telegram-ui';
import { Page } from '@/components/Page';
import { telegramService } from '@/services/telegramService';
import { useNotification } from '@/components/Notification/NotificationContext';
import './VideoCallResultPage.css';
import logo from '@/logo.png';

interface LocationState {
  videoCallUrl: string;
}

export const VideoCallResultPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { showNotification } = useNotification();
  
  const [isLoading, setIsLoading] = useState(false);
  const [preparedMessageId, setPreparedMessageId] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  
  // Используем initDataState как в официальном SDK
  const initData = useSignal(initDataState);
  
  // Получаем user_id из initDataState
  const user_id = initData?.user?.id || null;
  
  // Отладочная информация
  console.log('=== VideoCallResultPage DEBUG ===');
  console.log('initData:', initData);
  console.log('user_id from initData:', user_id);
  console.log('initData.user:', initData?.user);
  console.log('================================');
  
  const state = location.state as LocationState;
  
  // Если нет URL, перенаправляем на главную
  if (!state?.videoCallUrl) {
    navigate('/');
    return null;
  }

  const { videoCallUrl } = state;

  // Получаем ID подготовленного сообщения при загрузке страницы
  useEffect(() => {
    const fetchPreparedMessageId = async () => {
      if (!user_id) {
        console.warn('User ID not available from initDataState:', initData);
        setIsReady(false);
        return;
      }

      try {
        console.log('Fetching prepared message ID for user:', user_id);
        const response = await fetch(`/bot/telemost/api/prepared-message-id?user_id=${user_id}&video_call_url=${encodeURIComponent(videoCallUrl)}`);
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.ok && data.id) {
          setPreparedMessageId(data.id);
          setIsReady(true);
          console.log('Prepared message ID:', data.id);
        } else {
          console.error('Failed to get prepared message ID:', data.error);
          setIsReady(false);
        }
      } catch (error) {
        console.error('Error fetching prepared message ID:', error);
        setIsReady(false);
      }
    };

    fetchPreparedMessageId();
  }, [videoCallUrl, user_id, initData]);

  const handleInviteFriends = async () => {
    if (!preparedMessageId) {
      showNotification('Prepared message not ready', 'error');
      return;
    }

    setIsLoading(true);
    try {
      console.log('Sending prepared message with ID:', preparedMessageId);
      // Отправляем подготовленное сообщение с полученным ID
      await postEvent('web_app_send_prepared_message', {
        id: preparedMessageId
      });
      console.log('Prepared message sent successfully');
    } catch (error) {
      console.error('Ошибка отправки сообщения:', error);
      alert('Ошибка отправки сообщения');
    } finally {
      setIsLoading(false);
    }
  };

  const handleJoinCall = () => {
    showNotification('Opening video meeting...', 'info');
    telegramService.openLink(videoCallUrl);
    showNotification('Video meeting opened!', 'success');
  };

  return (
    <Page back={true}>
      <div className="video-call-result">
        
        <div className="video-call-result__header">
          <img src={logo} alt="Telemost" className="video-call-result__logo-icon" />
          <h1 className="video-call-result__title">
            Telemost
          </h1>
          <p className="video-call-result__subtitle">
            click-and-join video call
          </p>
        </div>

        <div className="video-call-result__button-container">
        <Cell
          className={`video-call-result__invite-button ${!isReady || isLoading ? 'disabled' : ''}`}
          onClick={handleInviteFriends}
          disabled={!isReady || isLoading}
        >
          <div className="video-call-result__button-content">
          <svg width="88" height="48" viewBox="0 0 88 48" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M27.0275 30.1199C23.2219 33.4244 21.0691 37.6393 21.0691 41.4513C21.0691 42.6367 21.3587 43.7397 21.9111 44.6874H4.70912C1.63454 44.6874 0.5 43.4111 0.5 41.1684C0.5 34.9671 7.09092 27.4427 17.2876 27.4427C21.0878 27.4427 24.3864 28.4869 27.0275 30.1199ZM25.2984 15.1463C25.2984 20.106 21.6287 23.9762 17.2876 23.9762C12.9654 23.9762 9.28106 20.106 9.28106 15.1837C9.28106 10.3359 12.9964 6.54272 17.2876 6.54272C21.6017 6.54272 25.2984 10.2611 25.2984 15.1463Z" fill="#04060B"/>
<path d="M86.8156 41.1684C86.8156 43.4111 85.6769 44.6874 82.6063 44.6874H65.4393C65.9898 43.7397 66.2774 42.6367 66.2774 41.4513C66.2774 37.6354 64.1248 33.4158 60.3147 30.1096C62.9518 28.4822 66.2455 27.4427 70.0425 27.4427C80.2432 27.4427 86.8156 34.9671 86.8156 41.1684ZM78.0573 15.1463C78.0573 20.106 74.3836 23.9762 70.0425 23.9762C65.7242 23.9762 62.0212 20.106 62.0212 15.1837C62.0212 10.3359 65.7326 6.54272 70.0425 6.54272C74.3565 6.54272 78.0573 10.2611 78.0573 15.1463Z" fill="#04060B"/>
<path d="M43.6919 23.4556C48.6614 23.4556 52.8975 19.0335 52.8975 13.3168C52.8975 7.70961 48.6532 3.43541 43.6919 3.43541C38.7307 3.43541 34.4864 7.78444 34.4864 13.3583C34.4864 19.0335 38.7038 23.4556 43.6919 23.4556ZM28.4811 44.6833H58.8654C61.4302 44.6833 62.9605 43.4685 62.9605 41.4513C62.9605 35.5808 55.512 27.5071 43.6733 27.5071C31.8532 27.5071 24.4048 35.5808 24.4048 41.4513C24.4048 43.4685 25.9349 44.6833 28.4811 44.6833Z" fill="#04060B"/>
</svg>

            <h2>
              {isLoading ? 'Sending...' : isReady ? 'Invite friends' : 'Loading...'}
            </h2>
            <p>
              {isLoading ? 'Please wait...' : isReady ? 'Send an invitation to the call on Telegram' : 'Preparing invitation...'}
            </p>
          </div>
        </Cell>

        {/* Кнопка "Join" */}
        <Cell
          className="video-call-result__join-button"
          onClick={handleJoinCall}
        >
          <div className="video-call-result__button-content">
            <svg width="72" height="48" viewBox="0 0 72 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <g clip-path="url(#clip0_join)">
                <path d="M46.4849 14.5582V33.407C46.4849 37.4399 44.1036 39.7586 40.005 39.7586H25.1109C25.6346 38.4094 25.9142 36.9489 25.9142 35.4328C25.9142 28.5323 20.2383 22.8587 13.3381 22.8571V14.5617C13.3381 10.5409 15.8609 8.22234 19.818 8.22234H40.1655C44.2641 8.22234 46.4849 10.5409 46.4849 14.5582ZM60.8754 13.9571V34.1099C60.8754 35.7738 59.8227 36.8933 58.2629 36.8933C57.47 36.8933 56.6381 36.4603 55.8663 35.7891L49.2695 30.0999V17.9515L55.8663 12.278C56.6416 11.6067 57.4665 11.1738 58.2629 11.1738C59.8227 11.1738 60.8754 12.2933 60.8754 13.9571Z" fill="#04060B"/>
                <path d="M23.1934 35.4328C23.1934 40.8079 18.6819 45.2949 13.3347 45.2949C7.94053 45.2949 3.47614 40.8393 3.47614 35.4328C3.47614 30.0229 7.94053 25.5777 13.3347 25.5777C18.7481 25.5777 23.1934 30.0229 23.1934 35.4328ZM12.0352 30.4995V34.121H8.39451C7.61873 34.121 7.09501 34.6325 7.09501 35.4362C7.09501 36.2208 7.62906 36.7357 8.39451 36.7357H12.0352V40.3834C12.0352 41.1523 12.5501 41.6795 13.3347 41.6795C14.1228 41.6795 14.6342 41.1523 14.6342 40.3834V36.7357H18.2785C19.0474 36.7357 19.5745 36.2208 19.5745 35.4362C19.5745 34.6325 19.0474 34.121 18.2785 34.121H14.6342V30.4995C14.6342 29.7238 14.1228 29.2 13.3347 29.2C12.5501 29.2 12.0352 29.7341 12.0352 30.4995Z" fill="#04060B"/>
              </g>
              <defs>
                <clipPath id="clip0_join">
                  <rect width="70.4895" height="48" fill="white" transform="translate(0.755249)"/>
                </clipPath>
              </defs>
            </svg>
            <h2>Join Call</h2>
            <p>Open your video call</p>
          </div>
        </Cell>
        </div>
      </div>
    </Page>
  );
};
