import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { Server } from 'socket.io';
import apiRouter from './routes/api';

const app = express();
const httpServer = createServer(app);

// 确保在所有中间件之前初始化 Socket.IO
const io = new Server(httpServer, {
  cors: {
    origin: "http://localhost:5173",
    methods: ["GET", "POST"],
    credentials: true
  }
});

// 导出 io 实例以供其他模块使用
export { io };

const port = 3000;

// 中间件
app.use(cors({
  origin: "http://localhost:5173",
  credentials: true
}));
app.use(express.json());

// 使用路由
app.use('/api', apiRouter);

// WebSocket 连接处理
io.on('connection', (socket) => {
  console.log('Client connected');

  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
});

// 错误处理中间件
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err);
  res.status(500).json({
    success: false,
    message: '服务器内部错误'
  });
});

// 使用 httpServer 而不是 app 来监听
httpServer.listen(port, () => {
  console.log(`Server running on port ${port}`);
});