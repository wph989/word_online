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
  
  // 默认字号（使用 pt）
  fontSize: '12pt',
  
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

export function getDisplayFontName(): string {
  return EDITOR_DEFAULTS.fontFamily;
}

// 常用中文字号映射 (pt 值)
export const WORD_FONT_SIZES = [
  { label: '初号', value: '42pt', pt: 42 },
  { label: '小初', value: '36pt', pt: 36 },
  { label: '一号', value: '26pt', pt: 26 },
  { label: '小一', value: '24pt', pt: 24 },
  { label: '二号', value: '22pt', pt: 22 },
  { label: '小二', value: '18pt', pt: 18 },
  { label: '三号', value: '16pt', pt: 16 },
  { label: '小三', value: '15pt', pt: 15 },
  { label: '四号', value: '14pt', pt: 14 },
  { label: '小四', value: '12pt', pt: 12 },
  { label: '五号', value: '10.5pt', pt: 10.5 },
  { label: '小五', value: '9pt', pt: 9 },
  { label: '六号', value: '7.5pt', pt: 7.5 },
  { label: '小六', value: '6.5pt', pt: 6.5 },
  { label: '七号', value: '5.5pt', pt: 5.5 },
  { label: '八号', value: '5pt', pt: 5 },
] as const;

export const FONT_SIZE_MAP = Object.fromEntries(
  WORD_FONT_SIZES.map(item => [item.value, item.pt])
);

// 常用字体配置
// 常用字体配置
export const FONT_FAMILY_OPTIONS = [
  { value: '微软雅黑', text: '微软雅黑', alias: ['Microsoft YaHei', 'sans-serif'] },
  { value: '宋体', text: '宋体', alias: ['SimSun', 'serif'] },
  { value: '黑体', text: '黑体', alias: ['SimHei'] },
  { value: '楷体', text: '楷体', alias: ['KaiTi', 'KaiTi_GB2312'] },
  { value: '仿宋', text: '仿宋', alias: ['FangSong', 'FangSong_GB2312'] },
  { value: '隶书', text: '隶书', alias: ['LiSu'] },
  { value: '幼圆', text: '幼圆', alias: ['YouYuan'] },
  { value: '华文细黑', text: '华文细黑', alias: ['STXihei'] },
  { value: '华文楷体', text: '华文楷体', alias: ['STKaiti'] },
  { value: '华文宋体', text: '华文宋体', alias: ['STSong'] },
  { value: '华文仿宋', text: '华文仿宋', alias: ['STFangsong'] },
  { value: 'Arial', text: 'Arial', alias: [] },
  { value: 'Times New Roman', text: 'Times New Roman', alias: [] },
  { value: 'Verdana', text: 'Verdana', alias: [] },
  { value: 'Tahoma', text: 'Tahoma', alias: [] },
  { value: 'Georgia', text: 'Georgia', alias: [] },
] as const;
