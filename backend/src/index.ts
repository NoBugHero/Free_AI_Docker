import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { Server } from 'socket.io';
import apiRouter from './routes/api';

const app = express();
const httpServer = createServer(app);

// 配置 CORS
const corsOptions = {
  origin: ["http://localhost:5173"],
  methods: ["GET", "POST"],
  credentials: true,
  allowedHeaders: ['Content-Type']
};

app.use(cors(corsOptions));

// 配置 Socket.IO
const io = new Server(httpServer, {
  cors: corsOptions,
  pingTimeout: 60000,
  pingInterval: 25000,
  transports: ['websocket', 'polling'],
  path: '/socket.io'
});

export { io };

const port = 3000;

// 中间件
app.use(express.json());

// 使用路由
app.use('/api', apiRouter);

// WebSocket 连接处理
io.on('connection', (socket) => {
  console.log('Client connected:', {
    id: socket.id,
    transport: socket.conn.transport.name
  });

  socket.on('disconnect', (reason) => {
    console.log('Client disconnected:', {
      id: socket.id,
      reason: reason
    });
  });

  socket.on('error', (error) => {
    console.error('Socket error:', {
      id: socket.id,
      error: error
    });
  });
});

// 错误处理中间件
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err);
  res.status(500).json({
    success: false,
    message: err.message || '服务器内部错误'
  });
});

httpServer.listen(port, () => {
  console.log(`Server running on port ${port}`);
});