<template>
  <div class="chat-interface">
    <div class="chat-header">
      <h3>AI 对话</h3>
      <div class="chat-actions">
        <button @click="clearChat" class="action-btn">清空对话</button>
        <button @click="newChat" class="action-btn">新建对话</button>
      </div>
    </div>
    
    <!-- 聊天消息区域 -->
    <div class="messages-container" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" class="message" :class="getMessageClass(message)">
        <div class="message-header">
          {{ getMessageHeader(message) }}
        </div>
        <div class="message-content" style="white-space: pre-wrap;">
          {{ message.content }}
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <textarea 
        v-model="inputMessage"
        :disabled="isLoading"
        placeholder="输入您的问题..."
        @keydown.ctrl.enter="sendMessage"
      ></textarea>
      <div class="input-actions">
        <span class="hint">Ctrl + Enter 发送</span>
        <button 
          @click="sendMessage" 
          :disabled="isLoading"
          class="send-btn"
        >
          {{ isLoading ? '发送中...' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
}

.chat-header {
  padding: 12px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 4px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.action-btn:hover {
  background: #f5f5f5;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  margin-bottom: 20px;
  padding: 12px;
  border-radius: 8px;
  background: #f9f9f9;
}

.message-header {
  font-weight: bold;
  margin-bottom: 8px;
}

.input-area {
  border-top: 1px solid #eee;
  padding: 20px;
}

textarea {
  width: 100%;
  height: 80px;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.hint {
  color: #666;
  font-size: 12px;
}

.send-btn {
  padding: 6px 16px;
  background: #4a9eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.send-btn:hover {
  background: #3d8be0;
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

textarea:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

/* 添加消息类型样式 */
.message.user {
  background: #f0f7ff;
  margin-left: 20%;
}

.message.assistant {
  background: #f5f5f5;
  margin-right: 20%;
}

.message-content {
  font-family: 'Consolas', 'Monaco', monospace;
  line-height: 1.5;
}

/* 添加新的消息类型样式 */
.message.user-request {
  background: #e3f2fd;
  margin-left: 20%;
}

.message.system-result {
  background: #f5f5f5;
  border-left: 4px solid #4caf50;
}

.message.system-error {
  background: #fbe9e7;
  border-left: 4px solid #f44336;
}

.message.system-prompt {
  background: #fff3e0;
  border-left: 4px solid #ff9800;
}

.message.ai-response {
  background: #f3e5f5;
  margin-right: 20%;
  border-left: 4px solid #9c27b0;
}
</style>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';

const messages = ref<Array<{role: string, content: string}>>([]);
const inputMessage = ref('');
const messagesContainer = ref<HTMLElement | null>(null);
const isLoading = ref(false);

// 添加滚动到底部函数
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 添加处理流式响应的函数
const handleStreamResponse = (data: { type: string, content: string }) => {
  console.log('Handling stream response:', data);

  switch (data.type) {
    case 'ai-response':
      // 如果最后一条消息是 AI 的回复，则追加内容
      if (messages.value.length > 0 && messages.value[messages.value.length - 1].role === 'assistant') {
        messages.value[messages.value.length - 1].content += data.content;
      } else {
        // 否则创建新的 AI 回复消息
        messages.value.push({
          role: 'assistant',
          content: data.content
        });
      }
      // 修改这里：立即检查是否包含完成标记并重置状态
      if (data.content.includes('[COMPLETE]')) {
        isLoading.value = false;
        // 确保输入框和按钮状态被重置
        nextTick(() => {
          inputMessage.value = '';
        });
      }
      break;

    case 'execution-result':
      messages.value.push({
        role: 'system',
        content: data.content
      });
      break;

    case 'error':
      messages.value.push({
        role: 'system',
        content: `错误: ${data.content}`
      });
      isLoading.value = false;  // 发生错误时重置状态
      break;

    default:
      console.warn('Unknown response type:', data.type);
  }

  scrollToBottom();
};

// 修改发送消息函数
const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;
  
  const userMessage = inputMessage.value;
  messages.value.push({
    role: 'user',
    content: userMessage
  });
  
  inputMessage.value = '';
  isLoading.value = true;
  scrollToBottom();
  
  let abortController = new AbortController();
  
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: userMessage
      }),
      signal: abortController.signal
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          isLoading.value = false;  // 流结束时重置状态
          break;
        }
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue;
          
          try {
            const data = JSON.parse(line.slice(6));
            handleStreamResponse(data);
          } catch (e) {
            console.error('Error parsing SSE data:', e);
          }
        }
      }
    } catch (error) {
      console.error('Error reading stream:', error);
      isLoading.value = false;  // 读取流错误时重置状态
      throw error;
    }
  } catch (error) {
    console.error('Error sending message:', error);
    messages.value.push({
      role: 'system',
      content: `错误: ${error instanceof Error ? error.message : 'network error'}`
    });
    isLoading.value = false;  // 发生错误时重置状态
  }
};

// 清空对话
const clearChat = () => {
  messages.value = [];
};

// 新建对话
const newChat = () => {
  clearChat();
};

// 获取消息类型样式
const getMessageClass = (message: { role: string, content: string }) => {
  if (message.content.startsWith('用户请求：')) return 'user-request';
  if (message.content.startsWith('系统执行结果：')) return 'system-result';
  if (message.content.startsWith('系统执行错误：')) return 'system-error';
  if (message.content.startsWith('系统提示：')) return 'system-prompt';
  if (message.role === 'assistant') return 'ai-response';
  return 'user';
};

// 获取消息头部文本
const getMessageHeader = (message: { role: string, content: string }) => {
  if (message.content.startsWith('用户请求：')) return '用户';
  if (message.content.startsWith('系统执行结果：')) return '系统';
  if (message.content.startsWith('系统执行错误：')) return '系统错误';
  if (message.content.startsWith('系统提示：')) return '系统';
  if (message.role === 'assistant') return 'AI助手';
  return '用户';
};

// 组件挂载时设置滚动容器引用
onMounted(() => {
  scrollToBottom();
});
</script> 