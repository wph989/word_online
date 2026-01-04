/**
 * 自定义行高菜单
 */

import { ISelectMenu, IDomEditor } from '@wangeditor/editor';
import { getActiveStyle } from '../utils/styleHelpers';

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
        return getActiveStyle(editor, 'lineHeight', '1.5');
    }

    isActive(_editor: IDomEditor): boolean { return false }
    isDisabled(_editor: IDomEditor): boolean { return false }

    exec(editor: IDomEditor, value: string | boolean) {
        if (value) {
            // @ts-ignore
            editor.setNode({ lineHeight: value.toString() });
        }
    }
}

export { WordLineHeightMenu };
