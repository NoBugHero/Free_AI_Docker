<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';

const emit = defineEmits(['config-saved']);

// 定义配置对象
const config = reactive({
  apiKey: '',
  apiUrl: '',
  model: '',
  savePath: '',
  provider: 'openai'
});

const saveStatus = ref(''); // 用于显示保存状态

// 判断是否为 Ollama
const isOllama = computed(() => {
  return config.apiUrl.includes('localhost:11434') || config.apiUrl.includes('127.0.0.1:11434');
});

// 获取 URL 占位符
const getUrlPlaceholder = computed(() => {
  return '例如: http://localhost:11434/v1/chat/completions (Ollama) 或 https://api.openai.com/v1 (OpenAI)';
});

// 获取模型占位符
const getModelPlaceholder = computed(() => {
  if (isOllama.value) {
    return '例如: llama2, mistral, codellama';
  }
  return '例如: gpt-3.5-turbo (OpenAI) 或 qwen-turbo (通义千问)';
});

// 保存配置
const saveConfig = async () => {
  try {
    // 验证必填字段
    if (!config.apiUrl.trim()) {
      saveStatus.value = '请输入 API URL';
      return;
    }
    if (!config.model.trim()) {
      saveStatus.value = '请输入模型名称';
      return;
    }
    if (!config.savePath.trim()) {
      saveStatus.value = '请输入保存路径';
      return;
    }

    // 规范化 URL
    if (config.apiUrl.includes('localhost:11434') || config.apiUrl.includes('127.0.0.1:11434')) {
      if (!config.apiUrl.endsWith('/v1/chat/completions')) {
        config.apiUrl = config.apiUrl.replace(/\/+$/, '') + '/v1/chat/completions';
      }
    }

    // 如果是 Ollama，设置默认值
    if (config.apiUrl.includes('/v1/chat/completions')) {
      config.provider = 'ollama';
      if (!config.apiKey) {
        config.apiKey = 'ollama';  // 设置默认值
      }
    }

    saveStatus.value = '保存中...';
    const response = await fetch('http://localhost:3000/api/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config)
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.message || '保存失败');
    }

    localStorage.setItem('aiConfig', JSON.stringify(config));
    saveStatus.value = '保存成功';
    emit('config-saved', true);
    
    setTimeout(() => {
      saveStatus.value = '';
    }, 3000);
  } catch (error) {
    console.error('保存配置失败:', error);
    saveStatus.value = '保存失败，请重试';
    emit('config-saved', false);
  }
};

// 组件加载时读取配置
onMounted(() => {
  // 先尝试从后端获取配置
  fetch('http://localhost:3000/api/config')
    .then(res => res.json())
    .then(data => {
      if (data.config) {
        Object.assign(config, data.config);
        emit('config-saved', true);
      } else {
        // 如果后端没有配置，则尝试从localStorage读取
        const savedConfig = localStorage.getItem('aiConfig');
        if (savedConfig) {
          const parsed = JSON.parse(savedConfig);
          Object.assign(config, parsed);
        }
      }
    })
    .catch(() => {
      // 如果后端请求失败，从localStorage读取
      const savedConfig = localStorage.getItem('aiConfig');
      if (savedConfig) {
        const parsed = JSON.parse(savedConfig);
        Object.assign(config, parsed);
      }
    });
});

const isApiKeyVisible = ref(false);
const toggleApiKeyVisibility = () => {
  isApiKeyVisible.value = !isApiKeyVisible.value;
};
</script>

<template>
  <div class="config-panel">
    <div class="config-header">
      <h3>配置面板</h3>
      <span class="save-status" :class="{ 
        'success': saveStatus === '保存成功',
        'error': saveStatus === '保存失败，请重试'
      }">{{ saveStatus }}</span>
    </div>
    <div class="config-grid">
      <div class="input-group">
        <label>API Key</label>
        <div class="input-wrapper">
          <input 
            :type="isApiKeyVisible ? 'text' : 'password'"
            v-model="config.apiKey" 
            :placeholder="isOllama ? '本地 Ollama 可选填 API Key' : '请输入 API Key'"
            class="config-input"
          />
          <span class="toggle-visibility" @click="toggleApiKeyVisibility">
            👁
          </span>
        </div>
      </div>

      <div class="input-group">
        <label>API URL</label>
        <input 
          type="text" 
          v-model="config.apiUrl" 
          :placeholder="getUrlPlaceholder"
          class="config-input"
        />
      </div>

      <div class="input-group">
        <label>模型名称</label>
        <input 
          type="text" 
          v-model="config.model" 
          :placeholder="getModelPlaceholder"
          class="config-input"
        />
      </div>

      <div class="input-group">
        <label>保存路径</label>
        <input 
          type="text" 
          v-model="config.savePath" 
          placeholder="请输入文件保存路径"
          class="config-input"
        />
      </div>
    </div>
    <button @click="saveConfig" class="save-btn">保存配置</button>
  </div>
</template>

<style scoped>
.config-panel {
  padding: 15px;
  background: #fff;
  border-radius: 8px;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-bottom: 15px;
}

.input-group {
  width: 100%;
}

.input-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.config-input {
  width: 100%;
  min-width: 300px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.toggle-visibility {
  position: absolute;
  right: 10px;
  cursor: pointer;
}

.save-btn {
  margin-top: 15px;
  padding: 8px 16px;
  background: #4a9eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.save-btn:hover {
  background: #3d8be0;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.save-status {
  font-size: 14px;
}

.save-status.success {
  color: #89d185;
}

.save-status.error {
  color: #f48771;
}
</style> 