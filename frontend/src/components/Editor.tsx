import { useState, useEffect, useRef } from 'react';
import { Editor, Toolbar } from '@wangeditor/editor-for-react';
import { Boot, ISelectMenu, IDomEditor, IEditorConfig, IToolbarConfig, DomEditor } from '@wangeditor/editor';
import '@wangeditor/editor/dist/css/style.css';
import { EDITOR_DEFAULTS, WORD_FONT_SIZES, FONT_FAMILY_OPTIONS } from '../config/editorDefaults';
import { settingsService } from '../services/api';



/**
 * 辅助函数：获取当前选区应用的样式（优先 Mark，其次 Block 默认配置，最后全局默认）
 * @param editor 编辑器实例
 * @param styleKey 样式属性名
 * @param defaultValue 全局默认值
 */
function getActiveStyle(editor: IDomEditor, styleKey: 'fontSize' | 'fontFamily' | 'lineHeight', defaultValue: string): string {
    // 1. 优先获取 Mark (内联样式) - 仅针对 fontSize/fontFamily
    if (styleKey !== 'lineHeight') {
        // @ts-ignore
        const markValue = editor.marks ? editor.marks[styleKey] : null;
        if (markValue) return markValue;
    }

    // 2. 如果没有 Mark，检查是否是标题 Block，并获取其默认配置
    // WangEditor 的标题 type 为 'header1' ~ 'header5'
    for (let i = 1; i <= 6; i++) {
        const type = `header${i}`;
        const node = DomEditor.getSelectedNodeByType(editor, type);
        if (node) {
            // 找到标题节点，查找对应的配置
            // @ts-ignore
            const headingStyles = editor.headingStyles;
            if (headingStyles) {
                const hKey = `h${i}`;
                const styleConfig = headingStyles[hKey];
                if (styleConfig) {
                    if (styleKey === 'fontSize') {
                        return `${styleConfig.fontSize}pt`;
                    } else if (styleKey === 'fontFamily') {
                        return styleConfig.fontFamily;
                    } else if (styleKey === 'lineHeight') {
                        return '1.5'; // 标题默认行高
                    }
                }
            }
            break; // 找到即止
        }
    }
    
    // 2.5 如果是行高，还需要检查普通段落的行高设置 (WangEditor 将其存储在节点属性中)
    if (styleKey === 'lineHeight') {
        const node = DomEditor.getSelectedNodeByType(editor, 'paragraph');
        if (node) {
            // @ts-ignore
            if (node.lineHeight) return node.lineHeight;
        }
        // check headers too if not handled above properly (though steps above handle config)
        // headers with manual line height?
        for (let i = 1; i <= 6; i++) {
            const node = DomEditor.getSelectedNodeByType(editor, `header${i}`);
            // @ts-ignore
            if (node && node.lineHeight) return node.lineHeight;
        }
    }

    // 3. 尝试获取 DOM 计算样式 (所见即所得)
    // 这能确保即使在普通段落或继承样式的情况下，也能显示真实的字体/字号
    try {
        const selection = window.getSelection();
        if (selection && selection.rangeCount > 0) {
            let node = selection.getRangeAt(0).commonAncestorContainer;
            if (node.nodeType === 3) node = node.parentElement!; // 文本节点 -> 父元素
            
            if (node instanceof HTMLElement) {
                // 3.1 优先检查内联 style 属性 (Raw Value)
                // 这能避免浏览器 fallback 导致的字体不一致 (例如用户设置了 'YouYuan' 但系统显示 'Microsoft YaHei')
                // 也能更准确地捕捉到用户的设置意图
                const inlineStyle = node.style[styleKey as any];
                if (inlineStyle) return inlineStyle;

                // 3.2 回退到计算样式 (Computed Value)
                const computed = window.getComputedStyle(node);
                const val = computed[styleKey as any];
                if (val) {
                    if (styleKey === 'lineHeight') {
                         // 计算样式返回可能是 "normal" 或 px 值，处理起来比较麻烦
                         // 如果是 normal，返回默认值
                         if (val === 'normal') return defaultValue;
                         // 如果是 px，尝试转换成倍数? 太复杂，暂且忽略 px 返回，依赖 defaultValue
                         // 或者如果是纯数字字符串，直接返回
                         if (!isNaN(Number(val))) return val;
                    } else {
                        return val;
                    }
                }
            }
        }
    } catch (e) {
        // 忽略 DOM 访问错误
    }

    // 4. 返回全局默认值
    return defaultValue;
}


// 自定义字号菜单
class WordFontSizeMenu implements ISelectMenu {
  readonly title = '字号'
  readonly tag = 'select'
  readonly width = 80
  
  // 选项列表
  getOptions(_editor: IDomEditor) {
    return WORD_FONT_SIZES.map(opt => ({
      value: opt.value,
      text: opt.label,
      selected: false // 获取值时会自动判断
    }))
  }

  // 获取当前值
  getValue(editor: IDomEditor): string | boolean {
    let val = getActiveStyle(editor, 'fontSize', '12pt');
    
    if (!val) return '12pt';
    
    val = val.toString().toLowerCase();
    
    // 兼容性处理：如果是 px，尝试转换为 pt 以匹配菜单选项
    if (val.includes('px')) {
        const num = parseFloat(val);
        if (!isNaN(num)) {
            // 1px ≈ 0.75pt
            const pt = num * 0.75;
            // 构造 pt 字符串，例如 "12pt" 或 "10.5pt"
            const ptStr = `${Number(pt.toFixed(2))}pt`; 
            
            // 检查这个 pt 值是否在我们的 Word 字号列表中
            // @ts-ignore
            const match = WORD_FONT_SIZES.some(opt => opt.value === ptStr);
            
            if (match) {
                val = ptStr;
            }
        }
    }
    
    return val;
  }

  isActive(_editor: IDomEditor): boolean { return false }
  isDisabled(_editor: IDomEditor): boolean { return false }

  exec(editor: IDomEditor, value: string | boolean) {
    if (value) {
      editor.addMark('fontSize', value.toString())
    }
  }
}

// 自定义字体菜单
class WordFontFamilyMenu implements ISelectMenu {
  readonly title = '字体'
  readonly tag = 'select'
  readonly width = 100
  
  getOptions(_editor: IDomEditor) {
    return FONT_FAMILY_OPTIONS.map(opt => ({
        value: opt.value,
        text: opt.text,
        selected: false
    }));
  }

  getValue(editor: IDomEditor): string | boolean {
    const activeFont = getActiveStyle(editor, 'fontFamily', 'Microsoft YaHei');
    if (!activeFont) return 'Microsoft YaHei';

    // 标准化处理：去除引号，取第一个字体（处理 fallback）
    // 例如: '"SimSun", sans-serif' -> 'SimSun'
    const normalized = activeFont.split(',')[0].replace(/['"]/g, '').trim().toLowerCase();
    
    // 在选项中查找匹配项 (不区分大小写，同时匹配 value, text 和 alias)
    // @ts-ignore
    const match = FONT_FAMILY_OPTIONS.find(opt => {
        const target = normalized;
        // 匹配 value (如 '黑体')
        if (opt.value.toLowerCase() === target) return true;
        // 匹配 text (如 '黑体')
        if (opt.text.toLowerCase() === target) return true;
        // 匹配 alias (如 'simhei')
        // @ts-ignore
        if (opt.alias && opt.alias.some(a => a.toLowerCase() === target)) return true;
        
        return false;
    });

    // 如果找到了匹配项，返回标准 value；否则尝试返回去引号后的值（因为如果不去引号，肯定匹配不上任何 value）
    return match ? match.value : activeFont.replace(/['"]/g, '');
  }

  isActive(_editor: IDomEditor): boolean { return false }
  isDisabled(_editor: IDomEditor): boolean { return false }

  exec(editor: IDomEditor, value: string | boolean) {
    if (value) {
      editor.addMark('fontFamily', value.toString());
    }
  }
}

// 自定义行高菜单
class WordLineHeightMenu implements ISelectMenu {
    readonly title = '行高'
    readonly tag = 'select'
    readonly width = 80

    getOptions(_editor: IDomEditor) {
        return [
            { value: '1', text: '1' },
            { value: '1.15', text: '1.15' },
            { value: '1.5', text: '1.5' },
            { value: '2', text: '2' },
            { value: '2.5', text: '2.5' },
            { value: '3', text: '3' },
        ];
    }

    getValue(editor: IDomEditor): string | boolean {
        // 默认行高 1.5
        return getActiveStyle(editor, 'lineHeight', '1.5');
    }

    isActive(_editor: IDomEditor): boolean { return false }
    isDisabled(_editor: IDomEditor): boolean { return false }

    exec(editor: IDomEditor, value: string | boolean) {
        if (value) {
            // WangEditor 设置行高是针对 Block 的
            // @ts-ignore
            editor.setNode({ lineHeight: value.toString() });
        }
    }
}

// 注册菜单 (防止热更新重复注册)
const fontSizeMenuKey = 'wordFontSize';
const fontFamilyMenuKey = 'wordFontFamily';
const lineHeightMenuKey = 'wordLineHeight';

try {
  Boot.registerMenu({ key: fontSizeMenuKey, factory() { return new WordFontSizeMenu() }, });
  Boot.registerMenu({ key: fontFamilyMenuKey, factory() { return new WordFontFamilyMenu() }, });
  Boot.registerMenu({ key: lineHeightMenuKey, factory() { return new WordLineHeightMenu() }, });
} catch (e) {
  // 忽略重复注册错误
}

interface EditorProps {
  html: string;
  onChange?: (html: string) => void;
  readOnly?: boolean;
  docId?: string; // 新增: 用于加载/保存文档配置
}


// ... (保留 Editor 组件定义)


export default function EditorComponent({ html, onChange, readOnly = false, docId }: EditorProps) {
  const [editor, setEditor] = useState<IDomEditor | null>(null); 
  
  // 配置加载状态
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  // 页面边距状态 (单位: cm)
  const [pageMargins, setPageMargins] = useState({
    top: 2.54,
    bottom: 2.54,
    left: 3.17,
    right: 3.17
  });

  // 标题样式状态 (H1-H6) - fontSize 单位: pt
  const [headingStyles, setHeadingStyles] = useState({
    h1: { fontSize: 22, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#1890ff', marginTop: 17, marginBottom: 16.5 },
    h2: { fontSize: 16, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 13, marginBottom: 13 },
    h3: { fontSize: 14, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 13, marginBottom: 13 },
    h4: { fontSize: 12, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 12, marginBottom: 12 },
    h5: { fontSize: 10.5, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 10, marginBottom: 10 },
    h6: { fontSize: 9, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#666666', marginTop: 9, marginBottom: 9 },
  });

  const [showPageSettings, setShowPageSettings] = useState(false);
  
  const editorContainerRef = useRef<HTMLDivElement>(null);
  
  // 工具栏配置
  const toolbarConfig: Partial<IToolbarConfig> = {
    excludeKeys: [
      'group-video',
      'fontSize', // 排除原生字号菜单
      'fontFamily', // 排除原生字体菜单
      'lineHeight' // 排除原生行高菜单
    ],
    insertKeys: {
        index: 10,
        keys: ['wordFontFamily', 'wordFontSize', 'wordLineHeight'] // 插入自定义菜单
    }
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
            font-size: ${style.fontSize}pt !important;
            font-family: ${style.fontFamily || 'Microsoft YaHei'} !important;
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
            font-family: inherit !important;
            font-weight: inherit !important;
            color: inherit !important;
            background-color: transparent !important;
          }
        `;
      }).join('\n')}
      
      /* 全局默认样式 (覆盖编辑器默认的 16px) */
      .w-e-text-container [data-slate-editor] {
        font-size: ${EDITOR_DEFAULTS.fontSize} !important;
        font-family: ${EDITOR_DEFAULTS.fontFamily} !important;
        line-height: ${EDITOR_DEFAULTS.lineHeight};
        color: ${EDITOR_DEFAULTS.color};
      }
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

  // 1. 加载文档配置
  useEffect(() => {
    if (docId) {
      settingsService.getDocumentSettings(docId)
        .then(data => {
          setPageMargins({
            // 自动检测并转换旧的 px 数据 (如果值 > 15 认为是 px)
            top: data.margin_top > 15 ? Number((data.margin_top / 37.8).toFixed(2)) : data.margin_top,
            bottom: data.margin_bottom > 15 ? Number((data.margin_bottom / 37.8).toFixed(2)) : data.margin_bottom,
            left: data.margin_left > 15 ? Number((data.margin_left / 37.8).toFixed(2)) : data.margin_left,
            right: data.margin_right > 15 ? Number((data.margin_right / 37.8).toFixed(2)) : data.margin_right
          });
          
          if (data.heading_styles) {
            setHeadingStyles(data.heading_styles);
          }
          setSettingsLoaded(true);
        })
        .catch(err => {
          console.error('加载文档配置失败:', err);
          // 失败也标记为加载完成，使用默认值
          setSettingsLoaded(true);
        });
    } else {
        setSettingsLoaded(true);
    }
  }, [docId]);

  // 2. 自动保存文档配置 (防抖)
  useEffect(() => {
    // 只有在配置已加载且有 docId 时才保存，避免用默认值覆盖服务器数据
    if (docId && settingsLoaded) {
      const timer = setTimeout(() => {
        settingsService.saveDocumentSettings(docId, {
          margin_top: pageMargins.top,
          margin_bottom: pageMargins.bottom,
          margin_left: pageMargins.left,
          margin_right: pageMargins.right,
          heading_styles: headingStyles
        }).catch(err => console.error('自动保存配置失败:', err));
      }, 1000); // 1秒防抖

      return () => clearTimeout(timer);
    }
  }, [docId, settingsLoaded, pageMargins, headingStyles]);

  // 3. 监听 headingStyles 变化，同步到 editor 实例供 Menu 使用
  useEffect(() => {
    if (editor && settingsLoaded) {
        // @ts-ignore
        editor.headingStyles = headingStyles;
    }
  }, [editor, headingStyles, settingsLoaded]);

  // 监听外部 html 变化更新编辑器
  useEffect(() => {
    if (editor && html) {
      // 只有内容真的变了才 setHtml
      // 移除原有的元数据剥离逻辑，现在 html 就是纯 html
      const currentContent = editor.getHtml();
      
      try {
        if (html !== currentContent) {
           // 只有在内容确实不同且编辑器可用时才更新
           // @ts-ignore
           if (!editor.isDestroyed) {
             editor.setHtml(html);
           }
        }
      } catch (e) {
        console.warn('更新编辑器内容时出错 (通常可忽略):', e);
      }
    }
  }, [html, editor]);


  // 4. 实现悬浮工具栏拖拽功能
  useEffect(() => {
    if (!editor) return;

    // 拖拽逻辑实现
    const enableDrag = (hoverBar: HTMLElement) => {
        if (hoverBar.dataset.dragEnabled === 'true') return;
        hoverBar.dataset.dragEnabled = 'true';
        
        // 核心状态：当前的位移偏移量
        const dragOffset = { x: 0, y: 0 };
        let isDragging = false;

        const applyTransform = () => {
             // 使用独立的 translate CSS 属性 (Chrome 104+)
             // 它独立于 transform 属性，不会被 WangEditor 的 style="transform:..." 覆盖
             // 且比 margin 更由硬件加速，定位更可靠
             const translateValue = `${dragOffset.x}px ${dragOffset.y}px`;
             
             if (hoverBar.style.translate !== translateValue) {
                 hoverBar.style.translate = translateValue;
             }
        };

        const insertHandle = () => {
             if (hoverBar.querySelector('.w-e-drag-handle')) return;
             if (!hoverBar.firstChild) return;

            const handle = document.createElement('div');
            handle.className = 'w-e-drag-handle';
            handle.title = "拖拽移动 (双击复位)";
            handle.innerHTML = `
              <svg viewBox="0 0 24 24" width="14" height="14" fill="#999">
                <path d="M9 3h2v18H9V3zm4 0h2v18h-2V3z"/>
              </svg>
            `;
            Object.assign(handle.style, {
              cursor: 'move',
              padding: '0 4px',
              marginRight: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRight: '1px solid #eee',
              height: '100%',
              userSelect: 'none',
              flexShrink: '0'
            });

            hoverBar.insertBefore(handle, hoverBar.firstChild);
            hoverBar.style.display = 'flex';
            hoverBar.style.alignItems = 'center';

            // 拖拽事件
            let startX = 0;
            let startY = 0;
            let startOffsetX = 0;
            let startOffsetY = 0;

            handle.addEventListener('dblclick', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dragOffset.x = 0;
                dragOffset.y = 0;
                applyTransform();
            });

            handle.addEventListener('mousedown', (e) => {
                e.preventDefault();
                e.stopPropagation();

                isDragging = true;
                startX = e.clientX;
                startY = e.clientY;
                startOffsetX = dragOffset.x;
                startOffsetY = dragOffset.y;

                const originalZIndex = hoverBar.style.zIndex;
                hoverBar.style.zIndex = '10001';
                // margin 动画不需要 transition hack

                const onMouseMove = (moveEvent: MouseEvent) => {
                    if (!isDragging) return;
                    const dx = moveEvent.clientX - startX;
                    const dy = moveEvent.clientY - startY;
                    
                    dragOffset.x = startOffsetX + dx;
                    dragOffset.y = startOffsetY + dy;
                    
                    applyTransform();
                };

                const onMouseUp = () => {
                    isDragging = false;
                    hoverBar.style.zIndex = originalZIndex;
                    document.removeEventListener('mousemove', onMouseMove);
                    document.removeEventListener('mouseup', onMouseUp);
                };

                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
            });
        };

        insertHandle();

        // 监听 HoverBar 变化
        const barObserver = new MutationObserver((mutations) => {
            let shouldInsert = false;
            
            // 检查是否被隐藏
            const isVisible = hoverBar.style.display !== 'none';

            for (const m of mutations) {
                if (m.type === 'childList') {
                    shouldInsert = true;
                }
                
                // 如果 WangEditor 重写了 style (比如更新位置)，可能会把我们的 transform 抹掉
                // 所以只要是可见状态，我们都要强制把 transform 加回去
                if (m.type === 'attributes' && m.attributeName === 'style') {
                    if (isVisible) {
                        applyTransform();
                    } else {
                        // 如果变成隐藏了，重置偏移量 (根据需求，也可选择仅保留不重置)
                        // 这里选择重置，让下次显示时出现在默认位置
                        if (dragOffset.x !== 0 || dragOffset.y !== 0) {
                             dragOffset.x = 0;
                             dragOffset.y = 0;
                             // 此时不需要 applyTransform，因为它是隐藏的，甚至 transform 可能被清空也无所谓
                             // 等下次变可见时，style 变化会再次触发这里，但 offset 是 0，所以会设为 translate(0,0)
                        }
                    }
                }
            }

            if (shouldInsert) insertHandle();
        });

        barObserver.observe(hoverBar, { 
            childList: true, 
            attributes: true, 
            attributeFilter: ['style'] 
        });
    };

    // 全局监听器：发现新的 HoverBar 并初始化
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            mutation.addedNodes.forEach(node => {
                if (node instanceof HTMLElement) {
                    if (node.classList.contains('w-e-hover-bar')) {
                        enableDrag(node);
                    } else {
                        const bars = node.querySelectorAll('.w-e-hover-bar');
                        bars.forEach(b => enableDrag(b as HTMLElement));
                    }
                }
            });
        }
    });

    // 初始扫描
    document.querySelectorAll('.w-e-hover-bar').forEach(bar => {
        if (bar instanceof HTMLElement) enableDrag(bar);
    });

    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
        observer.disconnect();
        // barObserver 绑定在 closure 里，无法在此处清理，但随着 dom 销毁也会失效，或者在 enableDrag 里根据 element 销毁来清理
        // 实际上这在 React useEffect cleanup 中是可以接受的，因为 body observer 断开后不再触发新的 enableDrag
    };
  }, [editor]);


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
    
    // 1. 提取并注入表格列宽 (保留此功能)
    currentHtml = extractTableWidths(currentHtml);
    
    // 移除原有 doc-settings 注入逻辑
    
    onChange?.(currentHtml);
  };

  return (
    <div 
      ref={editorContainerRef} 
      style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: '100%',
        // 注入 CSS 变量 (cm -> px, 1cm ≈ 37.8px)
        // @ts-ignore
        '--page-margin-top': `${pageMargins.top * 37.8}px`,
        '--page-margin-right': `${pageMargins.right * 37.8}px`,
        '--page-margin-bottom': `${pageMargins.bottom * 37.8}px`,
        '--page-margin-left': `${pageMargins.left * 37.8}px`
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
            <strong style={{ minWidth: '80px' }}>页边距 (cm):</strong>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label>上:</label>
              <input type="number" step="0.1" value={pageMargins.top} onChange={e => setPageMargins({...pageMargins, top: Number(e.target.value)})} style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label>下:</label>
              <input type="number" step="0.1" value={pageMargins.bottom} onChange={e => setPageMargins({...pageMargins, bottom: Number(e.target.value)})} style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label>左:</label>
              <input type="number" step="0.1" value={pageMargins.left} onChange={e => setPageMargins({...pageMargins, left: Number(e.target.value)})} style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label>右:</label>
              <input type="number" step="0.1" value={pageMargins.right} onChange={e => setPageMargins({...pageMargins, right: Number(e.target.value)})} style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} />
            </div>
          </div>

          {/* 标题样式区域 */}
          {[
            { key: 'h1' as const, label: '一级标题 (H1)' },
            { key: 'h2' as const, label: '二级标题 (H2)' },
            { key: 'h3' as const, label: '三级标题 (H3)' },
            { key: 'h4' as const, label: '四级标题 (H4)' },
            { key: 'h5' as const, label: '五级标题 (H5)' },
            { key: 'h6' as const, label: '六级标题 (H6)' }
          ].map(h => (
            //@ts-ignore
            <div key={h.key} style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <strong style={{ minWidth: '80px' }}>{h.label}:</strong>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span>字号</span>
                <select
                  //@ts-ignore
                  value={`${headingStyles[h.key].fontSize}pt`} 
                  //@ts-ignore
                  onChange={e => setHeadingStyles({...headingStyles, [h.key]: { ...headingStyles[h.key], fontSize: parseFloat(e.target.value) }})}
                  style={{ width: '80px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }} 
                >
                  {WORD_FONT_SIZES.map(size => (
                    <option key={size.value} value={size.value}>{size.label}</option>
                  ))}
                  {/* 如果当前值不在预设列表中，显示为自定义 */}
                  {!WORD_FONT_SIZES.some(s => s.value === `${headingStyles[h.key].fontSize}pt`) && (
                      //@ts-ignore
                      <option value={`${headingStyles[h.key].fontSize}pt`} hidden>{headingStyles[h.key].fontSize}pt</option>
                  )}
                </select>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <span>字体</span>
                <select
                  //@ts-ignore
                  value={headingStyles[h.key].fontFamily || 'Microsoft YaHei'}
                  //@ts-ignore
                  onChange={e => setHeadingStyles({...headingStyles, [h.key]: { ...headingStyles[h.key], fontFamily: e.target.value }})}
                  style={{ width: '100px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }}
                >
                    <option value="Microsoft YaHei">微软雅黑</option>
                    <option value="SimSun">宋体</option>
                    <option value="SimHei">黑体</option>
                    <option value="KaiTi">楷体</option>
                    <option value="Arial">Arial</option>
                    <option value="Times New Roman">Times New Roman</option>
                </select>
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
              setPageMargins({ top: 2.54, bottom: 2.54, left: 3.17, right: 3.17 });
              setHeadingStyles({
                h1: { fontSize: 22, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#1890ff', marginTop: 17, marginBottom: 16.5 },
                h2: { fontSize: 16, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 13, marginBottom: 13 },
                h3: { fontSize: 14, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 13, marginBottom: 13 },
                h4: { fontSize: 12, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 12, marginBottom: 12 },
                h5: { fontSize: 10.5, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 10, marginBottom: 10 },
                h6: { fontSize: 9, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#666666', marginTop: 9, marginBottom: 9 },
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
