import { AIProvider, AIModelConfig, AIResponse, Message } from '../types';

export class GeminiProvider implements AIProvider {
  async sendMessage(messages: Message[], config: AIModelConfig): Promise<AIResponse> {
    try {
      const response = await fetch(config.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-goog-api-key': config.apiKey
        },
        body: JSON.stringify({
          contents: messages.map(msg => ({
            role: msg.role === 'assistant' ? 'model' : msg.role,
            parts: [{ text: msg.content }]
          })),
          generationConfig: {
            temperature: 0.7,
            maxOutputTokens: 1500
          }
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'API request failed');
      }

      const data = await response.json();
      return {
        success: true,
        content: data.candidates[0].content.parts[0].text
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