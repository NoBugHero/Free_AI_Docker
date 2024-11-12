import { AIProvider, AIModelConfig } from './types';
import { QwenProvider } from './providers/qwen';
import { OpenAIProvider } from './providers/openai';
import { GeminiProvider } from './providers/gemini';
import { OllamaProvider } from './providers/ollama';

export class AIProviderFactory {
  private static providers: Map<string, AIProvider> = new Map();

  static {
    this.providers.set('qwen', new QwenProvider());
    this.providers.set('openai', new OpenAIProvider());
    this.providers.set('gemini', new GeminiProvider());
    this.providers.set('ollama', new OllamaProvider());
  }

  static getProvider(config: AIModelConfig): AIProvider {
    if (config.apiUrl.includes('/v1/chat/completions')) {
      return this.providers.get('ollama')!;
    }
    if (config.apiUrl.includes('localhost:11434') || config.apiUrl.includes('127.0.0.1:11434')) {
      return this.providers.get('ollama')!;
    }
    if (config.apiUrl.includes('dashscope.aliyuncs.com')) {
      return this.providers.get('qwen')!;
    }
    if (config.apiUrl.includes('api.openai.com')) {
      return this.providers.get('openai')!;
    }
    if (config.apiUrl.includes('generativelanguage.googleapis.com')) {
      return this.providers.get('gemini')!;
    }

    throw new Error('不支持的 AI 提供者');
  }
} 