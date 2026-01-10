import React, { useState, useRef } from 'react';
import './ImportDocxModal.css';

interface ImportDocxModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (file: File, options: ImportOptions) => Promise<void>;
}

interface ImportOptions {
  maxHeadingLevel: number;
  documentTitle: string;
}

const ImportDocxModal: React.FC<ImportDocxModalProps> = ({ isOpen, onClose, onImport }) => {
  const [file, setFile] = useState<File | null>(null);
  const [maxHeadingLevel, setMaxHeadingLevel] = useState(2);
  const [documentTitle, setDocumentTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      // 使用文件名作为默认文档标题
      if (!documentTitle) {
        setDocumentTitle(selectedFile.name.replace(/\.docx$/i, ''));
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.name.toLowerCase().endsWith('.docx')) {
      setFile(droppedFile);
      if (!documentTitle) {
        setDocumentTitle(droppedFile.name.replace(/\.docx$/i, ''));
      }
    }
  };

  const handleImport = async () => {
    if (!file) return;
    
    setLoading(true);
    try {
      await onImport(file, {
        maxHeadingLevel,
        documentTitle: documentTitle || file.name.replace(/\.docx$/i, '')
      });
      // 成功后重置状态
      setFile(null);
      setDocumentTitle('');
      setMaxHeadingLevel(2);
    } catch (error) {
      // 错误处理由父组件负责
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setFile(null);
      setDocumentTitle('');
      setMaxHeadingLevel(2);
      onClose();
    }
  };

  return (
    <div className="import-modal-overlay" onClick={handleClose}>
      <div className="import-modal" onClick={e => e.stopPropagation()}>
        <div className="import-modal-header">
          <h3>📥 导入 Word 文档</h3>
          <button className="import-modal-close" onClick={handleClose} disabled={loading}>
            ✕
          </button>
        </div>
        
        <div className="import-modal-body">
          {/* 文件拖放区域 */}
          <div 
            className={`import-dropzone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".docx"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            {file ? (
              <div className="file-info">
                <span className="file-icon">📄</span>
                <span className="file-name">{file.name}</span>
                <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
              </div>
            ) : (
              <div className="dropzone-hint">
                <span className="upload-icon">📂</span>
                <p>拖拽文件到此处，或点击选择文件</p>
                <p className="hint-sub">仅支持 .docx 格式</p>
              </div>
            )}
          </div>

          {/* 导入选项 */}
          <div className="import-options">
            <div className="option-group">
              <label htmlFor="docTitle">文档标题</label>
              <input
                id="docTitle"
                type="text"
                value={documentTitle}
                onChange={e => setDocumentTitle(e.target.value)}
                placeholder="默认使用文件名"
              />
            </div>
            
            <div className="option-group">
              <label htmlFor="headingLevel">章节标题级别</label>
              <select
                id="headingLevel"
                value={maxHeadingLevel}
                onChange={e => setMaxHeadingLevel(Number(e.target.value))}
              >
                <option value={1}>仅 H1 创建章节</option>
                <option value={2}>H1 + H2 创建章节</option>
                <option value={3}>H1 ~ H3 创建章节</option>
                <option value={4}>H1 ~ H4 创建章节</option>
                <option value={5}>H1 ~ H5 创建章节</option>
                <option value={6}>所有标题创建章节</option>
              </select>
              <p className="option-hint">
                选定级别的标题将作为独立章节，更高级别的标题作为章节内容
              </p>
            </div>
          </div>
        </div>

        <div className="import-modal-footer">
          <button 
            className="import-btn-cancel" 
            onClick={handleClose}
            disabled={loading}
          >
            取消
          </button>
          <button 
            className="import-btn-confirm"
            onClick={handleImport}
            disabled={!file || loading}
          >
            {loading ? '导入中...' : '开始导入'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ImportDocxModal;
