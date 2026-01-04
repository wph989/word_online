/**
 * 确认对话框组件
 * 用于需要用户确认的操作
 */

import { useState } from 'react';
import './ConfirmDialog.css';

export interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'info' | 'warning' | 'danger';
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmText = '确定',
  cancelText = '取消',
  type = 'info',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="confirm-dialog-overlay" onClick={onCancel}>
      <div
        className="confirm-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={`confirm-dialog-header confirm-dialog-${type}`}>
          <div className="confirm-dialog-icon">
            {type === 'info' && 'ℹ'}
            {type === 'warning' && '⚠'}
            {type === 'danger' && '⚠'}
          </div>
          <h3 className="confirm-dialog-title">{title}</h3>
        </div>

        <div className="confirm-dialog-body">
          <p className="confirm-dialog-message">{message}</p>
        </div>

        <div className="confirm-dialog-footer">
          <button
            className="confirm-dialog-button confirm-dialog-cancel"
            onClick={onCancel}
          >
            {cancelText}
          </button>
          <button
            className={`confirm-dialog-button confirm-dialog-confirm confirm-dialog-confirm-${type}`}
            onClick={() => {
              onConfirm();
              onCancel();
            }}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

// 确认对话框 Hook
export function useConfirmDialog() {
  const [dialogState, setDialogState] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    type: 'info' | 'warning' | 'danger';
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    type: 'info',
    onConfirm: () => {},
  });

  const showConfirm = (
    title: string,
    message: string,
    onConfirm: () => void,
    type: 'info' | 'warning' | 'danger' = 'info'
  ) => {
    setDialogState({
      isOpen: true,
      title,
      message,
      type,
      onConfirm,
    });
  };

  const hideConfirm = () => {
    setDialogState((prev) => ({ ...prev, isOpen: false }));
  };

  const confirmDelete = (itemName: string, onConfirm: () => void) => {
    showConfirm(
      '确认删除',
      `确定要删除"${itemName}"吗？此操作不可恢复。`,
      onConfirm,
      'danger'
    );
  };

  return {
    dialogProps: {
      ...dialogState,
      onCancel: hideConfirm,
    },
    showConfirm,
    hideConfirm,
    confirmDelete,
  };
}
