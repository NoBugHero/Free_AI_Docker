import express from 'express';
import { saveConfig, handleChat, getApiStatus, getConfig } from '../controllers/ChatController';

const router = express.Router();

router.post('/config', saveConfig);
router.post('/chat', handleChat);
router.get('/status', getApiStatus);
router.get('/config', getConfig);

export default router; 