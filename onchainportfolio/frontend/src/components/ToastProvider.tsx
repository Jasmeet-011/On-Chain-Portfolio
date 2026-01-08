// src/components/ToastProvider.tsx - Global Toast Configuration
import React from 'react';
import { Toaster } from 'react-hot-toast';
import { useAppContext } from '../context/AppContext';

const ToastProvider: React.FC = () => {
  const { theme } = useAppContext();

  return (
    <Toaster
      position="top-center"
      reverseOrder={false}
      gutter={8}
      containerClassName=""
      containerStyle={{}}
      toastOptions={{
        // Default options for all toasts
        duration: 4000,
        style: {
          background: theme === 'dark' ? '#18181b' : '#ffffff',
          color: theme === 'dark' ? '#fafafa' : '#18181b',
          border: theme === 'dark' ? '1px solid #3f3f46' : '1px solid #e5e7eb',
          padding: '12px 16px',
          borderRadius: '12px',
          fontSize: '14px',
          fontWeight: '500',
          boxShadow: theme === 'dark' 
            ? '0 10px 40px rgba(0, 0, 0, 0.4)' 
            : '0 10px 40px rgba(0, 0, 0, 0.1)',
        },
        
        // Success toast styling
        success: {
          duration: 3000,
          iconTheme: {
            primary: '#10b981',
            secondary: theme === 'dark' ? '#18181b' : '#ffffff',
          },
          style: {
            background: theme === 'dark' ? '#18181b' : '#ffffff',
            color: theme === 'dark' ? '#fafafa' : '#18181b',
            border: theme === 'dark' ? '1px solid #10b981' : '1px solid #10b981',
          },
        },
        
        // Error toast styling
        error: {
          duration: 5000,
          iconTheme: {
            primary: '#ef4444',
            secondary: theme === 'dark' ? '#18181b' : '#ffffff',
          },
          style: {
            background: theme === 'dark' ? '#18181b' : '#ffffff',
            color: theme === 'dark' ? '#fafafa' : '#18181b',
            border: theme === 'dark' ? '1px solid #ef4444' : '1px solid #ef4444',
          },
        },
        
        // Loading toast styling
        loading: {
          duration: Infinity,
          style: {
            background: theme === 'dark' ? '#18181b' : '#ffffff',
            color: theme === 'dark' ? '#a1a1aa' : '#71717a',
            border: theme === 'dark' ? '1px solid #3f3f46' : '1px solid #e5e7eb',
          },
        },
      }}
    />
  );
};

export default ToastProvider;