# Free AI Docker 🚀

A powerful AI-powered development tool that helps you interact with AI models and automatically execute commands and generate files.

## ✨ Features

- 🤖 **AI Integration**: Seamlessly integrate with various AI models (Qwen, OpenAI, Gemini)
- 🔄 **Auto-Execution**: Automatically parse and execute commands from AI responses
- 📁 **File Management**: Create and manage files based on AI instructions
- 🖥️ **Terminal Integration**: Real-time command execution feedback
- 🔍 **Error Handling**: Automatic error detection and retry mechanism
- 💾 **Persistent Storage**: Save chat history and configurations

## 🛠️ Tech Stack

- **Frontend**:
  - Vue 3
  - TypeScript
  - Element Plus
  - Pinia
  - Vite

- **Backend**:
  - Node.js
  - Express
  - Socket.IO
  - TypeScript

## 🚀 Getting Started

### Prerequisites

- Node.js (v18.0.0 or higher)
- npm (v9.0.0 or higher)
- PowerShell (v5.1 or higher)
- Git

### Quick Install

1. **Clone the repository**
```bash
git clone https://github.com/supersuperbruce/free-ai-docker.git
cd free-ai-docker
```

2. **Install all dependencies using requirements.txt**
```bash
# Install backend dependencies
cd backend
npm install $(cat requirements.txt | grep "Backend" -A 10 | grep -v "Backend" | grep -v "^$" | tr '\n' ' ')

# Install frontend dependencies
cd ../frontend
npm install $(cat ../requirements.txt | grep "Frontend" -A 10 | grep -v "Frontend" | grep -v "^$" | tr '\n' ' ')
```

### Manual Installation

1. **Install backend dependencies**
```bash
cd backend
npm install typescript@5.6.3 ts-node@10.9.2 ts-node-dev@2.0.0 express@4.18.2 cors@2.8.5 socket.io@4.7.4 @types/express@4.17.21 @types/cors@2.8.17 @types/node@20.11.24
```

2. **Install frontend dependencies**
```bash
cd frontend
npm install vue@3.4.19 vite@5.1.4 @vitejs/plugin-vue@5.0.4 typescript@5.6.3 @vue/tsconfig@0.5.1
```

### Development Setup

1. **Start backend server**
```bash
cd backend
npm run dev
# Server will start on http://localhost:3000
```

2. **Start frontend development server**
```bash
cd frontend
npm run dev
# Frontend will be available on http://localhost:5173
```

3. **Access the application**
- Open your browser and navigate to `http://localhost:5173`
- Configure your AI provider settings in the configuration panel

### Configuration

Configure the following in the settings panel:
- `API Key`: Your AI provider's API key
- `API URL`: The API endpoint URL
- `Model`: AI model name
- `Save Path`: Directory path for file operations

### Supported AI Providers

- **Qwen**
  - URL: https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
  - Models: qwen-turbo, qwen-plus, qwen-max

- **OpenAI**
  - URL: https://api.openai.com/v1/chat/completions
  - Models: gpt-3.5-turbo, gpt-4

- **Gemini**
  - URL: https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent
  - Models: gemini-pro

## 🔧 Configuration

1. Get your API key from the AI provider
2. Configure the API settings in the configuration panel:
   - API Key
   - API URL
   - Model Name
   - Save Path

## 💡 Usage

1. **Configure API Settings**
   - Enter your API credentials
   - Set the save path for generated files

2. **Start Chatting**
   - Type your request in the chat input
   - AI will respond and automatically execute commands
   - View execution results in the terminal panel

3. **Error Handling**
   - System automatically detects execution errors
   - AI provides alternative solutions
   - Retry mechanism ensures task completion

## 🌟 Key Features Explained

### Automatic Command Execution
The system automatically detects and executes:
- Shell commands
- Python scripts
- Batch files
- File operations

### Real-time Terminal
- View command execution in real-time
- See detailed error messages
- Track operation progress

### Error Recovery
- Automatic error detection
- AI-powered error resolution
- Smart retry mechanism

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all contributors
- Inspired by the AI development community
- Built with ❤️ using Vue.js and Node.js

## 📞 Contact

Project Link: [https://github.com/supersuperbruce/free-ai-docker](https://github.com/supersuperbruce/free-ai-docker)

---
⭐️ If you find this project fun, please consider giving it a star! 