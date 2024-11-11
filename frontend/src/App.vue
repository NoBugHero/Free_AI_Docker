<script setup lang="ts">
import ConfigPanel from './components/ConfigPanel.vue'
import ChatInterface from './components/ChatInterface.vue'
import Terminal from './components/Terminal.vue'
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1>Free AI Docker</h1>
    </header>

    <div class="config-section">
      <ConfigPanel />
    </div>

    <!-- 主要内容区域，固定高度 -->
    <div class="main-content">
      <div class="chat-section">
        <ChatInterface />
      </div>
      <div class="terminal-section">
        <Terminal />
      </div>
    </div>
  </div>
</template>

<style>
/* 重置基础样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Arial, sans-serif;
  background-color: #f5f5f5;
}

/* 应用容器 */
.app-container {
  height: 140vh; /* 使用视口高度 */
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 12px; /* 减小间距 */
  overflow: hidden; /* 防止整体滚动 */
}

/* 头部样式 */
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background-color: #4a9eff;
  color: white;
  border-radius: 8px;
}

/* 配置区域 - 减小高度 */
.config-section {
  width: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  max-height: 250px; /* 限制最大高度 */
  overflow-y: none; /* 如果内容过多允许滚动 */
}

/* 主要内容区域 - 固定高度并允许子元素滚动 */
.main-content {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0; /* 重要：允许flex子项收缩 */
  overflow: hidden; /* 防止内容溢出 */
}

/* 聊天区域 */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden; /* 确保内容在容器内滚动 */
}

/* 终端区域 */
.terminal-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden; /* 确保内容在容器内滚动 */
}
</style>
