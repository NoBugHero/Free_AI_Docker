import { AIProvider, AIModelConfig, AIResponse, Message } from '../types';

export class OllamaProvider implements AIProvider {
  async sendMessage(messages: Message[], config: AIModelConfig): Promise<AIResponse> {
    try {
      console.log('Sending request to Ollama:', {
        url: config.apiUrl,
        model: config.model,
        messages: messages
      });

      const response = await fetch(config.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: config.model,
          messages: messages.map(msg => ({
            role: msg.role === 'system' ? 'system' : msg.role === 'assistant' ? 'assistant' : 'user',
            content: msg.content
          })),
          stream: true,
          format: 'json',
          options: {
            temperature: 0.7
          }
        })
      });

      if (!response.ok) {
        const error = await response.text();
        console.error('Ollama API error:', error);
        throw new Error(`Ollama API request failed: ${error}`);
      }

      console.log('Ollama response headers:', 
        Array.from(response.headers.entries())
      );

      return {
        success: true,
        content: '',
        stream: response.body
      };
    } catch (error: any) {
      console.error('Ollama error:', error);
      return {
        success: false,
        content: '',
        error: error.message
      };
    }
  }
} 