/**
 * Toast 通知组件
 * 用于显示操作成功/失败的提示信息
 */

import { useState, useEffect } from 'react';
import './Toast.css';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastProps {
  messages: ToastMessage[];
  onRemove: (id: string) => void;
}

export default function Toast({ messages, onRemove }: ToastProps) {
  useEffect(() => {
    messages.forEach((msg) => {
      const duration = msg.duration || 3000;
      const timer = setTimeout(() => {
        onRemove(msg.id);
      }, duration);

      return () => clearTimeout(timer);
    });
  }, [messages, onRemove]);

  if (messages.length === 0) return null;

  return (
    <div className="toast-container">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`toast toast-${msg.type}`}
          onClick={() => onRemove(msg.id)}
        >
          <div className="toast-icon">
            {msg.type === 'success' && '✓'}
            {msg.type === 'error' && '✕'}
            {msg.type === 'warning' && '⚠'}
            {msg.type === 'info' && 'ℹ'}
          </div>
          <div className="toast-message">{msg.message}</div>
          <button
            className="toast-close"
            onClick={(e) => {
              e.stopPropagation();
              onRemove(msg.id);
            }}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

// Toast 管理 Hook
export function useToast() {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  const showToast = (
    message: string,
    type: ToastType = 'info',
    duration?: number
  ) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    const newMessage: ToastMessage = { id, type, message, duration };
    
    setMessages((prev) => [...prev, newMessage]);
  };

  const removeToast = (id: string) => {
    setMessages((prev) => prev.filter((msg) => msg.id !== id));
  };

  const success = (message: string, duration?: number) => {
    showToast(message, 'success', duration);
  };

  const error = (message: string, duration?: number) => {
    showToast(message, 'error', duration);
  };

  const warning = (message: string, duration?: number) => {
    showToast(message, 'warning', duration);
  };

  const info = (message: string, duration?: number) => {
    showToast(message, 'info', duration);
  };

  return {
    messages,
    removeToast,
    success,
    error,
    warning,
    info,
  };
}
