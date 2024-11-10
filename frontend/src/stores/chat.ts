import { defineStore } from 'pinia'
import type { ChatMessage } from '../types'

interface ChatState {
  messages: ChatMessage[]
  conversationId: string | null
}

export const useChatStore = defineStore({
  id: 'chat',
  state: (): ChatState => ({
    messages: [],
    conversationId: null
  }),
  
  actions: {
    addMessage(message: ChatMessage) {
      this.messages.push(message)
    },
    
    clearMessages() {
      this.messages = []
      this.conversationId = null
    },
    
    startNewConversation() {
      this.conversationId = new Date().getTime().toString()
      this.messages = []
    }
  },
  
  persist: {
    key: 'chat-history',
    storage: localStorage
  }
}) 