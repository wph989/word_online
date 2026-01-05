/**
 * 修复首行缩进的 em 单位问题
 * 
 * 问题：text-indent: 2em 基于 <p> 元素的 font-size 计算，
 * 但实际字号在内部 <span> 上，导致缩进不正确
 * 
 * 解决方案：从 <p> 内部第一个有 font-size 的元素获取字号，
 * 并应用到 <p> 元素上
 */
export function fixTextIndentFontSize(container: HTMLElement | null) {
    if (!container) return;

    // 查找所有有 text-indent 样式的段落和标题
    const elements = container.querySelectorAll('p[style*="text-indent"], h1[style*="text-indent"], h2[style*="text-indent"], h3[style*="text-indent"], h4[style*="text-indent"], h5[style*="text-indent"], h6[style*="text-indent"]');


    let fixedCount = 0;

    elements.forEach((elem) => {
        const element = elem as HTMLElement;
        const textIndent = element.style.textIndent;

        // 只处理使用 em 单位的缩进
        if (!textIndent || !textIndent.includes('em')) {
            return;
        }

        // 查找第一个有 font-size 样式的子元素（通常是 <span>）
        const firstSpan = element.querySelector('[style*="font-size"]') as HTMLElement;

        if (firstSpan && firstSpan.style.fontSize) {
            const currentFontSize = element.style.fontSize;
            const targetFontSize = firstSpan.style.fontSize;

            // 只有当字号不同时才更新
            if (currentFontSize !== targetFontSize) {
                element.style.fontSize = targetFontSize;
                fixedCount++;
            }
        }
    });

}
