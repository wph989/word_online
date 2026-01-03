/**
 * 编辑器默认样式配置
 * 
 * 这些值会应用于：
 * 1. 前端编辑器的默认样式
 * 2. 后端导出时的默认样式
 * 
 * 修改这里的值可以统一调整整个系统的默认样式
 */

export const EDITOR_DEFAULTS = {
  // 默认字体
  fontFamily: 'Microsoft YaHei',
  
  // 默认字号（像素）
  fontSize: '16px',
  
  // 默认行高（倍数）
  lineHeight: '1.5',
  
  // 默认文字颜色
  color: '#333',
  
  // 默认段落间距（像素）
  paragraphSpacing: '10px'
} as const;

/**
 * 获取字体的 CSS font-family 值
 * 包含备用字体
 */
export function getFontFamilyCSS(): string {
  return `"${EDITOR_DEFAULTS.fontFamily}", "Heiti SC", sans-serif`;
}

/**
 * 获取用于显示的字体名称
 */
export function getDisplayFontName(): string {
  return EDITOR_DEFAULTS.fontFamily;
}
