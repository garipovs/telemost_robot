import { Section, List, ButtonCell } from '@telegram-apps/telegram-ui';
import { postEvent } from '@telegram-apps/sdk';
import { initDataState, useSignal } from '@telegram-apps/sdk-react';
import type { FC } from 'react';
import { useState, useEffect } from 'react';

import { Page } from '@/components/Page.tsx';

export const SendMessagePage: FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [preparedMessageId, setPreparedMessageId] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [debugInfo, setDebugInfo] = useState<any>({});
  
  // Используем initDataState как в официальном шаблоне
  const initData = useSignal(initDataState);
  
  // Получаем user_id из initDataState (как в официальном шаблоне)
  const user_id = initData?.user?.id || null;
  
  // Отладочная информация
  console.log('=== DEBUG INFO ===');
  console.log('initData:', initData);
  console.log('initData.user:', initData?.user);
  console.log('user_id from initData:', user_id);
  console.log('==================');

  // Обновляем отладочную информацию для отображения
  useEffect(() => {
    setDebugInfo({
      initData: initData,
      user: initData?.user,
      user_id: user_id,
      hasUser: !!initData?.user,
    });
  }, [initData, user_id]);

  // Получаем ID подготовленного сообщения при загрузке страницы
  useEffect(() => {
    const fetchPreparedMessageId = async () => {
      // Fallback для тестирования - используем тестовый user_id
      const testUserId = user_id || 12345; // Временный ID для тестирования
      
      if (!user_id) {
        console.warn('User ID not available, using test ID:', testUserId);
      }

      try {
        console.log('Fetching prepared message ID for user:', testUserId);
        const response = await fetch(`/api/prepared-message-id?user_id=${testUserId}`);
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);
        setPreparedMessageId(data.id);
        setIsReady(true);
        console.log('Prepared message ID:', data.id);
      } catch (error) {
        console.error('Ошибка получения ID подготовленного сообщения:', error);
        setIsReady(false);
      }
    };

    fetchPreparedMessageId();
  }, [user_id]);

  const sendPreparedMessage = async () => {
    if (!preparedMessageId) {
      alert('Подготовленное сообщение не готово');
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

  return (
    <Page>
      <List>
        <Section
          header="Написать сообщение"
          footer={isReady ? "Готово к отправке" : "Загрузка..."}
        >
          <ButtonCell
            title={
              isLoading 
                ? "Отправка..." 
                : isReady 
                  ? "Отправить подготовленное сообщение" 
                  : "Загрузка..."
            }
            onClick={sendPreparedMessage}
            disabled={isLoading || !isReady}
          />
        </Section>
        
        <Section header="🔍 Отладочная информация">
          <ButtonCell
            title={`User ID: ${user_id || 'Не найден'}`}
            onClick={() => console.log('User ID clicked:', user_id)}
          />
          <ButtonCell
            title={`InitData: ${initData ? 'Доступен' : 'Недоступен'}`}
            onClick={() => console.log('InitData clicked:', initData)}
          />
          <ButtonCell
            title={`User: ${initData?.user ? 'Доступен' : 'Недоступен'}`}
            onClick={() => console.log('User clicked:', initData?.user)}
          />
          <ButtonCell
            title={`Prepared ID: ${preparedMessageId || 'Не загружен'}`}
            onClick={() => console.log('Prepared ID clicked:', preparedMessageId)}
          />
          <ButtonCell
            title={`Ready: ${isReady ? 'Да' : 'Нет'}`}
            onClick={() => console.log('Ready clicked:', isReady)}
          />
        </Section>

        <Section header="📊 Детальная отладка">
          <ButtonCell
            title="Показать InitData"
            onClick={() => {
              console.log('=== INIT DATA ===');
              console.log(JSON.stringify(initData, null, 2));
            }}
          />
          <ButtonCell
            title="Показать Debug Info"
            onClick={() => {
              console.log('=== DEBUG INFO ===');
              console.log(JSON.stringify(debugInfo, null, 2));
            }}
          />
          <ButtonCell
            title="Тест API"
            onClick={async () => {
              try {
                const response = await fetch('/api/prepared-message-id?user_id=12345');
                const data = await response.json();
                console.log('API Test Result:', data);
                alert(`API Test: ${JSON.stringify(data)}`);
              } catch (error) {
                console.error('API Test Error:', error);
                alert(`API Test Error: ${error}`);
              }
            }}
          />
        </Section>
      </List>
    </Page>
  );
};