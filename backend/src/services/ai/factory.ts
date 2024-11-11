import { AIProvider, AIModelConfig } from './types';
import { QwenProvider } from './providers/qwen';
import { OpenAIProvider } from './providers/openai';
import { GeminiProvider } from './providers/gemini';

export class AIProviderFactory {
  private static providers: Map<string, AIProvider> = new Map();

  static {
    // 注册所有支持的AI提供者
    this.providers.set('qwen', new QwenProvider());
    this.providers.set('openai', new OpenAIProvider());
    this.providers.set('gemini', new GeminiProvider());
  }

  static getProvider(config: AIModelConfig): AIProvider {
    // 根据模型名称或URL判断使用哪个提供者
    if (config.apiUrl.includes('dashscope.aliyuncs.com')) {
      return this.providers.get('qwen')!;
    }
    if (config.apiUrl.includes('api.openai.com')) {
      return this.providers.get('openai')!;
    }
    if (config.apiUrl.includes('generativelanguage.googleapis.com')) {
      return this.providers.get('gemini')!;
    }

    throw new Error('Unsupported AI provider');
  }
} 