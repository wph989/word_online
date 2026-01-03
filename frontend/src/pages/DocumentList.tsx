import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { chapterService } from '../services/chapterService';
import './DocumentList.css';

const DocumentList: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  // const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadDocs();
  }, [page]);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const res = await chapterService.getDocumentsList(page, 10);
      setDocuments(res.items); // setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    const title = prompt('请输入文档标题', '新文档');
    if (title) {
      try {
        const newDoc = await chapterService.createDocument(title);
        // 创建成功后直接跳转
        navigate(`/doc/${newDoc.id}`);
      } catch (e) {
        alert('创建失败');
      }
    }
  };

  return (
    <div className="doc-list-container">
      <div className="doc-list-header">
        <h2>我的文档</h2>
        <button className="primary-btn" onClick={handleCreate}>新建文档</button>
      </div>
      
      {loading ? <div>加载中...</div> : (
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
                <button 
                  className="doc-action-btn"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    chapterService.exportDocumentToDocx(doc.id);
                  }}
                >
                  导出 Word
                </button>
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
    </div>
  );
};

export default DocumentList;
