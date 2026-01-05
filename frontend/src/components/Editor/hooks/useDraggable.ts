/**
 * 悬浮工具栏拖拽功能 Hook
 */

import { useEffect } from 'react';
import { IDomEditor } from '@wangeditor/editor';

export const useDraggable = (editor: IDomEditor | null) => {
  useEffect(() => {
    if (!editor) return;

    // 拖拽逻辑实现
    const enableDrag = (hoverBar: HTMLElement) => {
        if (hoverBar.dataset.dragEnabled === 'true') return;
        hoverBar.dataset.dragEnabled = 'true';
        
        // 核心状态：当前的位移偏移量
        const dragOffset = { x: 0, y: 0 };
        let isDragging = false;

        const applyTransform = () => {
             // 使用独立的 translate CSS 属性 (Chrome 104+)
             // 它独立于 transform 属性，不会被 WangEditor 的 style="transform:..." 覆盖
             // 且比 margin 更由硬件加速，定位更可靠
             const translateValue = `${dragOffset.x}px ${dragOffset.y}px`;
             
             if (hoverBar.style.translate !== translateValue) {
                 hoverBar.style.translate = translateValue;
             }
        };

        const insertHandle = () => {
             if (hoverBar.querySelector('.w-e-drag-handle')) return;
             if (!hoverBar.firstChild) return;

            const handle = document.createElement('div');
            handle.className = 'w-e-drag-handle';
            handle.title = "拖拽移动 (双击复位)";
            handle.innerHTML = `
              <svg viewBox="0 0 24 24" width="14" height="14" fill="#999">
                <path d="M9 3h2v18H9V3zm4 0h2v18h-2V3z"/>
              </svg>
            `;
            Object.assign(handle.style, {
              cursor: 'move',
              padding: '0 4px',
              marginRight: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRight: '1px solid #eee',
              height: '100%',
              userSelect: 'none',
              flexShrink: '0'
            });

            hoverBar.insertBefore(handle, hoverBar.firstChild);
            hoverBar.style.display = 'flex';
            hoverBar.style.alignItems = 'center';

            // 拖拽事件
            let startX = 0;
            let startY = 0;
            let startOffsetX = 0;
            let startOffsetY = 0;

            handle.addEventListener('dblclick', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dragOffset.x = 0;
                dragOffset.y = 0;
                applyTransform();
            });

            handle.addEventListener('mousedown', (e) => {
                e.preventDefault();
                e.stopPropagation();

                isDragging = true;
                startX = e.clientX;
                startY = e.clientY;
                startOffsetX = dragOffset.x;
                startOffsetY = dragOffset.y;

                const originalZIndex = hoverBar.style.zIndex;
                hoverBar.style.zIndex = '10001';
                // margin 动画不需要 transition hack

                const onMouseMove = (moveEvent: MouseEvent) => {
                    if (!isDragging) return;
                    const dx = moveEvent.clientX - startX;
                    const dy = moveEvent.clientY - startY;
                    
                    dragOffset.x = startOffsetX + dx;
                    dragOffset.y = startOffsetY + dy;
                    
                    applyTransform();
                };

                const onMouseUp = () => {
                    isDragging = false;
                    hoverBar.style.zIndex = originalZIndex;
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                };

                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
            });
        };

        insertHandle();

        // 监听 HoverBar 变化
        const barObserver = new MutationObserver((mutations) => {
            let shouldInsert = false;
            
            // 检查是否被隐藏
            const isVisible = hoverBar.style.display !== 'none';

            for (const m of mutations) {
                if (m.type === 'childList') {
                    shouldInsert = true;
                }
                
                // 如果 WangEditor 重写了 style (比如更新位置)，可能会把我们的 transform 抹掉
                // 所以只要是可见状态，我们都要强制把 transform 加回去
                if (m.type === 'attributes' && m.attributeName === 'style') {
                    if (isVisible) {
                        applyTransform();
                    } else {
                        // 如果变成隐藏了，重置偏移量 (根据需求，也可选择仅保留不重置)
                        // 这里选择重置，让下次显示时出现在默认位置
                        if (dragOffset.x !== 0 || dragOffset.y !== 0) {
                             dragOffset.x = 0;
                             dragOffset.y = 0;
                             // 此时不需要 applyTransform，因为它是隐藏的，甚至 transform 可能被清空也无所谓
                             // 等下次变可见时，style 变化会再次触发这里，但 offset 是 0，所以会设为 translate(0,0)
                        }
                    }
                }
            }

            if (shouldInsert) insertHandle();
        });

        barObserver.observe(hoverBar, { 
            childList: true, 
            attributes: true, 
            attributeFilter: ['style'] 
        });
    };

    // 全局监听器：发现新的 HoverBar 并初始化
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            mutation.addedNodes.forEach(node => {
                if (node instanceof HTMLElement) {
                    if (node.classList.contains('w-e-hover-bar')) {
                        enableDrag(node);
                    } else {
                        const bars = node.querySelectorAll('.w-e-hover-bar');
                        bars.forEach(b => enableDrag(b as HTMLElement));
                    }
                }
            });
        }
    });

    // 初始扫描
    document.querySelectorAll('.w-e-hover-bar').forEach(bar => {
        if (bar instanceof HTMLElement) enableDrag(bar);
    });

    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
        observer.disconnect();
        // barObserver 绑定在 closure 里，无法在此处清理，但随着 dom 销毁也会失效，或者在 enableDrag 里根据 element 销毁来清理
        // 实际上这在 React useEffect cleanup 中是可以接受的，因为 body observer 断开后不再触发新的 enableDrag
    };
  }, [editor]);
};
