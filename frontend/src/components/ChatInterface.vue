<template>
  <div class="chat-container">
    <div class="chat-header">
      <el-button type="primary" plain size="small" @click="startNewChat">
        新对话
      </el-button>
      <el-button type="danger" plain size="small" @click="clearChat">
        清空对话
      </el-button>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(message, index) in chatStore.messages" 
           :key="index" 
           :class="['message-wrapper', message.role]">
        <el-card class="message-card" :body-style="{ padding: '10px' }">
          <div class="message-header">
            <el-avatar :size="24" :icon="message.role === 'user' ? 'User' : 'Assistant'" />
            <span class="role-name">{{ message.role === 'user' ? '用户' : 'AI助手' }}</span>
          </div>
          <MessageContent 
            v-if="message.blocks" 
            :blocks="message.blocks"
          />
          <div v-else class="message-content">{{ message.content }}</div>
        </el-card>
      </div>
    </div>
    
    <div class="chat-input">
      <el-input
        v-model="userInput"
        type="textarea"
        :rows="3"
        placeholder="输入您的问题..."
        :disabled="!configStore.apiKey"
        @keyup.ctrl.enter="sendMessage"
      />
      <div class="input-footer">
        <span class="hint">Ctrl + Enter 发送</span>
        <el-button 
          type="primary" 
          @click="sendMessage"
          :loading="loading"
          :disabled="!configStore.apiKey || loading"
        >
          {{ loading ? '发送中...' : '发送' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, inject, onMounted } from 'vue'
import { useConfigStore } from '../stores/config'
import { useChatStore } from '../stores/chat'
import type { ChatMessage, Config } from '../types'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import MessageContent from './MessageContent.vue'

const configStore = useConfigStore()
const chatStore = useChatStore()
const userInput = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const terminal = inject('terminal')

onMounted(() => {
  if (terminal?.value) {
    terminal.value.addLog('system', '聊天界面已就绪')
  }
})

// 如果没有会话ID，创建新会话
if (!chatStore.conversationId) {
  chatStore.startNewConversation()
}

// 滚动到最新消息
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动
watch(() => chatStore.messages.length, scrollToBottom)

// 开始新对话
const startNewChat = async () => {
  if (chatStore.messages.length > 0) {
    try {
      await ElMessageBox.confirm(
        '开始新对话将清空当前对话记录，是否继续？',
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
      chatStore.startNewConversation()
    } catch {
      // 用户取消操作
    }
  } else {
    chatStore.startNewConversation()
  }
}

// 清空对话
const clearChat = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有对话记录吗？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    chatStore.clearMessages()
  } catch {
    // 用户取消操作
  }
}

// 添加错误重试处理
const handleExecutionError = async (error: string) => {
  const retryMessage = `
执行上一个命令时遇到错误：
${error}

请提供新的解决方案，直接给出可执行的命令。
注意：
1. 我使用的是Windows系统
2. 保存路径是：${configStore.savePath}
3. 请直接给出命令，不需要解释
`;

  try {
    if (terminal?.value) {
      terminal.value.addLog('info', '请求AI处理错误', { error });
    }

    const config: Config = {
      apiKey: configStore.apiKey,
      apiUrl: configStore.apiUrl,
      model: configStore.model,
      savePath: configStore.savePath
    };

    const response = await axios.post('/api/chat', {
      message: retryMessage,
      config,
      conversationId: chatStore.conversationId,
      isRetry: true  // 标记这是一个重试请求
    });

    if (terminal?.value) {
      terminal.value.addLog('success', '收到AI的新解决方案', response.data);
    }

    // 添加AI的响应到对话
    chatStore.addMessage({
      role: 'assistant',
      content: response.data.message,
      blocks: response.data.blocks
    });

  } catch (retryError: any) {
    if (terminal?.value) {
      terminal.value.addLog('error', '重试失败', retryError);
    }
    ElMessage.error('重试失败，请手动处理或开始新的对话');
  }
};

// 修改原有的 sendMessage 函数
const sendMessage = async () => {
  if (!userInput.value.trim()) return
  if (!configStore.apiKey) {
    ElMessage.warning('请先配置API Key')
    return
  }
  
  loading.value = true
  const inputContent = userInput.value.trim()
  userInput.value = '' // 提前清空输入框
  
  const currentMessage: ChatMessage = {
    role: 'user',
    content: inputContent
  }
  
  chatStore.addMessage(currentMessage)
  
  try {
    if (terminal?.value) {
      terminal.value.addLog('info', '发送消息到服务器', {
        message: inputContent,
        model: configStore.model
      })
    }

    console.log('Sending request to backend:', {
      message: inputContent,
      apiUrl: configStore.apiUrl,
      model: configStore.model
    });

    const config: Config = {
      apiKey: configStore.apiKey,
      apiUrl: configStore.apiUrl,
      model: configStore.model, // 添加模型参数
      savePath: configStore.savePath
    }
    
    const response = await axios.post('/api/chat', {
      message: currentMessage.content,
      config,
      conversationId: chatStore.conversationId
    }, {
      timeout: 30000, // 30秒超时
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    console.log('Received response:', response.data);

    if (terminal?.value) {
      terminal.value.addLog('success', '收到服务器响应', response.data)
    }

    // 检查执行结果
    if (response.data.blocks) {
      for (const block of response.data.blocks) {
        if (block.type === 'command' && block.result?.error) {
          // 如果命令执行失败，自动重试
          await handleExecutionError(block.result.error);
          return;  // 退出当前函数，等待重试结果
        }
      }
    }

    // 如果没有错误，正常添加消息
    chatStore.addMessage({
      role: 'assistant',
      content: response.data.message,
      blocks: response.data.blocks
    });
  } catch (error: any) {
    console.error('发送消息失败:', error);
    
    const errorMessage = error.response?.data?.details || error.message || '未知错误'
    ElMessage.error(`发送消息失败: ${errorMessage}`)
    
    chatStore.addMessage({
      role: 'assistant',
      content: `错误: ${errorMessage}`
    });

    if (terminal?.value) {
      terminal.value.addLog('error', '发送消息失败', error)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 10px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  gap: 10px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message-wrapper {
  margin: 10px 0;
}

.message-wrapper.user {
  margin-left: 20%;
}

.message-wrapper.assistant {
  margin-right: 20%;
}

.message-card {
  background-color: #fff;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.role-name {
  margin-left: 8px;
  font-weight: 500;
}

.message-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-input {
  padding: 20px;
  border-top: 1px solid #eee;
  background-color: #fff;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.hint {
  color: #909399;
  font-size: 12px;
}

.el-button {
  min-width: 100px;
}
</style> 