import { useState, useRef, useCallback, useEffect } from "react";

export type MessageRole = "user" | "agent";

export interface ToolCall {
  name: string;
  input: Record<string, unknown>;
  result?: Record<string, unknown>;
  status: "pending" | "done" | "error";
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  toolCalls: ToolCall[];
  timestamp: Date;
}

const WS_URL =
  import.meta.env.VITE_WS_URL ||
  `ws://${window.location.hostname}:8001/chat/ws`;

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const agentMsgRef = useRef<string | null>(null);

  const handleEvent = useCallback((event: Record<string, unknown>) => {
    switch (event.type) {
      case "tool_call": {
        const toolCall: ToolCall = {
          name: event.name as string,
          input: event.input as Record<string, unknown>,
          status: "pending",
        };

        if (!agentMsgRef.current) {
          const id = crypto.randomUUID();
          agentMsgRef.current = id;
          setMessages((prev) => [
            ...prev,
            {
              id,
              role: "agent",
              content: "",
              toolCalls: [toolCall],
              timestamp: new Date(),
            },
          ]);
        } else {
          const msgId = agentMsgRef.current;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? { ...m, toolCalls: [...m.toolCalls, toolCall] }
                : m
            )
          );
        }
        break;
      }

      case "tool_result": {
        const msgId = agentMsgRef.current;
        if (!msgId) break;
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id !== msgId) return m;
            const updated = m.toolCalls.map((tc) =>
              tc.name === event.name && tc.status === "pending"
                ? {
                    ...tc,
                    result: event.result as Record<string, unknown>,
                    status: "done" as const,
                  }
                : tc
            );
            return { ...m, toolCalls: updated };
          })
        );
        break;
      }

      case "text": {
        if (!agentMsgRef.current) {
          const id = crypto.randomUUID();
          agentMsgRef.current = id;
          setMessages((prev) => [
            ...prev,
            {
              id,
              role: "agent",
              content: event.content as string,
              toolCalls: [],
              timestamp: new Date(),
            },
          ]);
        } else {
          const msgId = agentMsgRef.current;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? { ...m, content: event.content as string }
                : m
            )
          );
        }
        break;
      }

      case "done": {
        setIsThinking(false);
        agentMsgRef.current = null;
        break;
      }

      case "error": {
        setIsThinking(false);
        agentMsgRef.current = null;
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "agent",
            content: `Error: ${event.message}`,
            toolCalls: [],
            timestamp: new Date(),
          },
        ]);
        break;
      }
    }
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => setIsConnected(true);

        ws.onclose = () => {
          setIsConnected(false);
          reconnectTimer = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          // onclose will fire after this
        };

        ws.onmessage = (e) => {
          try {
            const event = JSON.parse(e.data);
            handleEvent(event);
          } catch {
            // ignore malformed messages
          }
        };

        wsRef.current = ws;
      } catch {
        reconnectTimer = setTimeout(connect, 3000);
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [handleEvent]);

  const sendMessage = useCallback((question: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    if (!question.trim()) return;

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: question,
        toolCalls: [],
        timestamp: new Date(),
      },
    ]);

    setIsThinking(true);
    agentMsgRef.current = null;

    wsRef.current.send(JSON.stringify({ question }));
  }, []);

  return { messages, isThinking, isConnected, sendMessage };
}
