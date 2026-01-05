/**
 * AI 编辑面板组件
 * 浮动在编辑器右侧，提供 AI 辅助功能
 */

import { useState, useEffect, useRef } from 'react';
import './AIPanel.css';

import { AI_ACTIONS } from '../constants/aiActions';

export interface AIPanelProps {
  onAIEdit: (action: string, text: string) => Promise<string>;
  onInsert: (text: string) => void;
  onReplace: (text: string) => void;
  saveSelection: () => string;
  selectedText?: string; // 实时选中文本
}

export default function AIPanel({ onAIEdit: _onAIEdit, onInsert, onReplace, saveSelection, selectedText: externalSelectedText }: AIPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'edit' | 'generate'>('edit');
  const [inputText, setInputText] = useState('');
  const [customPrompt, setCustomPrompt] = useState(''); // 自定义指令
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [hasSelection, setHasSelection] = useState(false); // 是否有选区

  // 用于取消请求
  const abortControllerRef = useRef<AbortController | null>(null);

  // 处理选中文本的更新（合并两个 useEffect）
  useEffect(() => {
    if (!isOpen) return;

    // 如果有外部传入的选中文本，直接使用
    if (externalSelectedText) {
      setInputText(externalSelectedText);
      setHasSelection(true);
      return;
    }

    // 否则尝试从编辑器获取
    const selectedText = saveSelection();
    if (selectedText) {
      setInputText(selectedText);
      setHasSelection(true);
    } else {
      setHasSelection(false);
    }
  }, [isOpen, externalSelectedText, saveSelection]);

  // 从编辑器获取选中文本
  const handleGetSelection = () => {
    const text = saveSelection();
    if (text) {
      setInputText(text);
      setHasSelection(true);
    } else {
      alert('请先在编辑器中选中文本');
    }
  };

  // 通用流式请求处理
  const streamAIEdit = async (action: string, text: string, style?: string) => {
    if (!text.trim() || loading) return;

    // 如果有正在进行的请求，先取消
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setResult(''); // 清空上次结果

    try {
      const response = await fetch('/api/v1/ai/edit/stream/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          action,
          style
        }),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.error) throw new Error(data.error);
              // 处理流式文本片段
              if (data.text) {
                setResult(prev => prev + data.text);
              }
            } catch (e) {
              // 忽略部分解析错误（因为chunk可能被截断）
            }
          }
        }
      }

    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Request aborted');
      } else {
        console.error('AI 操作失败:', error);
        setResult(prev => prev + '\n[AI 处理失败，请重试]');
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleCustomAction = async () => {
    if (!customPrompt.trim()) return;
    await streamAIEdit('custom', inputText, customPrompt);
  };

  const handleAction = async (actionId: string) => {
    await streamAIEdit(actionId, inputText);
  };

  // 替换原文本（插入到选区位置）
  const handleReplace = () => {
    if (result) {
      onReplace(result);
      setResult('');
      setInputText('');
      setHasSelection(false);
    }
  };

  // 追加到文档末尾
  const handleInsert = () => {
    if (result) {
      onInsert(result);
      setResult('');
      setInputText('');
    }
  };

  // 复制结果到剪贴板
  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(result)
        .then(() => alert('已复制到剪贴板'))
        .catch(() => alert('复制失败'));
    }
  };

  const handleGenerate = async () => {
    // 生成模式默认使用 'expand' 动作，或者可以扩展后端支持 'generate' 动作
    // 这里暂时复用 expand，或者可以在 constants 增加 'generate' action
    await streamAIEdit('expand', inputText || '请帮我写一段关于...');
  };

  return (
    <>
      {/* 触发按钮 */}
      <button
        className={`ai-panel-trigger ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        title="AI 助手"
      >
        🤖 AI
      </button>

      {/* AI 面板 */}
      {isOpen && (
        <div className="ai-panel">
          <div className="ai-panel-header">
            <h3>🤖 AI 写作助手</h3>
            <button className="ai-panel-close" onClick={() => setIsOpen(false)}>
              ×
            </button>
          </div>

          {/* 标签切换 */}
          <div className="ai-panel-tabs">
            <button
              className={`ai-tab ${activeTab === 'edit' ? 'active' : ''}`}
              onClick={() => setActiveTab('edit')}
            >
              ✏️ 编辑文本
            </button>
            <button
              className={`ai-tab ${activeTab === 'generate' ? 'active' : ''}`}
              onClick={() => setActiveTab('generate')}
            >
              ✨ 生成内容
            </button>
          </div>

          <div className="ai-panel-body">
            {activeTab === 'edit' ? (
              <>
                {/* 编辑模式 */}
                <div className="ai-input-section">
                  <div className="ai-input-header">
                    <label>输入或粘贴要编辑的文本:</label>
                    <button
                      className="ai-get-selection-btn"
                      onClick={handleGetSelection}
                      title="从编辑器获取选中文本"
                    >
                      📋 获取选中文本
                    </button>
                  </div>
                  <textarea
                    className="ai-textarea"
                    value={inputText}
                    onChange={(e) => {
                      setInputText(e.target.value);
                      setHasSelection(false); // 手动编辑后，取消选区标记
                    }}
                    placeholder="在此输入或粘贴文本..."
                    rows={6}
                  />
                  {hasSelection && (
                    <small className="ai-selection-hint">
                      ✓ 已获取编辑器选中文本，AI 处理后可直接替换
                    </small>
                  )}
                </div>

                <div className="ai-actions-grid">
                  {AI_ACTIONS.map((action) => (
                    <button
                      key={action.id}
                      className="ai-action-card"
                      onClick={() => handleAction(action.id)}
                      disabled={!inputText.trim() || loading}
                      title={action.description}
                    >
                      <span className="ai-action-icon">{action.icon}</span>
                      <span className="ai-action-name">{action.name}</span>
                    </button>
                  ))}
                </div>

                {/* 自定义指令区域 */}
                <div className="ai-custom-section">
                  <input
                    type="text"
                    className="ai-custom-input"
                    placeholder="例如: 翻译成日语、使语气更委婉..."
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleCustomAction();
                    }}
                  />
                  <button
                    className="ai-custom-btn"
                    onClick={handleCustomAction}
                    disabled={!customPrompt.trim() || loading}
                  >
                    发送
                  </button>
                </div>
              </>
            ) : (
              <>
                {/* 生成模式 */}
                <div className="ai-input-section">
                  <label>描述你想要生成的内容:</label>
                  <textarea
                    className="ai-textarea"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="例如: 写一段关于人工智能发展的介绍..."
                    rows={4}
                  />
                  <button
                    className="ai-generate-btn"
                    onClick={handleGenerate}
                    disabled={loading}
                  >
                    {loading ? '生成中...' : '🚀 生成内容'}
                  </button>
                </div>
              </>
            )}

            {/* 加载状态 */}
            {loading && (
              <div className="ai-loading">
                <div className="ai-loading-spinner"></div>
                <span>AI 处理中，请稍候...</span>
              </div>
            )}

            {/* 结果显示 */}
            {result && (
              <div className="ai-result-section">
                <div className="ai-result-header">
                  <label>AI 处理结果:</label>
                  <div className="ai-result-actions">
                    <button className="ai-copy-btn" onClick={handleCopy} title="复制内容">
                      📋
                    </button>
                    {hasSelection && (
                      <button className="ai-replace-btn" onClick={handleReplace}>
                        🔄 替换原文
                      </button>
                    )}
                    <button className="ai-insert-btn" onClick={handleInsert}>
                      📥 插入到末尾
                    </button>
                  </div>
                </div>
                <div className="ai-result-text">{result}</div>
              </div>
            )}
          </div>

          {/* 提示信息 */}
          <div className="ai-panel-footer">
            <small>💡 提示: 先在编辑器中选中文本，再点击"获取选中文本"按钮</small>
          </div>
        </div>
      )}
    </>
  );
}
