import React from 'react';
import './Sidebar.css';

interface ChapterMeta {
  id: string;
  title: string;
  order_index: number;
  level: number;
  parent_id?: string | null;
}

interface SidebarProps {
  chapters: ChapterMeta[];
  currentChapterId: string | null;
  onSelect: (id: string) => void;
  onCreate: (parentId?: string) => void;
  onDelete: (id: string) => void;
  onRename: (id: string, newTitle: string) => void;
  onMove: (draggedId: string, newParentId: string | null, newIndex: number) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  chapters, 
  currentChapterId, 
  onSelect, 
  onCreate, 
  onDelete,
  onRename,
  onMove
}) => {
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [editTitle, setEditTitle] = React.useState('');

  // DnD State
  const [draggedId, setDraggedId] = React.useState<string | null>(null);
  const [dragOverInfo, setDragOverInfo] = React.useState<{ id: string, pos: 'top' | 'bottom' | 'inside' } | null>(null);

  const handleStartEdit = (chapter: ChapterMeta, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(chapter.id);
    setEditTitle(chapter.title);
  };

  const handleFinishEdit = () => {
    if (editingId && editTitle.trim()) {
      onRename(editingId, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleFinishEdit();
    if (e.key === 'Escape') setEditingId(null);
  };

  // DnD Handlers
  const handleDragStart = (e: React.DragEvent, id: string) => {
    e.dataTransfer.setData('text/plain', id);
    setDraggedId(id);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (draggedId === targetId) return;

    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const y = e.clientY - rect.top;
    const height = rect.height;

    // 判定区域：上25% -> before, 下25% -> after, 中间50% -> inside
    let pos: 'top' | 'bottom' | 'inside' = 'inside';
    if (y < height * 0.25) pos = 'top';
    else if (y > height * 0.75) pos = 'bottom';

    // 如果目标是自己或自己的子代（简单防错，主要逻辑后端也会借），前端可简单判断
    // 这里简单略过复杂判断...

    setDragOverInfo({ id: targetId, pos });
  };

  const handleDragLeave = () => {
    // 简单的 leave 处理可能导致闪烁，通常配合 onDragEnter 或只在 Drop/End 时清除
    // 这里暂不清除，依赖 DragOver 持续更新
  };

  const handleDragEnd = () => {
    setDraggedId(null);
    setDragOverInfo(null);
  };

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (!draggedId || !dragOverInfo) return;

    const { pos } = dragOverInfo;
    const targetChapter = chapters.find(c => c.id === targetId);
    if (!targetChapter) return;

    let newParentId: string | null = null;
    let newIndex = 0;

    if (pos === 'inside') {
      newParentId = targetId;
      // 插入到最后：计算targetId有多少个子节点
      const children = chapters.filter(c => c.parent_id === targetId);
      newIndex = children.length;
    } else {
      newParentId = targetChapter.parent_id || null;
      const siblings = chapters.filter(c => c.parent_id === newParentId).sort((a, b) => a.order_index - b.order_index);

      let targetIndex = siblings.findIndex(c => c.id === targetId);
      if (targetIndex === -1) targetIndex = 0; // Should not happen

      if (pos === 'top') {
        newIndex = targetChapter.order_index; // 插在它前面，占用它的 index
      } else {
        newIndex = targetChapter.order_index + 1; // 插在它后面
      }
    }

    onMove(draggedId, newParentId, newIndex);
    handleDragEnd();
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h3>文档大纲</h3>
        <button className="add-btn" onClick={() => onCreate()} title="新建章节">+</button>
      </div>
      <ul className="chapter-list">
        {chapters.map((chapter) => {
          let itemStyle = {};
          if (dragOverInfo && dragOverInfo.id === chapter.id) {
            if (dragOverInfo.pos === 'top') itemStyle = { borderTop: '2px solid #1890ff' };
            else if (dragOverInfo.pos === 'bottom') itemStyle = { borderBottom: '2px solid #1890ff' };
            else itemStyle = { backgroundColor: '#e6f7ff', border: '2px dashed #1890ff' };
          }

          return (
          <li 
            key={chapter.id} 
               className={`chapter-item ${chapter.id === currentChapterId ? 'active' : ''} ${draggedId === chapter.id ? 'dragging' : ''}`}
            onClick={() => onSelect(chapter.id)}
               style={{
                 paddingLeft: `${(chapter.level - 1) * 20 + 16}px`,
                 ...itemStyle
               }}
               draggable="true"
               onDragStart={(e) => handleDragStart(e, chapter.id)}
               onDragOver={(e) => handleDragOver(e, chapter.id)}
               onDragLeave={handleDragLeave}
               onDrop={(e) => handleDrop(e, chapter.id)}
               onDragEnd={handleDragEnd}
          >
            {editingId === chapter.id ? (
              <input 
                type="text" 
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onBlur={handleFinishEdit}
                onKeyDown={handleKeyDown}
                autoFocus
                onClick={(e) => e.stopPropagation()}
                className="rename-input"
              />
            ) : (
              <span 
                className="chapter-title" 
                title={chapter.title}
                onDoubleClick={(e) => handleStartEdit(chapter, e)}
              >
                {chapter.title || '未命名章节'}
              </span>
            )}
            
               <div className="chapter-actions">
                 <button 
                   className="action-btn add-sub-btn"
                   onClick={(e) => {
                     e.stopPropagation();
                     onCreate(chapter.id);
                   }}
                   title="添加子章节"
                 >
                   +
                 </button>
                 <button
                   className="action-btn delete-btn"
                   onClick={(e) => {
                     e.stopPropagation();
                     if (window.confirm('确定要删除该章节吗？将会同时删除所有子章节。')) {
                       onDelete(chapter.id);
                     }
                   }}
                   title="删除章节"
                 >
                   ×
                 </button>
               </div>
          </li>
          )
        })} 
      </ul>
    </div>
  );
};

export default Sidebar;
