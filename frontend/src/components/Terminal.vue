<template>
  <div class="terminal">
    <div class="terminal-header">
      <h3>终端日志</h3>
      <button @click="clearLogs" class="clear-btn">清空日志</button>
    </div>
    <div class="terminal-content" ref="terminalContent">
      <pre v-for="(log, index) in logs" :key="index" :class="getLogClass(log)">{{ log }}</pre>
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
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.4;
}

pre {
  margin: 0;
  padding: 2px 0;
  white-space: pre-wrap;
  word-wrap: break-word;
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
</style>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { io } from 'socket.io-client';

const logs = ref<string[]>([]);
const terminalContent = ref<HTMLElement | null>(null);
const socket = io('http://localhost:3000', {
  withCredentials: true,
  transports: ['websocket', 'polling']
});

// 添加连接状态处理
socket.on('connect', () => {
  addLog('WebSocket connected');
});

socket.on('connect_error', (error) => {
  console.error('WebSocket connection error:', error);
  addLog('WebSocket connection error');
});

// 接收实时命令输出
socket.on('command-output', (output: string) => {
  addLog(output);
});

// 组件卸载时断开连接
onUnmounted(() => {
  socket.disconnect();
});

// 添加日志
const addLog = (log: string) => {
  logs.value.push(log);
  setTimeout(() => {
    if (terminalContent.value) {
      terminalContent.value.scrollTop = terminalContent.value.scrollHeight;
    }
  }, 0);
};

// 清空日志
const clearLogs = () => {
  logs.value = [];
};

// 日志类型判断
const getLogClass = (log: string) => {
  if (log.includes('ERROR') || log.includes('error')) return 'log-error';
  if (log.includes('SUCCESS') || log.includes('success')) return 'log-success';
  if (log.includes('INFO') || log.includes('info')) return 'log-info';
  if (log.includes('WARN') || log.includes('warning')) return 'log-warning';
  if (log.startsWith('$') || log.startsWith('>')) return 'log-command';
  return 'log-default';
};

onMounted(() => {
  addLog('PowerShell Terminal initialized...');
  addLog('Ready for commands...');
});
</script>