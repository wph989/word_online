import React from 'react';
import './Sidebar.css';

interface ChapterMeta {
  id: string;
  title: string;
  orderIndex: number; // 注意：前端可能使用驼峰，后端可能是下划线，需要调用处适配
}

interface SidebarProps {
  chapters: ChapterMeta[];
  currentChapterId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, newTitle: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  chapters, 
  currentChapterId, 
  onSelect, 
  onCreate, 
  onDelete,
  onRename
}) => {
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [editTitle, setEditTitle] = React.useState('');

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

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h3>文档大纲</h3>
        <button className="add-btn" onClick={onCreate} title="新建章节">+</button>
      </div>
      <ul className="chapter-list">
        {chapters.map((chapter) => (
          <li 
            key={chapter.id} 
            className={`chapter-item ${chapter.id === currentChapterId ? 'active' : ''}`}
            onClick={() => onSelect(chapter.id)}
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
            
            <button 
              className="delete-btn"
              onClick={(e) => {
                e.stopPropagation();
                if (window.confirm('确定要删除该章节吗？')) {
                  onDelete(chapter.id);
                }
              }}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Sidebar;
