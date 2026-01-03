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
  
  // 页面边距状态 (单位: px)
  const [pageMargins, setPageMargins] = useState({
    top: 40,
    bottom: 40,
    left: 50,
    right: 50
  });

  // 标题样式状态 (H1-H6)
  const [headingStyles, setHeadingStyles] = useState({
    h1: { fontSize: 24, fontWeight: 'bold', color: '#1890ff', marginTop: 24, marginBottom: 12 },
    h2: { fontSize: 22, fontWeight: 'bold', color: '#333333', marginTop: 20, marginBottom: 10 },
    h3: { fontSize: 20, fontWeight: 'bold', color: '#333333', marginTop: 16, marginBottom: 8 },
    h4: { fontSize: 18, fontWeight: 'bold', color: '#333333', marginTop: 14, marginBottom: 6 },
    h5: { fontSize: 16, fontWeight: 'bold', color: '#333333', marginTop: 12, marginBottom: 4 },
    h6: { fontSize: 14, fontWeight: 'bold', color: '#666666', marginTop: 10, marginBottom: 2 },
  });

  const [showPageSettings, setShowPageSettings] = useState(false);
  
  const editorContainerRef = useRef<HTMLDivElement>(null);
  
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
        server: '/api/v1/upload/image',
        maxFileSize: 5 * 1024 * 1024,
        maxNumberOfFiles: 10,
        allowedFileTypes: ['image/*'],
        metaWithUrl: false,
        withCredentials: false,
        timeout: 10 * 1000,
        onBeforeUpload(file: File) {
          return file;
        },
        customInsert(res: any, insertFn: (url: string, alt: string, href: string) => void) {
          const url = res.data?.url || res.url;
          if (url) insertFn(url, '', '');
        },
      },
    },
  };
  
  // 生成动态样式标签
  const renderDynamicStyles = () => (
    <style>{`
      /* 动态注入标题样式 H1-H6 */
      ${['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].map(tag => {
        // @ts-ignore
        const style = headingStyles[tag];
        return `
          /* 1. 应用到标题容器 */
          .w-e-text-container [data-slate-editor] ${tag},
          .w-e-text-container .w-e-scroll ${tag},
          .w-e-text-container ${tag} {
            font-size: ${style.fontSize}px !important;
            font-weight: ${style.fontWeight} !important;
            color: ${style.color} !important;
            margin-top: ${style.marginTop}px !important;
            margin-bottom: ${style.marginBottom}px !important;
            line-height: 1.5 !important;
          }

          /* 2. 强制标题内部所有子元素继承父级样式 (解决内联样式冲突) */
          .w-e-text-container [data-slate-editor] ${tag} *,
          .w-e-text-container .w-e-scroll ${tag} *,
          .w-e-text-container ${tag} * {
            font-size: inherit !important;
            font-weight: inherit !important;
            color: inherit !important;
            background-color: transparent !important; /* 可选：清除背景色干扰 */
          }
        `;
      }).join('\n')}
    `}</style>
  );

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
      // 移除可能存在的旧 metadata
      modifiedHtml = modifiedHtml.replace(/<div id="doc-settings".*?><\/div>/, '');

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

  // 监听外部 html 变化更新编辑器 (包含解析页面设置)
  useEffect(() => {
    if (editor && html) {
      // 1. 尝试解析页面设置元数据
      try {
        const match = html.match(/<div id="doc-settings".*?data-settings='(.*?)'.*?><\/div>/);
        if (match && match[1]) {
           let settingsStr = match[1];
           let settings;
           try {
              // 尝试 Base64 解码
              const decoded = atob(settingsStr);
              settings = JSON.parse(decoded);
           } catch {
              // 不是 Base64，尝试直接解析
              settings = JSON.parse(settingsStr); 
           }
           
           if (settings) {
             if (settings.margins) setPageMargins(settings.margins);
             if (settings.headingStyles) setHeadingStyles(settings.headingStyles);
           }
        }
      } catch (e) {
        console.error('解析页面设置失败:', e);
      }

      // 2. 剥离元数据后设置给编辑器
      // 注意：必须非常小心地比较，以避免死循环和重置光标
      const cleanHtml = html.replace(/<div id="doc-settings".*?><\/div>/g, '');
      
      try {
        const currentContent = editor.getHtml().replace(/<div id="doc-settings".*?><\/div>/g, '');
        if (cleanHtml !== currentContent) {
           // 只有在内容确实不同且编辑器可用时才更新
           // @ts-ignore - 检查私有属性或捕获错误
           if (!editor.isDestroyed) {
             editor.setHtml(cleanHtml);
           }
        }
      } catch (e) {
        console.warn('更新编辑器内容时出错 (通常可忽略):', e);
      }
    }
  }, [html, editor]);

  // 组件销毁时，销毁编辑器
  useEffect(() => {
    return () => {
      if (editor) {
        try {
            editor.destroy();
        } catch(e) {
            // ignore destroy errors
        }
        setEditor(null);
      }
    };
  }, [editor]);

  const handleChange = (editor: IDomEditor) => {
    let currentHtml = editor.getHtml();
    
    // 移除编辑器可能包含的旧 metadata (防止重复)
    currentHtml = currentHtml.replace(/<div id="doc-settings".*?><\/div>/g, '');

    // 1. 提取并注入表格列宽
    currentHtml = extractTableWidths(currentHtml);
    
    // 2. 序列化并注入页面设置
    const settings = {
      margins: pageMargins,
      headingStyles: headingStyles
    };
    try {
      // 使用 Base64 编码避免 HTML 属性转义问题
      const settingsStr = btoa(JSON.stringify(settings));
      const metadataHtml = `<div id="doc-settings" style="display:none" data-settings='${settingsStr}'></div>`;
      currentHtml = metadataHtml + currentHtml;
    } catch (e) {
      console.error('序列化页面设置失败:', e);
    }

    onChange?.(currentHtml);
  };

  return (
    <div 
      ref={editorContainerRef} 
      style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: '100%',
        // 注入 CSS 变量
        // @ts-ignore
        '--page-margin-top': `${pageMargins.top}px`,
        '--page-margin-right': `${pageMargins.right}px`,
        '--page-margin-bottom': `${pageMargins.bottom}px`,
        '--page-margin-left': `${pageMargins.left}px`
      }}
    >
      {renderDynamicStyles()}
      <div style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid #e8e8e8' }}>
        <div style={{ flex: 1 }}>
          <Toolbar
            editor={editor}
            defaultConfig={toolbarConfig}
            mode="default"
            style={{ borderBottom: 'none' }}
          />
        </div>
        <button 
          onClick={() => setShowPageSettings(!showPageSettings)}
          style={{
            padding: '5px 15px',
            margin: '0 10px',
            border: '1px solid #d9d9d9',
            background: showPageSettings ? '#e6f7ff' : '#fff',
            color: showPageSettings ? '#1890ff' : '#666',
            cursor: 'pointer',
            borderRadius: '4px',
            fontSize: '13px',
            whiteSpace: 'nowrap'
          }}
        >
           🛠️ 文档设置
        </button>
      </div>

      {/* 文档设置面板 */}
      {showPageSettings && (
        <div style={{
          padding: '16px 20px',
          background: '#fafafa',
          borderBottom: '1px solid #e8e8e8',
          fontSize: '13px',
          color: '#333',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          maxHeight: '300px',
          overflowY: 'auto'
        }}>
          {/* 页边距区域 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
            <strong style={{ minWidth: '80px' }}>页边距 (px):</strong>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label>上:</label>
              <input type="number" value={pageMargins.top} onChange={e => setPageMargins({...pageMargins, top: Number(e.target.value)})} style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label>下:</label>
              <input type="number" value={pageMargins.bottom} onChange={e => setPageMargins({...pageMargins, bottom: Number(e.target.value)})} style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label>左:</label>
              <input type="number" value={pageMargins.left} onChange={e => setPageMargins({...pageMargins, left: Number(e.target.value)})} style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label>右:</label>
              <input type="number" value={pageMargins.right} onChange={e => setPageMargins({...pageMargins, right: Number(e.target.value)})} style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} />
            </div>
          </div>

          {/* 标题样式区域 */}
          {[
            { key: 'h1', label: '一级标题 (H1)' },
            { key: 'h2', label: '二级标题 (H2)' },
            { key: 'h3', label: '三级标题 (H3)' },
            { key: 'h4', label: '四级标题 (H4)' },
            { key: 'h5', label: '五级标题 (H5)' },
            { key: 'h6', label: '六级标题 (H6)' }
          ].map(h => (
            //@ts-ignore
            <div key={h.key} style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <strong style={{ minWidth: '80px' }}>{h.label}:</strong>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span>字号</span>
                <input 
                  type="number" 
                  //@ts-ignore
                  value={headingStyles[h.key].fontSize} 
                  //@ts-ignore
                  onChange={e => setHeadingStyles({...headingStyles, [h.key]: { ...headingStyles[h.key], fontSize: Number(e.target.value) }})}
                  style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} 
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span>颜色</span>
                <input 
                  type="color" 
                  //@ts-ignore
                  value={headingStyles[h.key].color} 
                  //@ts-ignore
                  onChange={e => setHeadingStyles({...headingStyles, [h.key]: { ...headingStyles[h.key], color: e.target.value }})}
                  style={{ width: '40px', padding: '0', border: 'none', background: 'none', cursor: 'pointer' }} 
                />
              </div>
               <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span>加粗</span>
                <input 
                  type="checkbox" 
                  //@ts-ignore
                  checked={headingStyles[h.key].fontWeight === 'bold'} 
                  //@ts-ignore
                  onChange={e => setHeadingStyles({...headingStyles, [h.key]: { ...headingStyles[h.key], fontWeight: e.target.checked ? 'bold' : 'normal' }})}
                />
              </div>
               <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span>段前/后</span>
                <input 
                  type="number" 
                  //@ts-ignore
                  value={headingStyles[h.key].marginTop} 
                  //@ts-ignore
                  onChange={e => setHeadingStyles({...headingStyles, [h.key]: { ...headingStyles[h.key], marginTop: Number(e.target.value) }})}
                  style={{ width: '40px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} 
                  title="段前距"
                />
                <input 
                  type="number" 
                  //@ts-ignore
                  value={headingStyles[h.key].marginBottom} 
                  //@ts-ignore
                  onChange={e => setHeadingStyles({...headingStyles, [h.key]: { ...headingStyles[h.key], marginBottom: Number(e.target.value) }})}
                  style={{ width: '40px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} 
                  title="段后距"
                />
              </div>
            </div>
          ))}

          <button 
            onClick={() => {
              setPageMargins({ top: 40, bottom: 40, left: 50, right: 50 });
              setHeadingStyles({
                h1: { fontSize: 24, fontWeight: 'bold', color: '#333333', marginTop: 24, marginBottom: 12 },
                h2: { fontSize: 22, fontWeight: 'bold', color: '#333333', marginTop: 20, marginBottom: 10 },
                h3: { fontSize: 20, fontWeight: 'bold', color: '#333333', marginTop: 16, marginBottom: 8 },
                h4: { fontSize: 18, fontWeight: 'bold', color: '#333333', marginTop: 14, marginBottom: 6 },
                h5: { fontSize: 16, fontWeight: 'bold', color: '#333333', marginTop: 12, marginBottom: 4 },
                h6: { fontSize: 14, fontWeight: 'bold', color: '#333333', marginTop: 10, marginBottom: 2 },
              });
            }}
            style={{ 
              alignSelf: 'flex-start',
              padding: '6px 16px', 
              background: '#fff', 
              border: '1px solid #d9d9d9', 
              cursor: 'pointer',
              borderRadius: '4px',
              color: '#666',
              marginTop: '10px'
            }}
          >
            重置所有设置
          </button>
        </div>
      )}
      
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
      <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
        <Editor
          defaultConfig={editorConfig}
          value={html}
          onCreated={setEditor}
          onChange={handleChange}
          mode="default"
          style={{ minHeight: '100%', overflowY: 'hidden' }}
        />
      </div>
    </div>
  );
}
