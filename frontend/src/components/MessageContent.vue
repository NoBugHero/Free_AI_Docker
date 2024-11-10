<template>
  <div class="message-content">
    <template v-for="(block, index) in blocks" :key="index">
      <!-- 文本内容 -->
      <div v-if="block.type === 'text'" class="text-block">
        {{ block.content }}
      </div>
      
      <!-- 命令行 -->
      <div v-else-if="block.type === 'command'" class="command-block">
        <div class="command">
          <span class="prompt">$</span>
          {{ block.content }}
        </div>
        <div v-if="block.result" class="result">
          <div v-if="block.result.success" class="success">
            {{ block.result.output }}
          </div>
          <div v-else class="error">
            {{ block.result.error }}
          </div>
        </div>
      </div>
      
      <!-- 代码块 -->
      <div v-else-if="block.type === 'code'" class="code-block">
        <div v-if="block.path" class="code-path">
          {{ block.path }}
        </div>
        <pre><code :class="block.language">{{ block.content }}</code></pre>
        <div v-if="block.result" class="result">
          <el-tag v-if="block.result.success" type="success">文件已保存</el-tag>
          <el-tag v-else type="danger">保存失败: {{ block.result.error }}</el-tag>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { PropType } from 'vue';

interface Block {
  type: 'text' | 'code' | 'command';
  content: string;
  language?: string;
  path?: string;
  result?: {
    success: boolean;
    output?: string;
    error?: string;
  };
}

defineProps({
  blocks: {
    type: Array as PropType<Block[]>,
    required: true
  }
});
</script>

<style scoped>
.message-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.text-block {
  margin: 8px 0;
}

.command-block {
  background: #1e1e1e;
  color: #fff;
  padding: 12px;
  border-radius: 4px;
  margin: 8px 0;
  font-family: monospace;
}

.command .prompt {
  color: #0f0;
  margin-right: 8px;
}

.result {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #333;
}

.result .error {
  color: #f66;
}

.code-block {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  margin: 8px 0;
}

.code-path {
  color: #666;
  font-size: 0.9em;
  margin-bottom: 8px;
}

pre {
  margin: 0;
  padding: 12px;
  background: #1e1e1e;
  border-radius: 4px;
  overflow-x: auto;
}

code {
  font-family: monospace;
  color: #fff;
}
</style> 