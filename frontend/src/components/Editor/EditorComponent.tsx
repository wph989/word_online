/**
 * 编辑器主组件 - 重构版本
 */

import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { Editor, Toolbar } from '@wangeditor-next/editor-for-react';
import { IDomEditor, IEditorConfig, IToolbarConfig, i18nAddResources } from '@wangeditor-next/editor';
import '@wangeditor-next/editor/dist/css/style.css';
import { EDITOR_DEFAULTS } from '../../config/editorDefaults';

// 导入拆分后的模块
import { useEditorSettings, useDraggable, useTableMultiSelect } from './hooks';
import './menus'; // 注册自定义菜单
import { PageSettings } from './components';
import { fixTextIndentFontSize } from './utils/fixTextIndent';

// 暴露给父组件的接口
export interface EditorRef {
    insertHtml: (html: string) => void;
    getSelectionText: () => string;
    saveSelection: () => string; // 保存选区并返回选中文本
    replaceSelection: (html: string) => void; // 恢复选区并替换内容
    focus: () => void; // 聚焦编辑器
    getSelectedCells: () => HTMLTableCellElement[]; // 获取选中的表格单元格
    clearCellSelection: () => void; // 清除单元格选中状态
}

interface EditorProps {
    html: string;
    onChange?: (html: string) => void;
    onSelectionChange?: (text: string) => void; // 新增：选区变化回调
    readOnly?: boolean;
    docId?: string;
}

export type { EditorProps };

// 添加自定义的多语言资源，覆盖默认的"默认字号"等文本
// 必须在组件外部或初始化前调用
i18nAddResources('zh-CN', {
    fontSize: {
        default: '小四 (12pt)',
    },
    fontFamily: {
        default: '宋体',
    },
    lineHeight: {
        default: '1.5',
    }
});

// 使用 forwardRef 包装组件
const EditorComponent = forwardRef<EditorRef, EditorProps>(({ html, onChange, onSelectionChange, readOnly = false, docId }, ref) => {
    const [editor, setEditor] = useState<IDomEditor | null>(null);

    // 保存的选区信息
    const savedSelectionRef = useRef<any>(null);
    const editorContainerRef = useRef<HTMLDivElement>(null);

    // 使用自定义 Hooks
    const {
        pageMargins,
        setPageMargins,
        headingStyles,
        setHeadingStyles,
        headingNumberingStyle,
        setHeadingNumberingStyle,
        syncHeadingStylesToEditor,
        resetSettings
    } = useEditorSettings(docId);

    const [showPageSettings, setShowPageSettings] = useState(false);

    // 同步标题样式到编辑器
    syncHeadingStylesToEditor(editor);

    // 使用拖拽功能
    useDraggable(editor);

    // 使用表格多选功能
    const { getSelectedCells, clearSelection: clearCellSelection } = useTableMultiSelect(editor);



    // 暴露方法给父组件
    useImperativeHandle(ref, () => ({
        insertHtml: (content: string) => {
            if (editor) {
                editor.focus();
                editor.dangerouslyInsertHtml(content);
            }
        },
        getSelectionText: () => {
            if (editor) {
                return editor.getSelectionText();
            }
            return '';
        },
        saveSelection: () => {
            if (editor) {
                // 保存当前选区
                savedSelectionRef.current = editor.selection;
                return editor.getSelectionText();
            }
            return '';
        },
        replaceSelection: (content: string) => {
            if (editor) {
                // 先聚焦编辑器
                editor.focus();

                // 如果有保存的选区，恢复它
                if (savedSelectionRef.current) {
                    try {
                        editor.select(savedSelectionRef.current);
                    } catch (e) {
                        console.warn('恢复选区失败:', e);
                    }
                }

                // 处理多行文本：按换行符分割，使用 insertBreak 模拟回车
                // 这样可以确保：
                // 1. 正确创建新的 Block（段落），避免结构错误
                // 2. 继承上一段落的样式
                const lines = content.split('\n');

                lines.forEach((line, index) => {
                    if (line) {
                        editor.insertText(line);
                    }
                    // 如果不是最后一行，插入换行符
                    if (index < lines.length - 1) {
                        editor.insertBreak();
                    }
                });

                // 清除保存的选区
                savedSelectionRef.current = null;
            }
        },
        focus: () => {
            if (editor) {
                editor.focus();
            }
        },
        getSelectedCells: () => {
            return getSelectedCells();
        },
        clearCellSelection: () => {
            clearCellSelection();
        }
    }));

    // 工具栏配置 - 使用 wangEditor-next 默认配置
    const toolbarConfig: Partial<IToolbarConfig> = {
        excludeKeys: [
            'group-video' // 只排除视频组
        ]
    };

    // 编辑器配置
    const editorConfig: Partial<IEditorConfig> = {
        placeholder: '请输入内容...',
        readOnly,
        MENU_CONF: {
            // 字号配置 - 使用 pt 单位和中文字号别名
            fontSize: {
                fontSizeList: [
                    { name: '初号 (42pt)', value: '42pt' },
                    { name: '小初 (36pt)', value: '36pt' },
                    { name: '一号 (26pt)', value: '26pt' },
                    { name: '小一 (24pt)', value: '24pt' },
                    { name: '二号 (22pt)', value: '22pt' },
                    { name: '小二 (18pt)', value: '18pt' },
                    { name: '三号 (16pt)', value: '16pt' },
                    { name: '小三 (15pt)', value: '15pt' },
                    { name: '四号 (14pt)', value: '14pt' },
                    { name: '小四 (12pt)', value: '12pt' },
                    { name: '五号 (10.5pt)', value: '10.5pt' },
                    { name: '小五 (9pt)', value: '9pt' },
                    { name: '六号 (7.5pt)', value: '7.5pt' },
                    { name: '小六 (6.5pt)', value: '6.5pt' },
                    { name: '七号 (5.5pt)', value: '5.5pt' },
                    { name: '八号 (5pt)', value: '5pt' },
                ]
            },
            // 字体配置 - 使用中文常用字体
            fontFamily: {
                fontFamilyList: [
                    { name: '宋体', value: '宋体, SimSun, serif' },
                    { name: '黑体', value: '黑体, SimHei, sans-serif' },
                    { name: '楷体', value: '楷体, KaiTi, serif' },
                    { name: '仿宋', value: '仿宋, FangSong, serif' },
                    { name: '微软雅黑', value: '微软雅黑, Microsoft YaHei, sans-serif' },
                    { name: '华文细黑', value: '华文细黑, STXihei, sans-serif' },
                    { name: '华文楷体', value: '华文楷体, STKaiti, serif' },
                    { name: 'Arial', value: 'Arial, sans-serif' },
                    { name: 'Times New Roman', value: '"Times New Roman", serif' },
                ]
            },
            // 行高配置 - 使用倍数显示
            lineHeight: {
                lineHeightList: ['1', '1.15', '1.5', '1.75', '2', '2.5', '3']
            },
            // 图片上传配置
            uploadImage: {
                server: '/api/v1/upload/image',
                maxFileSize: 5 * 1024 * 1024,
                maxNumberOfFiles: 10,
                allowedFileTypes: ['image/*'],
                timeout: 10 * 1000,
                metaWithUrl: false,
                base64LimitSize: 0,
                onSuccess(file: any, res: any) {
                    console.log('图片上传成功', file?.name, res);
                },
                onFailed(file: any, res: any) {
                    console.log('图片上传失败', file?.name, res);
                },
                onError(file: any, err: any, _res: any) {
                    console.log('图片上传错误', file?.name, err);
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

      /* 强制给容器增加顶部内边距，解决表格菜单被遮挡问题 */
      .w-e-text-container {
        padding-top: 160px !important;
      }
    `}</style>
    );

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

                        // 修复首行缩进的 em 单位问题
                        // 需要等待 DOM 更新完成
                        setTimeout(() => {
                            const editorDom = editorContainerRef.current?.querySelector('[data-slate-editor]') as HTMLElement;
                            fixTextIndentFontSize(editorDom);
                        }, 100);
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
                } catch (e) {
                    // ignore destroy errors
                }
                setEditor(null);
            }
        };
    }, [editor]);

    // 监听选区变化 (独立于内容变化)
    useEffect(() => {
        if (!editor) return;

        const handleSelection = () => {
            if (editor.isDestroyed) return;

            // 只有当编辑器拥有焦点时才更新
            // 这样避免了点击 AI 面板输入框时，因编辑器失焦而导致的错误更新
            if (editor.isFocused()) {
                // 自动更新保存的选区，确保 replaceSelection 能使用最新选区
                // @ts-ignore
                savedSelectionRef.current = editor.selection;

                if (onSelectionChange) {
                    try {
                        // 使用浏览器原生 API 获取完整选中文本
                        // editor.getSelectionText() 可能返回不完整的文本
                        const browserSelection = window.getSelection();
                        const text = browserSelection ? browserSelection.toString() : '';
                        onSelectionChange(text);
                    } catch (e) {
                        console.warn('Get selection failed:', e);
                    }
                }
            }
        };

        // 使用全局 selectionchange 事件，因为 WangEditor/Slate 没有直接暴露可靠的 selection 事件
        document.addEventListener('selectionchange', handleSelection);

        return () => {
            document.removeEventListener('selectionchange', handleSelection);
        };
    }, [editor, onSelectionChange]);

    const handleChange = (editor: IDomEditor) => {
        let currentHtml = editor.getHtml();

        // 1. 提取并注入表格列宽 (保留此功能，但需注意不要破坏 DOM 结构)
        // 如果此函数导致了 Slate 路径错误，应暂时禁用或优化
        // currentHtml = extractTableWidths(currentHtml, editorContainerRef); 
        // 暂时保持开启，但如果你发现输入时光标跳动或报错，请注释掉上面这行

        // 2. 修复首行缩进的 em 单位问题（实时修复，用户修改字号后立即生效）
        // 使用 setTimeout 而不是 requestAnimationFrame，给 WangEditor 更多时间完成 DOM 更新
        setTimeout(() => {
            const editorDom = editorContainerRef.current?.querySelector('[data-slate-editor]') as HTMLElement;
            fixTextIndentFontSize(editorDom);
        }, 50);

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
                <PageSettings
                    pageMargins={pageMargins}
                    headingStyles={headingStyles}
                    headingNumberingStyle={headingNumberingStyle}
                    setPageMargins={setPageMargins}
                    setHeadingStyles={setHeadingStyles}
                    setHeadingNumberingStyle={setHeadingNumberingStyle}
                    resetSettings={resetSettings}
                />
            )}


            <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
                <Editor
                    defaultConfig={editorConfig}
                    value={html}
                    onCreated={setEditor}
                    onChange={handleChange}
                    mode="default"
                    style={{ minHeight: '100%', overflowY: 'visible' }}
                />
            </div>
        </div>
    );
});

export default EditorComponent;
