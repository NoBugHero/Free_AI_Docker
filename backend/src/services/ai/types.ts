// AI服务的通用类型定义
export interface AIModelConfig {
  apiKey: string;
  apiUrl: string;
  model: string;
}

export interface AIResponse {
  success: boolean;
  content: string;
  error?: string;
}

// 统一的消息格式
export interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

// AI服务提供者的抽象接口
export interface AIProvider {
  sendMessage(messages: Message[], config: AIModelConfig): Promise<AIResponse>;
} 