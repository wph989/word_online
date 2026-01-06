import { Boot } from '@wangeditor-next/editor';
import { DOMElement } from '@wangeditor-next/editor/dist/editor/src/utils/dom';

/**
 * 解析 HTML 样式到编辑器属性
 * 确保 font-size, font-family, line-height 能正确从 HTML 回显到编辑器
 */
export function registerStyleParsers() {
    // 1. 解析段落的 lineHeight（块级属性）
    Boot.registerParseElemHtml({
        selector: 'p',
        parseElemHtml: (domElem: DOMElement, node: any) => {
            const elem = domElem as unknown as HTMLElement;
            const newNode = { ...node };

            // 提取 line-height
            if (elem.style.lineHeight) {
                newNode.lineHeight = elem.style.lineHeight;
            }

            return newNode;
        }
    });

    // 2. 解析标题的 lineHeight
    for (let i = 1; i <= 6; i++) {
        Boot.registerParseElemHtml({
            selector: `h${i}`,
            parseElemHtml: (domElem: DOMElement, node: any) => {
                const elem = domElem as unknown as HTMLElement;
                const newNode = { ...node };

                // 提取 line-height
                if (elem.style.lineHeight) {
                    newNode.lineHeight = elem.style.lineHeight;
                }

                return newNode;
            }
        });
    }

    // 3. 解析文本的 fontSize 和 fontFamily（文本标记）
    Boot.registerParseStyleHtml((domElem: DOMElement, node: any, _editor: any) => {
        const elem = domElem as unknown as HTMLElement;
        if (!elem.style) return node;

        const newNode = { ...node };

        // 解析 font-size
        if (elem.style.fontSize) {
            newNode.fontSize = elem.style.fontSize;
        }

        // 解析 font-family
        if (elem.style.fontFamily) {
            newNode.fontFamily = elem.style.fontFamily;
        }

        return newNode;
    });
}
