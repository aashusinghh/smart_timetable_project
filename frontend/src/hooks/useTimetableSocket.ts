import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WebSocketTimetableEvent } from '../types';

interface UseTimetableSocketOptions {
  onEvent?: (event: WebSocketTimetableEvent) => void;
  enabled?: boolean;
}

export function useTimetableSocket(versionId?: number, options: UseTimetableSocketOptions = {}) {
  const { onEvent, enabled = true } = options;
  const queryClient = useQueryClient();

  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<WebSocketTimetableEvent | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const retryCountRef = useRef(0);

  const connect = useCallback(() => {
    if (!versionId || !enabled) return;

    // Clean up existing socket
    if (socketRef.current) {
      socketRef.current.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use backend port 8000 for development Vite proxy or window.location.host
    const host = window.location.port === '5173' ? 'localhost:8000' : window.location.host;
    const wsUrl = `${protocol}//${host}/ws/timetable/${versionId}/`;

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        retryCountRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketTimetableEvent = JSON.parse(event.data);
          setLastEvent(data);

          // Auto-sync TanStack query cache on any meeting or schedule changes
          if (data.type?.startsWith('meeting.') || data.type?.startsWith('schedule.')) {
            queryClient.invalidateQueries({ queryKey: ['timetable-grid', versionId] });
            queryClient.invalidateQueries({ queryKey: ['timetable-versions'] });
          }

          if (onEvent) {
            onEvent(data);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Exponential backoff reconnect: 1s, 2s, 4s, 8s, up to 16s
        const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 16000);
        retryCountRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      setIsConnected(false);
    }
  }, [versionId, enabled, queryClient, onEvent]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((msg: any) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return {
    isConnected,
    lastEvent,
    sendMessage,
  };
}
