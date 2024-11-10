export interface Config {
  apiKey: string
  apiUrl?: string
  model: string
  savePath: string
}

export interface MessageBlock {
  type: 'text' | 'code' | 'command'
  content: string
  language?: string
  path?: string
  result?: {
    success: boolean
    output?: string
    error?: string
  }
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  blocks?: MessageBlock[]
} 