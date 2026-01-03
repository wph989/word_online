import { useState, useEffect, useRef } from 'react';
import { Editor, Toolbar } from '@wangeditor/editor-for-react';
import { IDomEditor, IEditorConfig, IToolbarConfig } from '@wangeditor/editor';
import '@wangeditor/editor/dist/css/style.css';
import { EDITOR_DEFAULTS, getDisplayFontName } from '../config/editorDefaults';

interface EditorProps {
  html: string;
  onChange?: (html: string) => void;
  readOnly?: boolean;
}

export default function EditorComponent({ html, onChange, readOnly = false }: EditorProps) {
  const [editor, setEditor] = useState<IDomEditor | null>(null);
  const [showHint, setShowHint] = useState(true); // 控制默认样式提示条的显示
  const editorContainerRef = useRef<HTMLDivElement>(null);
  
  // 状态栏信息
  const [editorStatus, setEditorStatus] = useState({
    fontFamily: '默认字体',
    fontSize: '16px',
    lineHeight: '1.5'
  });

  // 工具栏配置
  const toolbarConfig: Partial<IToolbarConfig> = {
    excludeKeys: [
      'group-video'
    ]
  };

  // 编辑器配置
  const editorConfig: Partial<IEditorConfig> = {
    placeholder: '请输入内容...',
    readOnly,
    MENU_CONF: {
      uploadImage: {
        // 上传图片的服务器地址
        server: '/api/v1/upload/image',

        // 单个文件的最大体积限制，默认为 2M
        maxFileSize: 5 * 1024 * 1024, // 5M

        // 最多可上传几个文件，默认为 100
        maxNumberOfFiles: 10,

        // 选择文件时的类型限制，默认为 ['image/*']
        allowedFileTypes: ['image/*'],

        // 自定义上传参数，例如传递验证的 token 等
        meta: {
          // token: 'xxx',
        },

        // 将 meta 拼接到 url 参数中，默认 false
        metaWithUrl: false,

        // 自定义增加 http  header
        headers: {
          // Accept: 'text/x-json',
        },

        // 跨域是否传递 cookie ，默认为 false
        withCredentials: false,

        // 超时时间，默认为 10 秒
        timeout: 10 * 1000, // 10 秒

        // 上传之前触发
        onBeforeUpload(file: File) {
          console.log('上传图片前:', file);
          return file; // 返回 false 会阻止上传
        },

        // 上传进度的回调函数
        onProgress(progress: number) {
          console.log('上传进度:', progress);
        },

        // 单个文件上传成功之后
        onSuccess(file: File, res: any) {
          console.log('上传成功:', file.name, res);
        },

        // 单个文件上传失败
        onFailed(file: File, res: any) {
          console.error('上传失败:', file.name, res);
          alert(`图片 ${file.name} 上传失败`);
        },

        // 上传错误，或者触发 timeout 超时
        onError(file: File, err: any, res: any) {
          console.error('上传出错:', file.name, err, res);
          alert(`图片 ${file.name} 上传出错`);
        },

        // 自定义插入图片
        customInsert(res: any, insertFn: (url: string, alt: string, href: string) => void) {
          // res 即服务端的返回结果
          console.log('服务器返回:', res);

          // 从返回结果中获取图片 url
          const url = res.data?.url || res.url;
          const alt = res.data?.alt || '';
          const href = res.data?.href || '';

          if (url) {
            // 插入图片到编辑器
            insertFn(url, alt, href);
          } else {
            alert('上传成功但未返回图片地址');
          }
        },
      },
    },
  };

  // 从 DOM 提取表格列宽度并注入到 HTML
  const extractTableWidths = (currentHtml: string): string => {
    try {
      const editorContainer = editorContainerRef.current;
      if (!editorContainer) return currentHtml;

      const slateEditor = editorContainer.querySelector('[data-slate-editor]');
      if (!slateEditor) return currentHtml;

      const tables = slateEditor.querySelectorAll('table');
      if (tables.length === 0) return currentHtml;

      let modifiedHtml = currentHtml;

      tables.forEach((table, tableIndex) => {
        const firstRow = table.querySelector('tr');
        const cells = firstRow ? firstRow.querySelectorAll('th, td') : [];

        const colWidths: string[] = [];
        let hasRealWidths = false;

        // 提取每列的实际渲染宽度
        for (let i = 0; i < cells.length; i++) {
          const cell = cells[i];
          let width: string | null = null;

          if (cell) {
            const cellRect = cell.getBoundingClientRect();
            if (cellRect.width > 0) {
              width = Math.round(cellRect.width).toString();
            }
          }

          if (width) {
            colWidths.push(width);
            hasRealWidths = true;
          } else {
            colWidths.push('auto');
          }
        }

        // 如果有真实宽度，注入 colgroup
        if (hasRealWidths) {
          const colgroupHtml = '<colgroup>' +
            colWidths.map(w => `<col width="${w}">`).join('') +
            '</colgroup>';

          // 在第 N 个 table 标签后插入 colgroup
          let tableCount = 0;
          modifiedHtml = modifiedHtml.replace(/<table([^>]*)>/g, (match) => {
            if (tableCount === tableIndex) {
              tableCount++;
              return match + colgroupHtml;
            }
            tableCount++;
            return match;
          });
        }
      });

      return modifiedHtml;
    } catch (e) {
      console.warn('无法提取表格列宽度:', e);
      return currentHtml;
    }
  };

  // 监听外部 html 变化更新编辑器
  useEffect(() => {
    if (editor && html !== editor.getHtml()) {
      // 简化处理：只在初始化或切换章节时更新
    }
  }, [html, editor]);
  
  // 监听编辑器选区变化，更新状态栏
  useEffect(() => {
    if (!editor) return;
    
    const updateStatus = () => {
      try {
        // 获取编辑器容器中的当前选中元素
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) return;
        
        const range = selection.getRangeAt(0);
        let node = range.startContainer;
        
        // 如果是文本节点，获取其父元素
        if (node.nodeType === Node.TEXT_NODE) {
          node = node.parentElement!;
        }
        
        const computedStyle = window.getComputedStyle(node as Element);
        
        setEditorStatus({
          fontFamily: computedStyle.fontFamily.replace(/['"]/g, '') || '默认字体',
          fontSize: computedStyle.fontSize || '16px',
          lineHeight: computedStyle.lineHeight || '1.5'
        });
      } catch (e) {
        // 忽略错误
      }
    };
    
    // 初始更新
    updateStatus();
    
    // 监听选区变化
    editor.on('selectionChange', updateStatus);
    
    return () => {
      editor.off('selectionChange', updateStatus);
    };
  }, [editor]);

  // 组件销毁时，销毁编辑器
  useEffect(() => {
    return () => {
      if (editor) {
        editor.destroy();
        setEditor(null);
      }
    };
  }, [editor]);

  const handleChange = (editor: IDomEditor) => {
    let currentHtml = editor.getHtml();

    // 提取并注入表格列宽
    currentHtml = extractTableWidths(currentHtml);

    onChange?.(currentHtml);
  };

  return (
    <div ref={editorContainerRef} style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar
        editor={editor}
        defaultConfig={toolbarConfig}
        mode="default"
        style={{ borderBottom: '1px solid #e8e8e8' }}
      />
      
      {/* 默认样式显式提示条 - 可收起 */}
      {showHint ? (
        <div style={{
          backgroundColor: '#e6f7ff',
          borderBottom: '1px solid #91d5ff',
          padding: '8px 16px',
          fontSize: '13px',
          color: '#0050b3',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          transition: 'all 0.3s'
        }}>
          <span style={{ fontSize: '16px' }}>💡</span>
          <span><strong>文档默认样式：</strong></span>
          <span style={{ background: 'rgba(255,255,255,0.6)', padding: '2px 6px', borderRadius: '4px', border: '1px solid rgba(0,0,0,0.05)' }}>
            字体 {getDisplayFontName()}
          </span>
          <span style={{ background: 'rgba(255,255,255,0.6)', padding: '2px 6px', borderRadius: '4px', border: '1px solid rgba(0,0,0,0.05)' }}>
            字号 {EDITOR_DEFAULTS.fontSize}
          </span>
          <span style={{ background: 'rgba(255,255,255,0.6)', padding: '2px 6px', borderRadius: '4px', border: '1px solid rgba(0,0,0,0.05)' }}>
            行高 {EDITOR_DEFAULTS.lineHeight}
          </span>
          <span style={{ marginLeft: 'auto', color: '#69c0ff', fontSize: '12px' }}>* 当工具栏显示"默认"时即使用上述值</span>
          <span 
            onClick={() => setShowHint(false)} 
            style={{ 
              cursor: 'pointer', 
              marginLeft: '10px', 
              color: '#1890ff',
              display: 'flex',
              alignItems: 'center',
              userSelect: 'none'
            }}
            title="收起提示"
          >
            收起 🔼
          </span>
        </div>
      ) : (
        <div 
          onClick={() => setShowHint(true)}
          style={{
            backgroundColor: '#f0faff',
            borderBottom: '1px solid #e6f7ff',
            padding: '2px 16px',
            fontSize: '12px',
            color: '#91d5ff',
            cursor: 'pointer',
            textAlign: 'center',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '5px',
            transition: 'all 0.3s'
          }}
          title="展开默认样式提示"
        >
          <span>💡 默认样式: {getDisplayFontName()} / {EDITOR_DEFAULTS.fontSize} / {EDITOR_DEFAULTS.lineHeight}</span>
          <span>🔽</span>
        </div>
      )}
      <div style={{ flex: 1, overflowY: 'auto', position: 'relative' }}>
        <Editor
          defaultConfig={editorConfig}
          value={html}
          onCreated={setEditor}
          onChange={handleChange}
          mode="default"
          style={{ minHeight: '100%' }} // 移除 fixed height 和 overflow hidden，允许自动撑开
        />
      </div>
      
      {/* 状态栏 */}
      <div style={{
        borderTop: '1px solid #e8e8e8',
        padding: '6px 16px',
        fontSize: '12px',
        color: '#666',
        backgroundColor: '#fafafa',
        display: 'flex',
        alignItems: 'center',
        gap: '24px',
        boxShadow: '0 -1px 2px rgba(0,0,0,0.03)'
      }}>
        <span style={{ fontWeight: 600, color: '#1890ff' }}>当前实际渲染:</span>
        <span title="字体">🔤 {editorStatus.fontFamily.split(',')[0].replace(/['"]/g, '')}</span>
        <span title="字号">📏 {editorStatus.fontSize}</span>
        <span title="行高">↕️ {editorStatus.lineHeight}</span>
        <span style={{ marginLeft: 'auto', color: '#999' }}>（未设置样式时使用默认值：微软雅黑, 16px, 1.5）</span>
      </div>
    </div>
  );
}
