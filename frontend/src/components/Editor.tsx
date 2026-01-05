/**
 * 编辑器组件 - 兼容性包装器
 * 此文件保持向后兼容性，实际实现已拆分到 Editor/ 文件夹中
 */

// 导入拆分后的模块
export { default } from './Editor/index';
export type { EditorRef, EditorProps } from './Editor/index';
