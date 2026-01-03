import { Content } from './content';
import { StyleSheet } from './stylesheet';

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
