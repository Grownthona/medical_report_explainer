import "../styles/ChatBot.css";
import { useState, useRef, useEffect } from "react";

export default function ChatBot({ patientData }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi! I'm MediBot 🩺 Ask me anything about your report and I'll explain it in plain language.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
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
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const reportContext = JSON.stringify(patientData, null, 2);

      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: `You are a friendly medical report explainer. You have access to the following patient report data:\n${reportContext}\n\nExplain medical terms in plain language. Be empathetic, clear, and always recommend consulting a doctor for medical decisions. Keep responses concise (2-4 sentences).`,
          messages: [
            ...messages
              .filter((m, i) => !(m.role === "assistant" && i === 0))
              .map((m) => ({
                role: m.role,
                content: m.text,
              })),
            { role: "user", content: userMsg },
          ],
        }),
      });

      const data = await response.json();

      const reply =
        data.content?.[0]?.text ||
        "Sorry, I couldn't process that. Please try again.";

      setMessages((prev) => [...prev, { role: "assistant", text: reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Connection error. Please try again." },
      ]);
    }

    setLoading(false);
  };

  const unread = !open && messages.length > 1;

  return (
    <>
      {/* SIDE PANEL */}
      <div
        className={`chatbot-panel ${
          open ? "chatbot-open" : "chatbot-closed"
        }`}
      >
        {/* HEADER */}
        <div className="chatbot-header">
          <div className="chatbot-header-row">
            <div className="chatbot-title-group">
              <div className="chatbot-avatar">🩺</div>

              <div>
                <div className="chatbot-title">MediBot</div>

                <div className="chatbot-status">
                  <div className="status-dot"></div>
                  {/* Online · Powered by  */}
                </div>
              </div>
            </div>

            <button
              className="close-btn"
              onClick={() => setOpen(false)}
            >
              ✕
            </button>
          </div>
        </div>

        {/* MESSAGES */}
        <div className="chatbot-messages">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`message-row ${
                m.role === "user" ? "message-user" : "message-bot"
              }`}
            >
              {m.role === "assistant" && (
                <div className="bot-avatar">🩺</div>
              )}

              <div
                className={`message ${
                  m.role === "user"
                    ? "message-user-bubble"
                    : "message-bot-bubble"
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

        {/* INPUT */}
        <div className="chatbot-input-area">
          <div className="chatbot-input-row">
            <input
              className="chatbot-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" && !e.shiftKey && sendMessage()
              }
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

          <p className="disclaimer">
            Always consult a doctor for medical decisions.
          </p>
        </div>
      </div>

      {/* FLOAT BUTTON */}
      <button
        className={`chatbot-fab ${open ? "fab-open" : "fab-closed"}`}
        onClick={() => setOpen((v) => !v)}
      >
        <span>{open ? "✕" : "💬"}</span>
        <span>{open ? "Close" : "Ask MediBot"}</span>

        {unread && !open && (
          <div
            style={{
              position: "absolute",
              top: -4,
              right: -4,
              width: 12,
              height: 12,
              borderRadius: "50%",
              background: "#f43f5e",
              border: "2px solid #070d1a",
              boxShadow: "0 0 6px #f43f5e",
            }}
          />
        )}
      </button>
    </>
  );
}