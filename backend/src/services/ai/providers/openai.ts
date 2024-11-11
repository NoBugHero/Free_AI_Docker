import { AIProvider, AIModelConfig, AIResponse, Message } from '../types';

export class OpenAIProvider implements AIProvider {
  async sendMessage(messages: Message[], config: AIModelConfig): Promise<AIResponse> {
    try {
      const response = await fetch(config.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${config.apiKey}`
        },
        body: JSON.stringify({
          model: config.model,
          messages: messages,
          temperature: 0.7,
          max_tokens: 1500
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'API request failed');
      }

      const data = await response.json();
      return {
        success: true,
        content: data.choices[0].message.content
      };
    } catch (error: any) {
      return {
        success: false,
        content: '',
        error: error.message
      };
    }
  }
} 