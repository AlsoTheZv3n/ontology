import { useRef, useEffect, useState, FormEvent } from "react";
import { useChat } from "@/hooks/useChat";
import { ToolCallBadge } from "@/components/ToolCallBadge";
import { Markdown } from "@/components/Markdown";

const EXAMPLES = [
  "Wie steht der WTI Ölpreis und was sind die neuesten News dazu?",
  "Vergleich NVIDIA, AMD und Intel Aktienkurse",
  "Welche AI-Companies haben die meisten GitHub Stars?",
  "Was sind die aktuellen Top-Nachrichten zu AI Regulation?",
  "Wie steht Bitcoin und der S&P 500 heute?",
  "Vergleich Anthropic, OpenAI und Mistral in der Ontology",
];

export function Chat() {
  const { messages, isThinking, isConnected, sendMessage } = useChat();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !isConnected) return;
    sendMessage(input.trim());
    setInput("");
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)] max-w-4xl">
      {/* Header */}
      <header className="mb-8 border-l-2 border-primary pl-8">
        <div className="flex items-center gap-2 text-primary font-label text-xs font-bold uppercase tracking-[0.2em] mb-4">
          <span
            className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-400 animate-pulse" : "bg-red-400"}`}
          />
          {isConnected ? "Agent Online" : "Connecting..."}
        </div>
        <h2 className="text-5xl font-bold tracking-tighter text-on-surface mb-4 font-headline">
          Intelligence Agent
        </h2>
        <p className="text-on-surface-variant max-w-2xl text-lg font-light leading-relaxed">
          Ask questions about the ontology. Live queries against PostgreSQL — no
          hallucinations, all sources cited.
        </p>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-4 mb-6">
        {/* Empty state */}
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-8">
            <div className="text-center">
              <p className="text-on-surface font-headline font-medium mb-1">
                Ask anything about the tech ontology
              </p>
              <p className="text-sm text-secondary">
                Live data from Wikipedia, GitHub, Yahoo Finance, SEC, Hacker News
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-2xl">
              {EXAMPLES.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-left text-xs px-4 py-3 border border-outline bg-surface-container/50 hover:border-primary/50 hover:text-on-surface text-secondary transition-all font-body"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message list */}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
          >
            {/* Avatar */}
            <div
              className={`flex-shrink-0 w-8 h-8 rounded-sm flex items-center justify-center text-[10px] font-label font-bold ${
                msg.role === "user"
                  ? "bg-surface-container-high text-secondary"
                  : "bg-primary text-surface"
              }`}
            >
              {msg.role === "user" ? "U" : "S"}
            </div>

            <div
              className={`flex flex-col gap-2 max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}
            >
              {/* Tool calls */}
              {msg.toolCalls.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {msg.toolCalls.map((tc, i) => (
                    <ToolCallBadge key={i} toolCall={tc} />
                  ))}
                </div>
              )}

              {/* Content */}
              {msg.content && (
                <div
                  className={`px-5 py-4 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-primary/10 text-on-surface border border-primary/20"
                      : "bg-surface-container/80 text-on-surface border border-outline"
                  }`}
                >
                  {msg.role === "agent" ? (
                    <Markdown content={msg.content} />
                  ) : (
                    msg.content
                  )}
                </div>
              )}

              {/* Timestamp */}
              <span className="text-[9px] text-secondary/50 font-label uppercase tracking-widest">
                {msg.timestamp.toLocaleTimeString("de-CH", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          </div>
        ))}

        {/* Thinking indicator */}
        {isThinking && !messages.at(-1)?.toolCalls?.length && (
          <div className="flex gap-4">
            <div className="w-8 h-8 rounded-sm bg-primary flex items-center justify-center text-[10px] font-label font-bold text-surface flex-shrink-0">
              S
            </div>
            <div className="px-5 py-4 bg-surface-container/80 border border-outline">
              <span className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-bounce [animation-delay:300ms]" />
              </span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-outline pt-6">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isConnected ? "Frag die Ontology..." : "Connecting..."
            }
            disabled={!isConnected || isThinking}
            className="flex-1 bg-surface-container-high border-b-2 border-outline focus:border-primary px-4 py-3 text-sm text-on-surface outline-none transition-colors placeholder-secondary/50 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!isConnected || isThinking || !input.trim()}
            className="px-8 py-3 bg-primary text-surface font-bold text-[11px] uppercase tracking-[0.2em] hover:bg-primary/80 active:scale-95 transition-all font-label disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
