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
  orderIndex: number; // 注意：后端可能是 order_index，这里前端可能用了驼峰
  created_at?: string;
  updated_at?: string;
}

export interface Document {
  id: string;
  title: string;
  chapters: Chapter[];
  created_at?: string;
  updated_at?: string;
}
