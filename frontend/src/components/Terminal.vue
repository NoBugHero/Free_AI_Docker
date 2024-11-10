<template>
  <div class="terminal">
    <div class="terminal-header">
      <span>终端日志</span>
      <div class="terminal-controls">
        <el-button size="small" type="primary" @click="clearLogs">
          清空日志
        </el-button>
      </div>
    </div>
    <div class="terminal-window" ref="terminalWindow">
      <div v-for="(log, index) in logs" :key="index" :class="['log-entry', log.type]">
        <div class="timestamp">{{ log.timestamp }}</div>
        <div class="content">
          <span class="prefix">{{ getPrefix(log.type) }}</span>
          <span class="message">{{ log.message }}</span>
        </div>
        <div v-if="log.details" class="details">
          {{ JSON.stringify(log.details, null, 2) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

interface LogEntry {
  type: 'info' | 'error' | 'success' | 'system'
  message: string
  details?: any
  timestamp: string
}

const logs = ref<LogEntry[]>([])
const terminalWindow = ref<HTMLElement | null>(null)

const getPrefix = (type: string) => {
  switch (type) {
    case 'info': return '[INFO]'
    case 'error': return '[ERROR]'
    case 'success': return '[SUCCESS]'
    case 'system': return '[SYSTEM]'
    default: return '[LOG]'
  }
}

const addLog = (type: LogEntry['type'], message: string, details?: any) => {
  logs.value.push({
    type,
    message,
    details,
    timestamp: new Date().toLocaleTimeString()
  })
  scrollToBottom()
}

const scrollToBottom = async () => {
  await nextTick()
  if (terminalWindow.value) {
    terminalWindow.value.scrollTop = terminalWindow.value.scrollHeight
  }
}

const clearLogs = () => {
  logs.value = []
}

// 暴露方法供外部使用
defineExpose({
  addLog,
  clearLogs
})
</script>

<style scoped>
.terminal {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #1e1e1e;
  border-radius: 4px;
  overflow: hidden;
}

.terminal-header {
  padding: 8px 12px;
  background-color: #2d2d2d;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.terminal-window {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.4;
}

.log-entry {
  margin-bottom: 8px;
  color: #fff;
}

.log-entry .timestamp {
  color: #666;
  font-size: 0.9em;
  margin-right: 8px;
}

.log-entry .content {
  display: flex;
  gap: 8px;
}

.log-entry .prefix {
  color: #666;
}

.log-entry.info .prefix {
  color: #3498db;
}

.log-entry.error .prefix {
  color: #e74c3c;
}

.log-entry.success .prefix {
  color: #2ecc71;
}

.log-entry.system .prefix {
  color: #f1c40f;
}

.log-entry .details {
  margin-top: 4px;
  padding-left: 24px;
  color: #666;
  white-space: pre-wrap;
}
</style> 