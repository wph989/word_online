import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { chapterService } from '../services/chapterService';
import Toast, { useToast } from '../components/Toast';
import { DocumentListSkeleton } from '../components/Loading';
import ConfirmDialog, { useConfirmDialog } from '../components/ConfirmDialog';
import ImportDocxModal from '../components/ImportDocxModal';
import './DocumentList.css';

const DocumentList: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showImportModal, setShowImportModal] = useState(false);
  const navigate = useNavigate();
  
  // UI 组件 Hooks
  const toast = useToast();
  const confirm = useConfirmDialog();

  useEffect(() => {
    loadDocs();
  }, [page]);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const res = await chapterService.getDocumentsList(page, 10);
      setDocuments(res.items);
    } catch (err) {
      console.error(err);
      toast.error('加载文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    const title = prompt('请输入文档标题', '新文档');
    if (title) {
      try {
        const newDoc = await chapterService.createDocument(title);
        toast.success('文档创建成功');
        // 创建成功后直接跳转
        navigate(`/doc/${newDoc.id}`);
      } catch (e) {
        toast.error('创建文档失败');
      }
    }
  };

  const handleImport = async (file: File, options: { maxHeadingLevel: number; documentTitle: string }) => {
    try {
      const result = await chapterService.importDocx(file, {
        maxHeadingLevel: options.maxHeadingLevel,
        documentTitle: options.documentTitle
      });

      toast.success(result.message);
      setShowImportModal(false);

      // 导入成功后跳转到新文档
      navigate(`/doc/${result.doc_id}`);
    } catch (error: any) {
      const message = error.response?.data?.detail || '导入失败，请检查文件格式';
      toast.error(message);
      throw error; // 重新抛出以便模态框保持打开状态
    }
  };

  const handleDelete = (doc: any) => {
    confirm.confirmDelete(doc.title, async () => {
      try {
        await chapterService.deleteDocument(doc.id);
        toast.success('文档已删除');
        loadDocs(); // 重新加载列表
      } catch (e) {
        toast.error('删除失败');
      }
    });
  };

  const handleExport = async (e: React.MouseEvent, doc: any) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      chapterService.exportDocumentToDocx(doc.id);
      toast.success('导出成功');
    } catch (e) {
      toast.error('导出失败');
    }
  };

  return (
    <div className="doc-list-container">
      <div className="doc-list-header">
        <h2>我的文档</h2>
        <div className="header-actions">
          <button className="secondary-btn" onClick={() => setShowImportModal(true)}>
            📥 导入 Word
          </button>
          <button className="primary-btn" onClick={handleCreate}>新建文档</button>
        </div>
      </div>
      
      {loading ? (
        <DocumentListSkeleton />
      ) : (
        <div className="doc-grid">
          {documents.map(doc => (
            <Link to={`/doc/${doc.id}`} key={doc.id} className="doc-card">
              <div className="doc-icon">📄</div>
              <div className="doc-info">
                <h3>{doc.title}</h3>
                <p>ID: {doc.id}</p>
                <p style={{marginTop: 5, fontSize: 10}}>
                  {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : ''}
                </p>
                <div className="doc-actions">
                  <button 
                    className="doc-action-btn"
                    onClick={(e) => handleExport(e, doc)}
                  >
                    导出 Word
                  </button>
                  <button 
                    className="doc-action-btn doc-delete-btn"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleDelete(doc);
                    }}
                  >
                    删除
                  </button>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
      
      {/* 简单分页 */}
      <div className="pagination">
        <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>上一页</button>
        <span>第 {page} 页</span>
        <button disabled={documents.length < 10} onClick={() => setPage(p => p + 1)}>下一页</button>
      </div>

      {/* DOCX 导入模态框 */}
      <ImportDocxModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImport={handleImport}
      />

      {/* UI 组件 */}
      <Toast messages={toast.messages} onRemove={toast.removeToast} />
      <ConfirmDialog {...confirm.dialogProps} />
    </div>
  );
};

export default DocumentList;

