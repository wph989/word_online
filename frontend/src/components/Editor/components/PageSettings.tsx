/**
 * 文档设置面板组件
 */

import React from 'react';
import { WORD_FONT_SIZES } from '../../../config/editorDefaults';

interface PageSettingsProps {
    pageMargins: {
        top: number;
        bottom: number;
        left: number;
        right: number;
    };
    headingStyles: any;
    headingNumberingStyle: {
        enabled: boolean;
        style?: string;
    } | null;
    setPageMargins: (margins: any) => void;
    setHeadingStyles: (styles: any) => void;
    setHeadingNumberingStyle: (style: any) => void;
    resetSettings: () => void;
}

export const PageSettings: React.FC<PageSettingsProps> = ({
    pageMargins,
    headingStyles,
    headingNumberingStyle,
    setPageMargins,
    setHeadingStyles,
    setHeadingNumberingStyle,
    resetSettings
}) => {
    return (
        <div style={{
            padding: '16px 20px',
            background: '#fafafa',
            borderBottom: '1px solid #e8e8e8',
            fontSize: '13px',
            color: '#333',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            maxHeight: '300px',
            overflowY: 'auto'
        }}>
            {/* 页边距区域 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                <strong style={{ minWidth: '80px' }}>页边距 (cm):</strong>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <label>上:</label>
                    <input
                        type="number"
                        step="0.1"
                        value={pageMargins.top}
                        onChange={e => setPageMargins({ ...pageMargins, top: Number(e.target.value) })}
                        style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }}
                    />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <label>下:</label>
                    <input
                        type="number"
                        step="0.1"
                        value={pageMargins.bottom}
                        onChange={e => setPageMargins({ ...pageMargins, bottom: Number(e.target.value) })}
                        style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }}
                    />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <label>左:</label>
                    <input
                        type="number"
                        step="0.1"
                        value={pageMargins.left}
                        onChange={e => setPageMargins({ ...pageMargins, left: Number(e.target.value) })}
                        style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }}
                    />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <label>右:</label>
                    <input
                        type="number"
                        step="0.1"
                        value={pageMargins.right}
                        onChange={e => setPageMargins({ ...pageMargins, right: Number(e.target.value) })}
                        style={{ width: '50px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }}
                    />
                </div>
            </div>

            {/* 标题编号样式区域 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                <strong style={{ minWidth: '80px' }}>标题编号:</strong>
                <select
                    value={headingNumberingStyle?.enabled ? (headingNumberingStyle.style || 'style2') : 'none'}
                    onChange={e => {
                        const value = e.target.value;
                        if (value === 'none') {
                            setHeadingNumberingStyle(null);
                        } else {
                            setHeadingNumberingStyle({ enabled: true, style: value });
                        }
                    }}
                    style={{
                        flex: 1,
                        padding: '6px 8px',
                        border: '1px solid #d9d9d9',
                        borderRadius: '4px',
                        fontSize: '13px'
                    }}
                >
                    <option value="none">不使用编号</option>
                    <option value="style1">中文混合（一、二、三 / 1.1 / (1)）</option>
                    <option value="style2">纯数字（1、2、3 / 1.1 / 1.1.1）</option>
                    <option value="style3">数字点号（1. / 1.1 / 1.1.1）</option>
                    <option value="style4">章节格式（第一章 / 1.1 / 1.1.1）</option>
                </select>
            </div>

            {/* 标题样式区域 */}
            {[
                { key: 'h1' as const, label: '一级标题 (H1)' },
                { key: 'h2' as const, label: '二级标题 (H2)' },
                { key: 'h3' as const, label: '三级标题 (H3)' },
                { key: 'h4' as const, label: '四级标题 (H4)' },
                { key: 'h5' as const, label: '五级标题 (H5)' },
                { key: 'h6' as const, label: '六级标题 (H6)' }
            ].map(h => (
                //@ts-ignore
                <div key={h.key} style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <strong style={{ minWidth: '80px' }}>{h.label}:</strong>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <span>字号</span>
                        <select
                            //@ts-ignore
                            value={`${headingStyles[h.key].fontSize}pt`}
                            //@ts-ignore
                            onChange={e => setHeadingStyles({ ...headingStyles, [h.key]: { ...headingStyles[h.key], fontSize: parseFloat(e.target.value) } })}
                            style={{ width: '80px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }}
                        >
                            {WORD_FONT_SIZES.map((size: any) => (
                                <option key={size.value} value={size.value}>{size.label}</option>
                            ))}
                            {/* 如果当前值不在预设列表中，显示为自定义 */}
                            {!WORD_FONT_SIZES.some((s: any) => s.value === `${headingStyles[h.key].fontSize}pt`) && (
                                //@ts-ignore
                                <option value={`${headingStyles[h.key].fontSize}pt`} hidden>{headingStyles[h.key].fontSize}pt</option>
                            )}
                        </select>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <span>字体</span>
                        <select
                            //@ts-ignore
                            value={headingStyles[h.key].fontFamily || 'Microsoft YaHei'}
                            //@ts-ignore
                            onChange={e => setHeadingStyles({ ...headingStyles, [h.key]: { ...headingStyles[h.key], fontFamily: e.target.value } })}
                            style={{ width: '100px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }}
                        >
                            <option value="Microsoft YaHei">微软雅黑</option>
                            <option value="SimSun">宋体</option>
                            <option value="SimHei">黑体</option>
                            <option value="KaiTi">楷体</option>
                            <option value="Arial">Arial</option>
                            <option value="Times New Roman">Times New Roman</option>
                        </select>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <span>颜色</span>
                        <input
                            type="color"
                            //@ts-ignore
                            value={headingStyles[h.key].color}
                            //@ts-ignore
                            onChange={e => setHeadingStyles({ ...headingStyles, [h.key]: { ...headingStyles[h.key], color: e.target.value } })}
                            style={{ width: '40px', padding: '0', border: 'none', background: 'none', cursor: 'pointer' }}
                        />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <span>加粗</span>
                        <input
                            type="checkbox"
                            //@ts-ignore
                            checked={headingStyles[h.key].fontWeight === 'bold'}
                            //@ts-ignore
                            onChange={e => setHeadingStyles({ ...headingStyles, [h.key]: { ...headingStyles[h.key], fontWeight: e.target.checked ? 'bold' : 'normal' } })}
                        />
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <span>段前/后</span>
                        <input
                            type="number"
                            //@ts-ignore
                            value={headingStyles[h.key].marginTop}
                            //@ts-ignore
                            onChange={e => setHeadingStyles({ ...headingStyles, [h.key]: { ...headingStyles[h.key], marginTop: Number(e.target.value) } })}
                            style={{ width: '40px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }}
                            title="段前距"
                        />
                        <input
                            type="number"
                            //@ts-ignore
                            value={headingStyles[h.key].marginBottom}
                            //@ts-ignore
                            onChange={e => setHeadingStyles({ ...headingStyles, [h.key]: { ...headingStyles[h.key], marginBottom: Number(e.target.value) } })}
                            style={{ width: '40px', padding: '4px', border: '1px solid #d9d9d9', borderRadius: '4px' }}
                            title="段后距"
                        />
                    </div>
                </div>
            ))}

            <button
                onClick={resetSettings}
                style={{
                    alignSelf: 'flex-start',
                    padding: '6px 16px',
                    background: '#fff',
                    border: '1px solid #d9d9d9',
                    cursor: 'pointer',
                    borderRadius: '4px',
                    color: '#666',
                    marginTop: '10px'
                }}
            >
                重置所有设置
            </button>
        </div>
    );
};
