export interface AIAction {
  id: string;
  name: string;
  icon: string;
  description: string;
}

export const AI_ACTIONS: AIAction[] = [
  { id: 'rewrite', name: '重写', icon: '🔄', description: '重新表述内容' },
  { id: 'improve', name: '改进', icon: '✨', description: '提升文本质量' },
  { id: 'expand', name: '扩展', icon: '📝', description: '添加更多细节' },
  { id: 'summarize', name: '总结', icon: '📋', description: '提炼核心要点' },
  { id: 'polish', name: '润色', icon: '💎', description: '优化语言表达' },
  { id: 'simplify', name: '简化', icon: '🎯', description: '使内容更易理解' },
];
