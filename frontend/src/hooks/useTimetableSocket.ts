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
  const isExplicitlyClosedRef = useRef(false);

  // Keep references to callback and queryClient to prevent reconnects on parent re-renders
  const onEventRef = useRef(onEvent);
  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const queryClientRef = useRef(queryClient);
  useEffect(() => {
    queryClientRef.current = queryClient;
  }, [queryClient]);

  useEffect(() => {
    if (!versionId || !enabled) {
      if (socketRef.current) {
        isExplicitlyClosedRef.current = true;
        socketRef.current.close();
        socketRef.current = null;
      }
      setIsConnected(false);
      return;
    }

    isExplicitlyClosedRef.current = false;

    const connect = () => {
      // Avoid reconnecting if already open or connecting to this version
      if (
        socketRef.current &&
        (socketRef.current.readyState === WebSocket.OPEN ||
          socketRef.current.readyState === WebSocket.CONNECTING)
      ) {
        return;
      }

      // Clear any pending reconnect timer
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.port === '5173' ? 'localhost:8000' : window.location.host;
      const wsUrl = `${protocol}//${host}/ws/timetable/${versionId}/`;

      try {
        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;

        ws.onopen = () => {
          if (!isExplicitlyClosedRef.current) {
            setIsConnected(true);
            retryCountRef.current = 0;
          }
        };

        ws.onmessage = (event) => {
          try {
            const data: WebSocketTimetableEvent = JSON.parse(event.data);
            setLastEvent(data);

            // Auto-sync TanStack query cache on any meeting or schedule changes
            if (data.type?.startsWith('meeting.') || data.type?.startsWith('schedule.')) {
              queryClientRef.current.invalidateQueries({ queryKey: ['timetable-grid', versionId] });
              queryClientRef.current.invalidateQueries({ queryKey: ['timetable-versions'] });
            }

            if (onEventRef.current) {
              onEventRef.current(data);
            }
          } catch (err) {
            console.error('Error parsing WebSocket message', err);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          // Only attempt reconnect if socket was not intentionally closed
          if (!isExplicitlyClosedRef.current) {
            const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 16000);
            retryCountRef.current += 1;
            reconnectTimeoutRef.current = setTimeout(() => {
              if (!isExplicitlyClosedRef.current) {
                connect();
              }
            }, delay);
          }
        };

        ws.onerror = () => {
          // Handled via onclose
        };
      } catch {
        setIsConnected(false);
      }
    };

    connect();

    return () => {
      isExplicitlyClosedRef.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setIsConnected(false);
    };
  }, [versionId, enabled]);

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
