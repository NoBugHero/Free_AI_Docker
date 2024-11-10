<template>
  <el-form :model="config" label-width="120px">
    <el-form-item label="API Key">
      <el-input v-model="config.apiKey" type="password" show-password />
    </el-form-item>
    
    <el-form-item label="API URL">
      <el-select v-model="selectedApi" placeholder="选择API类型" @change="handleApiChange">
        <el-option label="通义千问" value="qwen" />
      </el-select>
      <el-input 
        v-model="config.apiUrl" 
        :placeholder="apiPlaceholder"
      />
    </el-form-item>

    <el-form-item label="模型">
      <el-input 
        v-model="config.model" 
        placeholder="输入模型名称，如：qwen-turbo"
      >
        <template #append>
          <el-tooltip 
            content="常用模型：qwen-turbo, qwen-plus, qwen-max, qwen-max-1201, qwen-max-longcontext" 
            placement="top"
          >
            <el-icon><QuestionFilled /></el-icon>
          </el-tooltip>
        </template>
      </el-input>
    </el-form-item>
    
    <el-form-item label="保存路径">
      <el-input v-model="config.savePath" />
    </el-form-item>
    
    <el-form-item>
      <el-button type="primary" @click="saveConfig">保存配置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useConfigStore } from '../stores/config'
import { ElMessage } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import type { Config } from '../types'

const configStore = useConfigStore()
const selectedApi = ref('qwen')

const config = reactive<Config>({
  apiKey: configStore.apiKey,
  apiUrl: configStore.apiUrl || '',
  model: configStore.model || '',
  savePath: configStore.savePath
})

const apiPlaceholder = computed(() => {
  return selectedApi.value === 'qwen' 
    ? 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'
    : ''
})

const handleApiChange = (value: string) => {
  if (value === 'qwen') {
    config.apiUrl = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'
    config.model = 'qwen2.5-3b-instruct'
  }
}

const saveConfig = () => {
  if (!config.apiKey) {
    ElMessage.warning('请输入 API Key')
    return
  }
  
  if (!config.apiUrl) {
    ElMessage.warning('请输入 API URL')
    return
  }

  if (!config.model) {
    ElMessage.warning('请输入模型名称')
    return
  }

  try {
    new URL(config.apiUrl)
  } catch {
    ElMessage.warning('请输入有效的 API URL')
    return
  }
  
  const configToSave = {
    apiKey: config.apiKey,
    apiUrl: config.apiUrl || '',
    model: config.model,
    savePath: config.savePath
  }
  
  configStore.updateConfig(configToSave)
  ElMessage.success('配置已保存')
}
</script>

<style scoped>
.el-select {
  width: 100%;
  margin-bottom: 10px;
}

.el-tooltip__trigger {
  cursor: help;
}

:deep(.el-input-group__append) {
  padding: 0 10px;
}
</style> 