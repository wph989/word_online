/**
 * 自定义菜单模块
 */

import { Boot } from '@wangeditor/editor';
import { WordFontSizeMenu } from './FontSizeMenu';
import { WordFontFamilyMenu } from './FontFamilyMenu';
import { WordLineHeightMenu } from './LineHeightMenu';
import { registerStyleParsers } from './styleParsing';

// 注册菜单
const fontSizeMenuKey = 'wordFontSize';
const fontFamilyMenuKey = 'wordFontFamily';
const lineHeightMenuKey = 'wordLineHeight';

try {
    // 注册自定义样式解析器 (确保回显正确)
    registerStyleParsers();

    Boot.registerMenu({ key: fontSizeMenuKey, factory() { return new WordFontSizeMenu() }, });
    Boot.registerMenu({ key: fontFamilyMenuKey, factory() { return new WordFontFamilyMenu() }, });
    Boot.registerMenu({ key: lineHeightMenuKey, factory() { return new WordLineHeightMenu() }, });
} catch (e) { }

export {
    fontSizeMenuKey,
    fontFamilyMenuKey,
    lineHeightMenuKey
};
