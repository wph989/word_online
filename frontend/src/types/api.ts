// 简化版的 Content 和 StyleSheet 定义
export interface Content {
  blocks: any[];
}

export interface StyleSheet {
  id?: string;
  styles?: any[];
  rules?: any[];
}

export interface Chapter {
  id: string;
  doc_id: string;
  title: string;
  html_content: string; // 后端返回 HTML
  content: Content;
  stylesheet: StyleSheet;
  order_index: number;
  level: number;
  parent_id?: string | null;
  created_at?: string;
  updated_at?: string;
  children?: Chapter[]; // 用于前端递归渲染
}

export interface Document {
  id: string;
  title: string;
  chapters: Chapter[];
  created_at?: string;
  updated_at?: string;
}
