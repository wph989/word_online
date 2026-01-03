// 简化版的 Content 定义，兼容 TS 编译
export interface Content {
  blocks: any[];
}

export interface Mark {
    type: string;
    [key: string]: any;
}
