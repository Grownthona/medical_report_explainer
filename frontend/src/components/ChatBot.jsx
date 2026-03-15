// ChatBot.jsx
import "../styles/ChatBot.css";
import { useState, useRef, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export default function ChatBot({ patientData, language = "en" }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! I'm MediBot 🩺 Ask me anything about your report and I'll explain it in plain language.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (open) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 80);
    }
  }, [open, messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput("");
    setError(null);

    const updatedMessages = [...messages, { role: "user", text: userMsg }];
    setMessages(updatedMessages);
    setLoading(true);

    const history = updatedMessages
      .slice(1)
      .map((m) => ({ role: m.role, content: m.text }));

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages:     history,
          patient_data: patientData ?? null,
          language:     language,       // 👈 was hardcoded "en", now uses prop
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail ?? `Server error ${response.status}`);
      }

      const data = await response.json();
      const reply = data.reply ?? "Sorry, I couldn't process that. Please try again.";

      setMessages((prev) => [...prev, { role: "assistant", text: reply }]);
    } catch (err) {
      const msg = err.message ?? "Connection error. Please try again.";
      setError(msg);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `⚠️ ${msg}` },
      ]);
    }

    setLoading(false);
  };

  // 👇 Reset chat when report data changes (new report uploaded)
  useEffect(() => {
    setMessages([
      {
        role: "assistant",
        text: "Hi! I'm MediBot 🩺 Ask me anything about your report and I'll explain it in plain language.",
      },
    ]);
  }, [patientData]);

  const unread = !open && messages.length > 1;

  return (
    <>
      <div className={`chatbot-panel ${open ? "chatbot-open" : "chatbot-closed"}`}>
        <div className="chatbot-header">
          <div className="chatbot-header-row">
            <div className="chatbot-title-group">
              <div className="chatbot-avatar">🩺</div>
              <div>
                <div className="chatbot-title">MediBot</div>
                <div className="chatbot-status">
                  <div className="status-dot"></div>
                </div>
              </div>
            </div>
            <button className="close-btn" onClick={() => setOpen(false)}>✕</button>
          </div>
        </div>

        <div className="chatbot-messages">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`message-row ${m.role === "user" ? "message-user" : "message-bot"}`}
            >
              {m.role === "assistant" && <div className="bot-avatar">🩺</div>}
              <div
                className={`message ${
                  m.role === "user" ? "message-user-bubble" : "message-bot-bubble"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row message-bot">
              <div className="bot-avatar">🩺</div>
              <div className="message message-bot-bubble">
                <div style={{ display: "flex", gap: 5 }}>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chatbot-input-area">
          <div className="chatbot-input-row">
            <input
              className="chatbot-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder="Ask about your results..."
            />
            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
            >
              ↑
            </button>
          </div>
          <p className="disclaimer">Always consult a doctor for medical decisions.</p>
        </div>
      </div>

      <button
        className={`chatbot-fab ${open ? "fab-open" : "fab-closed"}`}
        onClick={() => setOpen((v) => !v)}
      >
        <span>{open ? "✕" : "💬"}</span>
        <span>{open ? "Close" : "Ask MediBot"}</span>

        {unread && !open && (
          <div
            style={{
              position: "absolute", top: -4, right: -4,
              width: 12, height: 12, borderRadius: "50%",
              background: "#f43f5e", border: "2px solid #070d1a",
              boxShadow: "0 0 6px #f43f5e",
            }}
          />
        )}
        {error && (
          <div className="error-toast">
            <span>⚠ {error}</span>
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}
      </button>
    </>
  );
}