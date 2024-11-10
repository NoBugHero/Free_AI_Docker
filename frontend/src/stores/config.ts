import { defineStore } from 'pinia'

interface ConfigState {
  apiKey: string
  apiUrl: string
  model: string
  savePath: string
}

export const useConfigStore = defineStore({
  id: 'config',
  state: (): ConfigState => ({
    apiKey: '',
    apiUrl: '',
    model: 'qwen-turbo',
    savePath: ''
  }),
  
  actions: {
    updateConfig(config: ConfigState) {
      this.apiKey = config.apiKey
      this.apiUrl = config.apiUrl
      this.model = config.model
      this.savePath = config.savePath
    }
  },
  
  persist: true
})