/**
 * 加载状态组件
 * 用于显示数据加载中的状态
 */

import './Loading.css';

interface LoadingProps {
  size?: 'small' | 'medium' | 'large';
  text?: string;
  fullscreen?: boolean;
}

export default function Loading({ 
  size = 'medium', 
  text = '加载中...', 
  fullscreen = false 
}: LoadingProps) {
  const sizeClass = `loading-spinner-${size}`;

  if (fullscreen) {
    return (
      <div className="loading-fullscreen">
        <div className="loading-content">
          <div className={`loading-spinner ${sizeClass}`}>
            <div className="spinner"></div>
          </div>
          {text && <div className="loading-text">{text}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="loading-inline">
      <div className={`loading-spinner ${sizeClass}`}>
        <div className="spinner"></div>
      </div>
      {text && <div className="loading-text">{text}</div>}
    </div>
  );
}

// 骨架屏组件
export function Skeleton({ 
  width = '100%', 
  height = '20px',
  count = 1,
  className = ''
}: { 
  width?: string | number; 
  height?: string | number;
  count?: number;
  className?: string;
}) {
  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <>
      {items.map((i) => (
        <div
          key={i}
          className={`skeleton ${className}`}
          style={{
            width: typeof width === 'number' ? `${width}px` : width,
            height: typeof height === 'number' ? `${height}px` : height,
            marginBottom: count > 1 ? '10px' : '0'
          }}
        />
      ))}
    </>
  );
}

// 文档列表骨架屏
export function DocumentListSkeleton() {
  return (
    <div className="document-list-skeleton">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="document-item-skeleton">
          <Skeleton width="60%" height="24px" />
          <Skeleton width="40%" height="16px" />
          <Skeleton width="80%" height="16px" />
        </div>
      ))}
    </div>
  );
}
