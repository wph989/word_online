/**
 * 自定义字体菜单
 */

import { ISelectMenu, IDomEditor } from '@wangeditor-next/editor';
import { FONT_FAMILY_OPTIONS } from '../../../config/editorDefaults';
import { getActiveStyle } from '../utils/styleHelpers';

class WordFontFamilyMenu implements ISelectMenu {
  readonly title = '字体'
  readonly tag = 'select'
  readonly width = 100

  getOptions(_editor: IDomEditor) {
    return FONT_FAMILY_OPTIONS.map((opt: any) => ({
      value: opt.value,
      text: opt.text,
      selected: false
    }));
  }

  getValue(editor: IDomEditor): string | boolean {
    const activeFont = getActiveStyle(editor, 'fontFamily', 'Microsoft YaHei');
    if (!activeFont) return 'Microsoft YaHei';
    const normalized = activeFont.split(',')[0].replace(/['"]/g, '').trim().toLowerCase();

    // @ts-ignore
    const match = FONT_FAMILY_OPTIONS.find((opt: any) => {
      const target = normalized;
      if (opt.value.toLowerCase() === target) return true;
      if (opt.text.toLowerCase() === target) return true;
      // @ts-ignore
      if (opt.alias && opt.alias.some((a: string) => a.toLowerCase() === target)) return true;
      return false;
    });
    return match ? match.value : activeFont.replace(/['"]/g, '');
  }

  isActive(_editor: IDomEditor): boolean { return false }
  isDisabled(_editor: IDomEditor): boolean { return false }

  exec(editor: IDomEditor, value: string | boolean) {
    if (value) editor.addMark('fontFamily', value.toString());
  }
}

export { WordFontFamilyMenu };
