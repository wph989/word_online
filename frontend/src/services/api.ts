/**
 * API 服务
 * 封装所有后端 API 调用
 */

import axios from 'axios';

// 从环境变量读取后端 API 地址
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');

// 配置 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 添加请求拦截器
api.interceptors.request.use(
  (config: any) => {
    return config;
  },
  (error: any) => {
    return Promise.reject(error);
  }
);

// 添加响应拦截器
api.interceptors.response.use(
  (response: any) => {
    return response;
  },
  (error: any) => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else {
      console.error('Network Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// ============ Chapter Service (兼容原项目结构) ============

export const chapterService = {
  // 文档相关
  getDocumentsList: async (page = 1, size = 10) => {
    const response = await api.get(`/api/v1/documents`, {
      params: { page, size }
    });
    return response.data; // Pydantic 模型: { total: number, items: [], page: number, size: number }
  },

  createDocument: async (title: string) => {
    const response = await api.post(`/api/v1/documents`, { title });
    return response.data;
  },

  getDocument: async (id: string) => {
    // 后端返回的文档包含 chapters 列表
    const response = await api.get(`/api/v1/documents/${id}`);
    return response.data;
  },

  // 章节相关
  createChapter: async (title: string, docId: string) => {
    const response = await api.post(`/api/v1/chapters`, {
      doc_id: docId,
      title: title,
      html_content: '<p>新章节内容...</p>', // 默认内容
      order_index: 0 // 后端可能会自动处理，但发一个比较安全
    });
    return response.data;
  },

  getChapter: async (id: string) => {
    const response = await api.get(`/api/v1/chapters/${id}`);
    return response.data;
  },

  updateChapter: async (id: string, data: any) => {
    // data 可能是 { title, html_content, ... }
    const response = await api.put(`/api/v1/chapters/${id}`, data);
    return response.data;
  },

  deleteChapter: async (id: string) => {
    const response = await api.delete(`/api/v1/chapters/${id}`);
    return response.data;
  },

  // 导出
  exportChapterToDocx: (chapterId: string, includeTitle = true) => {
    const url = `${API_BASE_URL}/api/v1/export/chapters/${chapterId}/docx?include_title=${includeTitle}`;
    window.open(url, '_blank');
  },

  exportDocumentToDocx: (docId: string, includeChapterTitles = true, chapterTitleLevel = 1) => {
    const url = `${API_BASE_URL}/api/v1/export/documents/${docId}/docx?include_chapter_titles=${includeChapterTitles}&chapter_title_level=${chapterTitleLevel}`;
    window.open(url, '_blank');
  }
};

// ============ Settings Service ============

export const settingsService = {
  // 获取文档配置
  getDocumentSettings: async (docId: string) => {
    const response = await api.get(`/api/v1/settings/${docId}`);
    return response.data;
  },

  // 保存文档配置 (Upsert)
  saveDocumentSettings: async (docId: string, settings: any) => {
    // settings 包含 margin_top 等和 heading_styles
    const response = await api.put(`/api/v1/settings/${docId}`, settings);
    return response.data;
  }
};

// 兼容现有代码的直接导出
export const createDocument = chapterService.createDocument;
export const listDocuments = chapterService.getDocumentsList;
export const getDocument = chapterService.getDocument;
export const createChapter = chapterService.createChapter;
export const getChapter = chapterService.getChapter;
export const saveChapter = chapterService.updateChapter;
export const deleteChapter = chapterService.deleteChapter;
export const exportChapterToDocx = chapterService.exportChapterToDocx;
export const exportDocumentToDocx = chapterService.exportDocumentToDocx;

export default api;
