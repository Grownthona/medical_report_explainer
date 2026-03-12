import { useState, useRef, useEffect } from "react";
import "../styles/VoiceExplainer.css";

export default function VoiceExplainer({ text }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const scrollRef = useRef(null);

  // Simulate audio progress for visual effect since we don't have real audio files
  useEffect(() => {
    let interval;
    if (isPlaying) {
      interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 100);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
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
            ></div>
          ))}
        </div>
        <button className="play-btn" onClick={togglePlay}>
          {isPlaying ? "⏸" : "▶"}
        </button>
        <div className="voice-title-container">
          <span className="voice-title">Voice Explainer</span>
          <div className="progress-track">
            <div className="progress-bar" style={{ width: `${progress}%` }}></div>
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
