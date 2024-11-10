<script setup lang="ts">
import { ref, provide } from 'vue'
import ConfigPanel from './components/ConfigPanel.vue'
import ChatInterface from './components/ChatInterface.vue'
import Terminal from './components/Terminal.vue'
import { useConfigStore } from './stores/config'

const configStore = useConfigStore()
const terminal = ref()
const chatInterface = ref()

// 提供终端实例给子组件
provide('terminal', terminal)

// 暴露终端实例，供其他组件使用
defineExpose({
  terminal
})
</script>

<template>
  <div class="app-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>Free AI Docker</h2>
          <el-tag type="success" v-if="configStore.apiKey">API已配置</el-tag>
          <el-tag type="danger" v-else>未配置API</el-tag>
        </div>
      </el-header>
      
      <el-container class="main-container">
        <el-aside width="300px">
          <el-card class="config-card">
            <template #header>
              <div class="card-header">
                <span>配置面板</span>
              </div>
            </template>
            <ConfigPanel />
          </el-card>
        </el-aside>
        
        <el-container class="content-container">
          <el-main class="chat-container">
            <el-card class="chat-card">
              <template #header>
                <div class="card-header">
                  <span>AI 对话</span>
                </div>
              </template>
              <ChatInterface ref="chatInterface" />
            </el-card>
          </el-main>
          
          <el-aside class="terminal-container" width="33%">
            <el-card class="terminal-card">
              <template #header>
                <div class="card-header">
                  <span>终端</span>
                </div>
              </template>
              <Terminal ref="terminal" />
            </el-card>
          </el-aside>
        </el-container>
      </el-container>
    </el-container>
  </div>
</template>

<style>
.app-container {
  height: 100vh;
  width: 100vw;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.el-header {
  background-color: #409EFF;
  color: white;
  line-height: 60px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);
}

.main-container {
  height: calc(100vh - 60px);
  background-color: #f0f2f5;
}

.content-container {
  display: flex;
  flex-direction: row;
}

.el-aside {
  background-color: #f0f2f5;
  padding: 20px;
}

.chat-container {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.terminal-container {
  background-color: #f0f2f5;
  padding: 20px;
  border-left: 1px solid #e6e6e6;
  width: 33% !important;
}

.config-card, .chat-card, .terminal-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-card .el-card__body,
.terminal-card .el-card__body {
  height: calc(100% - 55px);
  padding: 0;
  flex: 1;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-card__body {
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
