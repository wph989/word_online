/**
 * 样式辅助工具
 */

import { IDomEditor, DomEditor } from '@wangeditor-next/editor';

/**
 * 辅助函数：获取当前选区应用的样式（优先 Mark，其次 Block 默认配置，最后全局默认）
 * @param editor 编辑器实例
 * @param styleKey 样式属性名
 * @param defaultValue 全局默认值
 */
export function getActiveStyle(editor: IDomEditor, styleKey: 'fontSize' | 'fontFamily' | 'lineHeight', defaultValue: string): string {
    // 1. 优先获取 Mark (内联样式) - 仅针对 fontSize/fontFamily
    if (styleKey !== 'lineHeight') {
        // @ts-ignore
        const markValue = editor.marks ? editor.marks[styleKey] : null;
        if (markValue) return markValue;
    }

    // 2. 如果没有 Mark，检查是否是标题 Block，并获取其默认配置
    for (let i = 1; i <= 6; i++) {
        const type = `header${i}`;
        const node = DomEditor.getSelectedNodeByType(editor, type);
        if (node) {
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
                        return '1.5';
                    }
                }
            }
            break;
        }
    }
    
    // 2.5 如果是行高
    if (styleKey === 'lineHeight') {
        const node = DomEditor.getSelectedNodeByType(editor, 'paragraph');
        if (node) {
            // @ts-ignore
            if (node.lineHeight) return node.lineHeight;
        }
        for (let i = 1; i <= 6; i++) {
            const node = DomEditor.getSelectedNodeByType(editor, `header${i}`);
            // @ts-ignore
            if (node && node.lineHeight) return node.lineHeight;
        }
    }

    // 3. 尝试获取 DOM 计算样式
    try {
        const selection = window.getSelection();
        if (selection && selection.rangeCount > 0) {
            let node = selection.getRangeAt(0).commonAncestorContainer;
            if (node.nodeType === 3) node = node.parentElement!;
            
            if (node instanceof HTMLElement) {
                const inlineStyle = node.style[styleKey as any];
                if (inlineStyle) return inlineStyle;

                const computed = window.getComputedStyle(node);
                const val = computed[styleKey as any];
                if (val) {
                    if (styleKey === 'lineHeight') {
                         if (val === 'normal') return defaultValue;
                         if (!isNaN(Number(val))) return val;
                    } else {
                        return val;
                    }
                }
            }
        }
    } catch (e) { }

    return defaultValue;
}
