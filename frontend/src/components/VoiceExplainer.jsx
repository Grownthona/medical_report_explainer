import { useState, useRef, useEffect } from "react";
import "../styles/VoiceExplainer.css";

export default function VoiceExplainer({ text, language = "en" }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress]   = useState(0);
  const [loading, setLoading]     = useState(false);
  const audioRef  = useRef(null);
  const scrollRef = useRef(null);

  // Clean up on unmount
  useEffect(() => () => audioRef.current?.pause(), []);

  const fetchAndPlay = async () => {
    setLoading(true);
    try {
      const form = new FormData();
      form.append("text", text);
      form.append("language", language);

      const res  = await fetch("http://localhost:8000/tts", { method: "POST", body: form });
      const data = await res.json();

      console.log("TTS response:", data);          // check shape
      console.log("audio_base64 preview:", data.audio_base64?.slice(0, 50));

      // Decode base64 → Blob → Object URL
      const base64Clean = data.audio_base64.replace(/\s/g, "");
      const binary = atob(base64Clean);

      const bytes  = new Uint8Array(binary.length).map((_, i) => binary.charCodeAt(i));
      const blob   = new Blob([bytes], { type: "audio/mp3" });
      const url    = URL.createObjectURL(blob);

      const audio  = new Audio(url);
      audioRef.current = audio;

      audio.ontimeupdate = () =>
        setProgress((audio.currentTime / audio.duration) * 100 || 0);

      audio.onended = () => { setIsPlaying(false); setProgress(0); };

      await audio.play();
      setIsPlaying(true);
    } catch (err) {
      console.error("TTS error:", err);
    } finally {
      setLoading(false);
    }
  };

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) { fetchAndPlay(); return; }
    if (isPlaying) { audio.pause(); setIsPlaying(false); }
    else           { audio.play();  setIsPlaying(true);  }
  };

  return (
    <div className="voice-explainer">
      <div className="voice-header">
        <div className="audio-visualizer">
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className={`bar ${isPlaying ? "animating" : ""}`}
              style={{
                height: isPlaying ? `${Math.random() * 20 + 10}px` : "10px",
                transitionDelay: `${i * 0.1}s`,
              }}
            />
          ))}
        </div>

        <button className="play-btn" onClick={togglePlay} disabled={loading || !text}>
          {loading ? "⏳" : isPlaying ? "⏸" : "▶"}
        </button>

        <div className="voice-title-container">
          <span className="voice-title">Voice Explainer</span>
          <div className="progress-track">
            <div className="progress-bar" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>

      <div className="transcript-container" ref={scrollRef}>
        <div className="transcript-label">Transcript</div>
        <p className="transcript-text">
          {text || "Hello. Your blood test results are mostly normal..."}
        </p>
      </div>
    </div>
  );
}