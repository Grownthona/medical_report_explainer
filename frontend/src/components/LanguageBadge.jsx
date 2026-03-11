import "../styles/LanguageBadge.css";

export default function LanguageBadge({ language }) {
  return (
    <div className="language-badge">
      <span className="language-text">
        🌐 Showing in
      </span>

      <span className="language-pill">
        {language}
      </span>
    </div>
  );
}