import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Editor from '../components/Editor'
import Sidebar from '../components/Sidebar'
import ErrorBoundary from '../components/ErrorBoundary'
import type { Chapter } from '../types/api'
import { chapterService } from '../services/chapterService'

interface ChapterMeta {
  id: string;
  title: string;
  orderIndex: number;
}

const DocumentEditor: React.FC = () => {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();

  const [docTitle, setDocTitle] = useState('');
  const [chapterList, setChapterList] = useState<ChapterMeta[]>([]);
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // 临时存储编辑器内容，用于保存
  const [currentHtml, setCurrentHtml] = useState('');

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
        orderIndex: c.order_index || 0
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
      // alert('加载失败');
    } finally {
      setLoading(false);
    }
  };

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
    }
  };

  const handleCreateChapter = async () => {
    if (!docId) return;
    try {
      const newChapter = await chapterService.createChapter(
        `新章节 ${chapterList.length + 1}`,
        docId
      );
      const newMeta = {
        id: newChapter.id,
        title: newChapter.title,
        orderIndex: newChapter.order_index || 0
      };
      setChapterList(prev => [...prev, newMeta]);

      // 自动选中新章节
      setChapter(newChapter);
      setCurrentHtml(newChapter.html_content || '');
    } catch (e) {
      alert("创建章节失败");
    }
  };

  const handleDeleteChapter = async (id: string) => {
    try {
      await chapterService.deleteChapter(id);
      const newList = chapterList.filter(c => c.id !== id);
      setChapterList(newList);

      if (chapter && chapter.id === id) {
        if (newList.length > 0) {
          loadChapter(newList[0].id);
        } else {
          setChapter(null);
          setCurrentHtml('');
        }
      }
    } catch (e) {
      alert("删除失败");
    }
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
    } catch (e) {
      alert("重命名失败");
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
      // 保存后重新加载以获取后端渲染的HTML
      await loadChapter(chapter.id);
    } catch (err) {
      alert('保存失败');
    } finally {
      setSaving(false);
    }
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
            onClick={() => chapter && chapterService.exportChapterToDocx(chapter.id)} 
            disabled={!chapter}
            style={{ backgroundColor: '#28a745', marginRight: '10px' }}
          >
            导出章节
          </button>
          <button 
            className="save-btn" 
            onClick={() => docId && chapterService.exportDocumentToDocx(docId)} 
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
        />

        <main>
          {loading ? (
            <div style={{ padding: 20 }}>Loading...</div>
          ) : chapter ? (
            <div className="word-editor-container">
              <ErrorBoundary>
                <Editor
                  key={chapter.id} // 切换章节时强制重新渲染编辑器
                  html={chapter.html_content || ''}
                  onChange={handleEditorChange}
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
    </div>
  )
}

export default DocumentEditor;
