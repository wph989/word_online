/**
 * 编辑器设置相关 Hooks
 */

import { useState, useEffect } from 'react';
import { IDomEditor } from '@wangeditor/editor';
import { settingsService } from '../../../services/api';

// 页面边距状态默认值 (单位: cm)
const DEFAULT_PAGE_MARGINS = {
    top: 2.54,
    bottom: 2.54,
    left: 3.17,
    right: 3.17
};

// 标题样式状态默认值 (H1-H6) - fontSize 单位: pt
const DEFAULT_HEADING_STYLES = {
    h1: { fontSize: 22, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#1890ff', marginTop: 17, marginBottom: 16.5 },
    h2: { fontSize: 16, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 13, marginBottom: 13 },
    h3: { fontSize: 14, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 13, marginBottom: 13 },
    h4: { fontSize: 12, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 12, marginBottom: 12 },
    h5: { fontSize: 10.5, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#333333', marginTop: 10, marginBottom: 10 },
    h6: { fontSize: 9, fontFamily: 'Microsoft YaHei', fontWeight: 'bold', color: '#666666', marginTop: 9, marginBottom: 9 },
};

export const useEditorSettings = (docId?: string) => {
    const [settingsLoaded, setSettingsLoaded] = useState(false);
    const [pageMargins, setPageMargins] = useState(DEFAULT_PAGE_MARGINS);
    const [headingStyles, setHeadingStyles] = useState(DEFAULT_HEADING_STYLES);

    // 1. 加载文档配置
    useEffect(() => {
        if (docId) {
            settingsService.getDocumentSettings(docId)
                .then((data: any) => {
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
                .catch((err: any) => {
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
                }).catch((err: any) => console.error('自动保存配置失败:', err));
            }, 1000); // 1秒防抖

            return () => clearTimeout(timer);
        }
    }, [docId, settingsLoaded, pageMargins, headingStyles]);

    // 3. 监听 headingStyles 变化，同步到 editor 实例供 Menu 使用
    const syncHeadingStylesToEditor = (editor: IDomEditor | null) => {
        useEffect(() => {
            if (editor && settingsLoaded) {
                // @ts-ignore
                editor.headingStyles = headingStyles;
            }
        }, [editor, headingStyles, settingsLoaded]);
    };

    const resetSettings = () => {
        setPageMargins(DEFAULT_PAGE_MARGINS);
        setHeadingStyles(DEFAULT_HEADING_STYLES);
    };

    return {
        settingsLoaded,
        pageMargins,
        setPageMargins,
        headingStyles,
        setHeadingStyles,
        syncHeadingStylesToEditor,
        resetSettings
    };
};
