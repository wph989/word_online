import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Editor, { EditorRef } from '../components/Editor'
import Sidebar from '../components/Sidebar'
import ErrorBoundary from '../components/ErrorBoundary'
import Toast, { useToast } from '../components/Toast'
import Loading from '../components/Loading'
import ConfirmDialog, { useConfirmDialog } from '../components/ConfirmDialog'
import AIPanel from '../components/AIPanel'
import type { Chapter } from '../types/api'
import { chapterService } from '../services/chapterService'

interface ChapterMeta {
  id: string;
  title: string;
  order_index: number;
  level: number;
  parent_id?: string | null;
}

const DocumentEditor: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  // ... (hooks) ...
  const navigate = useNavigate();
  const editorRef = useRef<EditorRef>(null);

  const [docTitle, setDocTitle] = useState('');
  const [chapterList, setChapterList] = useState<ChapterMeta[]>([]);
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedText, setSelectedText] = useState(''); // 实时选中文本

  // 临时存储编辑器内容，用于保存
  const [currentHtml, setCurrentHtml] = useState('');

  // UI 组件 Hooks
  const toast = useToast();
  const confirm = useConfirmDialog();

  useEffect(() => {
    if (docId) {
      loadDocument(docId);
    }
  }, [docId]);

  const loadDocument = async (id: string) => {
    setLoading(true);
    try {
      const doc = await chapterService.getDocument(id);
      setDocTitle(doc.title);
      // 后端返回的 chapter 可能有 order_index，需要适配
      const adaptedChapters = (doc.chapters || []).map((c: any) => ({
        id: c.id,
        title: c.title,
        order_index: c.order_index || 0,
        level: c.level || 1,
        parent_id: c.parent_id || null
      }));
      setChapterList(adaptedChapters);

      if (adaptedChapters.length > 0) {
        await loadChapter(adaptedChapters[0].id);
      } else {
        // 如果没有章节，不自动创建，让用户手动创建
        setChapter(null);
      }
    } catch (err) {
      console.error('Initialization failed:', err);
      toast.error('加载文档失败');
    } finally {
      setLoading(false);
    }
  };

  // ... (loadChapter function is fine) ...

  const loadChapter = async (id: string) => {
    if (!id) return;
    try {
      const data = await chapterService.getChapter(id);
      console.log('=== 后端返回的章节数据 ===');
      console.log('章节 ID:', data.id);
      console.log('章节标题:', data.title);
      console.log('HTML 内容:', data.html_content);
      console.log('HTML 长度:', data.html_content?.length);
      console.log('========================');

      setChapter(data);
      setCurrentHtml(data.html_content || '');
    } catch (e) {
      console.error("Failed to load chapter", e);
      toast.error('加载章节失败');
    }
  };

  const handleCreateChapter = async (parentId?: string) => {
    if (!docId) return;
    try {
      // 计算 level
      let level = 1;
      if (parentId) {
        const parent = chapterList.find(c => c.id === parentId);
        if (parent) {
          level = parent.level + 1;
        }
      }

      // 计算 order_index (简单起见，放在同级最后)
      // 注意：这里需要准确过滤同级章节。如果仅仅是追加，重新加载列表最安全。
      const siblings = chapterList.filter(c => c.parent_id === (parentId || null));
      const orderIndex = siblings.length;

      const newChapter = await chapterService.createChapter(
        `新章节 ${chapterList.length + 1}`,
        docId,
        { parent_id: parentId, level, order_index: orderIndex }
      );

      // 重新加载整个文档结构以确保排序正确（后端会处理排序）
      await loadDocument(docId);

      // 自动选中新章节
      setChapter(newChapter);
      setCurrentHtml(newChapter.html_content || '');
      toast.success('章节创建成功');
    } catch (e) {
      toast.error('创建章节失败');
    }
  };

  const handleDeleteChapter = async (id: string) => {
    const chapterToDelete = chapterList.find(c => c.id === id);
    if (!chapterToDelete) return;

    confirm.confirmDelete(chapterToDelete.title, async () => {
      try {
        await chapterService.deleteChapter(id);

        // 删除章节后重新加载文档结构，确保所有子章节也被移除
        if (docId) {
          await loadDocument(docId);
        }

        // 如果当前选中的是被删除的章节（或其子章节），则选中第一个可用章节
        if (chapter && (chapter.id === id || chapterList.find(c => c.id === id)?.id === chapter.parent_id)) {
          // 由于 state 更新是异步的，这里暂时无法获取最新的 list。
          // loadDocument 会设置新的 list。
          // 我们可以简单地清空当前章节，loadDocument 的逻辑会处理选中第一个。
          setChapter(null);
          setCurrentHtml('');
        }

        toast.success('章节已删除');
      } catch (e) {
        toast.error('删除失败');
      }
    });
  };

  const handleRenameChapter = async (id: string, newTitle: string) => {
    try {
      await chapterService.updateChapter(id, { title: newTitle });

      setChapterList(prev => prev.map(c =>
        c.id === id ? { ...c, title: newTitle } : c
      ));

      if (chapter && chapter.id === id) {
        setChapter({ ...chapter, title: newTitle });
      }
      toast.success('重命名成功');
    } catch (e) {
      toast.error('重命名失败');
    }
  };

  const handleMoveChapter = async (draggedId: string, newParentId: string | null, newIndex: number) => {
    try {
      await chapterService.moveChapter(draggedId, newParentId, newIndex);
      // 移动后重新加载文档结构
      if (docId) await loadDocument(docId);
    } catch (e: any) {
      toast.error('移动章节失败: ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleEditorChange = (html: string) => {
    setCurrentHtml(html);
  };

  const handleSave = async () => {
    if (!chapter) return;
    setSaving(true);
    try {
      console.log('Saving HTML:', currentHtml.substring(0, 200)); // Debug log
      await chapterService.updateChapter(chapter.id, {
        html_content: currentHtml,
        title: chapter.title
      });
      console.log('Saved successfully');
      toast.success('保存成功');
      // 保存后重新加载以获取后端渲染的HTML
      await loadChapter(chapter.id);
    } catch (err) {
      toast.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleExportChapter = () => {
    if (!chapter) return;
    try {
      chapterService.exportChapterToDocx(chapter.id);
      toast.success('导出成功');
    } catch (e) {
      toast.error('导出失败');
    }
  };

  const handleExportDocument = () => {
    if (!docId) return;
    try {
      chapterService.exportDocumentToDocx(docId);
      toast.success('导出成功');
    } catch (e) {
      toast.error('导出失败');
    }
  };

  // AI 编辑功能
  const handleAIEdit = async (action: string, text: string): Promise<string> => {
    try {
      const response = await fetch('/api/v1/ai/edit/text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          action,
        }),
      });

      if (!response.ok) {
        throw new Error('AI 操作失败');
      }

      const data = await response.json();
      return data.edited_text;
    } catch (error) {
      console.error('AI 编辑失败:', error);
      toast.error('AI 处理失败');
      throw error;
    }
  };

  const handleAIInsert = (text: string) => {
    // 将 AI 生成的文本插入到编辑器末尾
    if (editorRef.current) {
      editorRef.current.focus();
      editorRef.current.insertHtml(`<p>${text}</p>`);
      toast.success('内容已插入');
    } else {
      const newHtml = currentHtml + `<p>${text}</p>`;
      setCurrentHtml(newHtml);
      toast.success('内容已追加');
    }
  };

  // AI 替换选中内容（保持原格式）
  const handleAIReplace = (text: string) => {
    if (editorRef.current) {
      // 传递纯文本，replaceSelection 会使用 insertText 保留原格式
      editorRef.current.replaceSelection(text);
      toast.success('内容已替换');
    } else {
      toast.error('无法替换，请重试');
    }
  };

  // 保存选区并返回选中文本
  const saveSelection = () => {
    if (editorRef.current) {
      return editorRef.current.saveSelection();
    }
    return '';
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '18px' }}>
            ←
          </button>
          <h1>{docTitle} <small>{chapter ? `- ${chapter.title}` : ''}</small></h1>
        </div>
        <div className="header-actions">
          <button 
            className="save-btn" 
            onClick={handleExportChapter} 
            disabled={!chapter}
            style={{ backgroundColor: '#28a745', marginRight: '10px' }}
          >
            导出章节
          </button>
          <button 
            className="save-btn" 
            onClick={handleExportDocument} 
            disabled={!docId}
            style={{ backgroundColor: '#17a2b8', marginRight: '10px' }}
          >
            导出文档
          </button>
          <button className="save-btn" onClick={handleSave} disabled={saving || !chapter}>
            {saving ? '保存中...' : '保存'}
          </button>
        </div>
      </header>

      <div className="app-body">
        <Sidebar
          chapters={chapterList}
          currentChapterId={chapter?.id || null}
          onSelect={loadChapter}
          onCreate={handleCreateChapter}
          onDelete={handleDeleteChapter}
          onRename={handleRenameChapter}
          onMove={handleMoveChapter}
        />

        <main>
          {loading ? (
            <Loading fullscreen text="加载中..." />
          ) : chapter ? (
            <div className="word-editor-container">
              <ErrorBoundary>
                <Editor
                  ref={editorRef}
                  key={chapter.id} // 切换章节时强制重新渲染编辑器
                  html={chapter.html_content || ''}
                  onChange={handleEditorChange}
                  onSelectionChange={setSelectedText}
                  docId={docId}
                />
              </ErrorBoundary>
            </div>
          ) : (
            <div style={{ padding: 20, textAlign: 'center', color: '#999', marginTop: '100px' }}>
              <h3>没有选中的章节</h3>
              <p>请新建章节或从左侧选择章节开始写作</p>
            </div>
          )}
        </main>
      </div>

      {/* UI 组件 */}
      <Toast messages={toast.messages} onRemove={toast.removeToast} />
      <ConfirmDialog {...confirm.dialogProps} />
      <AIPanel 
        onAIEdit={handleAIEdit} 
        onInsert={handleAIInsert} 
        onReplace={handleAIReplace}
        saveSelection={saveSelection}
        selectedText={selectedText}
      />
    </div>
  )
}

export default DocumentEditor;
