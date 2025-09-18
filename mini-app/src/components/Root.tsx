import { App } from '@/components/App.tsx';
import { ErrorBoundary } from '@/components/ErrorBoundary.tsx';
import { NotificationProvider } from '@/components/Notification/NotificationContext';
import { NotificationToast } from '@/components/Notification/NotificationToast';

function ErrorBoundaryError({ error }: { error: unknown }) {
  return (
    <div>
      <p>An unhandled error occurred:</p>
      <blockquote>
        <code>
          {error instanceof Error
            ? error.message
            : typeof error === 'string'
              ? error
              : JSON.stringify(error)}
        </code>
      </blockquote>
    </div>
  );
}

export function Root() {
  return (
    <ErrorBoundary fallback={ErrorBoundaryError}>
      <NotificationProvider>
        <App/>
        <NotificationToast/>
      </NotificationProvider>
    </ErrorBoundary>
  );
}
