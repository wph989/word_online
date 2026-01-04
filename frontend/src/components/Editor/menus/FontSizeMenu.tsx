/**
 * 自定义字号菜单
 */

import { ISelectMenu, IDomEditor } from '@wangeditor/editor';
import { WORD_FONT_SIZES } from '../../../config/editorDefaults';
import { getActiveStyle } from '../utils/styleHelpers';

class WordFontSizeMenu implements ISelectMenu {
  readonly title = '字号'
  readonly tag = 'select'
  readonly width = 80

  getOptions(_editor: IDomEditor) {
    return WORD_FONT_SIZES.map((opt: any) => ({
      value: opt.value,
      text: opt.label,
      selected: false
    }))
  }

  getValue(editor: IDomEditor): string | boolean {
    let val = getActiveStyle(editor, 'fontSize', '12pt');
    if (!val) return '12pt';
    val = val.toString().toLowerCase();

    if (val.includes('px')) {
      const num = parseFloat(val);
      if (!isNaN(num)) {
        const pt = num * 0.75;
        const ptStr = `${Number(pt.toFixed(2))}pt`;
        // @ts-ignore
        const match = WORD_FONT_SIZES.some((opt: any) => opt.value === ptStr);
        if (match) val = ptStr;
      }
    }
    return val;
  }

  isActive(_editor: IDomEditor): boolean { return false }
  isDisabled(_editor: IDomEditor): boolean { return false }

  exec(editor: IDomEditor, value: string | boolean) {
    if (value) editor.addMark('fontSize', value.toString())
  }
}

export { WordFontSizeMenu };
