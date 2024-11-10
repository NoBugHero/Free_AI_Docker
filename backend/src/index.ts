import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import { ChatController } from './controllers/ChatController';

// 声明全局 WebSocket 实例
declare global {
  var io: Server | undefined;
}

const app = express();
const httpServer = createServer(app);

// CORS 配置
const corsOptions = {
  origin: ['http://localhost:5173', 'http://127.0.0.1:5173'],
  methods: ['GET', 'POST'],
  credentials: true
};

app.use(cors(corsOptions));
app.use(express.json());

// WebSocket 配置
const io = new Server(httpServer, {
  cors: corsOptions
});

// 设置全局 io 实例
global.io = io;

// 聊天路由
app.post('/api/chat', ChatController.handleChat);

// WebSocket连接
io.on('connection', (socket) => {
  console.log('Client connected');
  
  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
});

// 错误处理中间件
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Global error:', err);
  global.io?.emit('terminal-log', {
    type: 'error',
    message: '服务器错误',
    details: err.message
  });
  
  res.status(500).json({
    error: '服务器错误',
    details: err.message
  });
});

const PORT = process.env.PORT || 3000;
httpServer.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  global.io?.emit('terminal-log', {
    type: 'system',
    message: `服务器启动在端口 ${PORT}`
  });
});

// 优雅关闭
process.on('SIGTERM', () => {
  httpServer.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
}); 