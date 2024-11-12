<template>
  <div class="terminal">
    <div class="terminal-header">
      <h3>终端日志</h3>
      <button @click="clearLogs" class="clear-btn">清空日志</button>
    </div>
    <div class="terminal-content" ref="terminalContent">
      <pre v-for="(log, index) in logs" 
           :key="index" 
           :class="[getLogClass(log), { 'streaming': log.isStreaming }]"
      >{{ log.content }}</pre>
    </div>
  </div>
</template>

<style scoped>
.terminal {
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.terminal-header {
  padding: 10px;
  background: #252526;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.terminal-header h3 {
  color: #fff;
  margin: 0;
}

.terminal-content {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
  font-family: 'Consolas', 'Microsoft YaHei Mono', monospace;
  font-size: 14px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-wrap: break-word;
}

pre {
  margin: 2px 0;
  padding: 2px 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', 'Microsoft YaHei Mono', monospace;
}

/* VS Code 风格的配色 */
.log-default {
  color: #d4d4d4;
}

.log-error {
  color: #f48771;
}

.log-success {
  color: #89d185;
}

.log-info {
  color: #569cd6;
}

.log-warning {
  color: #dcdcaa;
}

.log-command {
  color: #c586c0;
}

.clear-btn {
  padding: 4px 8px;
  background: #4d4d4d;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.clear-btn:hover {
  background: #666;
}

.streaming {
  border-left: 2px solid #4a9eff;
  padding-left: 8px;
}
</style>

<script setup lang="ts">
interface TerminalLog {
  content: string;
  isStreaming: boolean;
}

import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { io, Socket } from 'socket.io-client';

const logs = ref<TerminalLog[]>([]);
const terminalContent = ref<HTMLElement | null>(null);
let socket: Socket | null = null;

// 修改 socket 初始化函数
const initSocket = () => {
  if (socket) {
    socket.disconnect();
  }

  socket = io('http://localhost:3000', {  // 使用完整的服务器 URL
    transports: ['websocket'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    autoConnect: true,
    withCredentials: true
  });

  // 添加事件监听
  socket.on('connect', () => {
    console.log('WebSocket connected:', socket?.id);
    addLog('PowerShell Terminal initialized...');
    addLog('Ready for commands...');
    addLog(`WebSocket connected: ${socket?.id}`);
  });

  socket.on('disconnect', (reason) => {
    console.log('WebSocket disconnected:', reason);
    addLog(`WebSocket disconnected: ${reason}`);
    
    // 自动重连
    setTimeout(() => {
      console.log('Attempting to reconnect...');
      initSocket();  // 重新初始化连接
    }, 2000);
  });

  socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    addLog(`Connection error: ${error.message}`);
  });

  socket.on('command-output', (output: string) => {
    console.log('Received command output:', output);
    addLog(output);
  });

  socket.on('error', (error: Error) => {
    console.error('Socket error:', error);
    addLog(`Socket error: ${error.message}`);
  });

  // 添加心跳检测
  const heartbeat = setInterval(() => {
    if (socket?.connected) {
      socket.emit('ping');
    }
  }, 30000);

  // 清理心跳定时器
  socket.on('disconnect', () => {
    clearInterval(heartbeat);
  });
};

// 修改 addLog 函数
const addLog = (message: string) => {
  try {
    console.log('Adding log:', message);

    // 如果最后一条日志是流式内容，则追加
    if (logs.value.length > 0 && logs.value[logs.value.length - 1].isStreaming) {
      logs.value[logs.value.length - 1].content += '\n' + message;
    } else {
      // 否则创建新的日志条目
      logs.value.push({
        content: message,
        isStreaming: message.startsWith('>')  // 命令开始标记
      });
    }

    // 确保滚动到底部
    nextTick(() => {
      if (terminalContent.value) {
        terminalContent.value.scrollTop = terminalContent.value.scrollHeight;
      }
    });
  } catch (error: unknown) {
    console.error('Error in addLog:', error);
    logs.value.push({
      content: `Error processing log: ${error instanceof Error ? error.message : 'Unknown error'}`,
      isStreaming: false
    });
  }
};

// 清空日志
const clearLogs = () => {
  logs.value = [];
};

// 修改 getLogClass 函数
const getLogClass = (log: TerminalLog) => {
  const content = log.content.toLowerCase();
  if (content.includes('error')) return 'log-error';
  if (content.includes('success')) return 'log-success';
  if (content.includes('info')) return 'log-info';
  if (content.includes('warn')) return 'log-warning';
  if (content.startsWith('>')) return 'log-command';
  return 'log-default';
};

onMounted(() => {
  console.log('Terminal component mounted');
  initSocket();
});

onUnmounted(() => {
  console.log('Terminal component unmounting');
  if (socket) {
    socket.disconnect();
    socket = null;
  }
});
</script>