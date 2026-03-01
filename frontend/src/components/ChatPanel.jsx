import { useState, useRef, useEffect } from "react";
import { getChatReply } from "../utils/chatResponses";
import { QUICK_PROMPTS } from "../utils/constants";
import "../styles/ChatPanel.css";

export default function ChatPanel({ patient, onClose }) {
  const [msgs, setMsgs] = useState([
    {
      role: "ai",
      text: `Hi! I'm here to help you understand ${patient.name}'s report. Ask me anything about the test results, what they mean, or what to do next.`,
    },
  ]);
  const [input, setInput]   = useState("");
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef();

  const send = async (msg) => {
    if (!msg.trim()) return;
    const userMsg = msg.trim();
    setMsgs((m) => [...m, { role: "user", text: userMsg }]);
    setInput("");
    setTyping(true);
    await new Promise((r) => setTimeout(r, 900 + Math.random() * 600));
    setTyping(false);
    setMsgs((m) => [...m, { role: "ai", text: getChatReply(userMsg) }]);
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, typing]);

  return (
    <div className="chat-panel">

      {/* Header */}
      <div className="chat-header">
        <div className="chat-header__left">
          <div className="chat-header__avatar">⚕</div>
          <div>
            <div className="chat-header__title">Report Assistant</div>
            <div className="chat-header__sub">Ask anything about this report</div>
          </div>
        </div>
        <button className="chat-header__close" onClick={onClose}>×</button>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {msgs.map((m, i) => (
          <div key={i} className={`chat-msg-row${m.role === "user" ? " chat-msg-row--user" : ""}`}>
            {m.role === "ai" && <div className="chat-ai-icon">⚕</div>}
            <div className={`chat-bubble chat-bubble--${m.role}`}>{m.text}</div>
          </div>
        ))}

        {typing && (
          <div className="chat-msg-row">
            <div className="chat-ai-icon">⚕</div>
            <div className="chat-bubble chat-bubble--ai chat-bubble--typing">
              <span className="chat-typing-dot chat-typing-dot--1" />
              <span className="chat-typing-dot chat-typing-dot--2" />
              <span className="chat-typing-dot chat-typing-dot--3" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick prompts */}
      <div className="chat-quick-row">
        {QUICK_PROMPTS.map((q) => (
          <button key={q} className="chat-quick-btn" onClick={() => send(q)}>
            {q}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="chat-input-row">
        <input
          className="chat-input"
          value={input}
          placeholder="Ask about any test result…"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
        />
        <button
          className={`chat-send-btn${!input.trim() ? " chat-send-btn--disabled" : ""}`}
          onClick={() => send(input)}
        >
          ↑
        </button>
      </div>

    </div>
  );
}
