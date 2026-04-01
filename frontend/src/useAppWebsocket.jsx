import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';

const WEBSOCKET_URL = import.meta.env.VITE_API_URL 
  ? import.meta.env.VITE_API_URL.replace('http', 'ws') + '/ws/'
  : 'ws://localhost:8000/ws/';

export function useAppWebsocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(WEBSOCKET_URL);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        setLastMessage(payload);
        
        // Push notification alerts
        if (payload.type === 'position_opened') {
          toast.success(payload.data, { theme: 'dark', hideProgressBar: true });
        } else if (payload.type === 'position_closed') {
          toast.info(payload.data, { theme: 'dark', hideProgressBar: true });
        }
      } catch (e) {
        console.error('WS parse error', e);
      }
    };

    return () => ws.close();
  }, []);

  return { isConnected, lastMessage };
}
