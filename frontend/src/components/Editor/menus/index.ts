/**
 * 自定义菜单模块
 * wangEditor-next 原生支持字体、行高、表格合并/拆分功能
 * 此文件只保留样式解析器以确保回显正确
 */

import { registerStyleParsers } from './styleParsing';

// 标记是否已注册
let isRegistered = false;

/**
 * 注册样式解析器
 * 确保 font-size, font-family, line-height 能正确从 HTML 回显到编辑器
 */
function registerParsers() {
    if (isRegistered) return;

    try {
        // 注册自定义样式解析器 (确保回显正确)
        registerStyleParsers();
        isRegistered = true;
        console.log('样式解析器注册成功');
    } catch (e) {
        console.warn('注册样式解析器失败:', e);
    }
}

// 立即执行注册
registerParsers();

export { registerParsers };
