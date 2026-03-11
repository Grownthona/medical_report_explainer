import "../styles/Navbar.css";

export default function Navbar({ onBack }) {
  return (
    <nav className={`navbar ${onBack ? "navbar-sticky" : ""}`}>
      
      {/* Left side */}
      <div className={`navbar-left ${onBack ? "navbar-left-back" : ""}`}>
        
        {onBack && (
          <button className="navbar-back-btn" onClick={onBack}>
            ← Back
          </button>
        )}

        <div className="navbar-brand">
          <span className={`navbar-icon ${onBack ? "navbar-icon-small" : ""}`}>
            🩺
          </span>

          <span className={`navbar-title ${onBack ? "navbar-title-small" : ""}`}>
            MediTranslate <span className="navbar-ai">AI</span>
          </span>
        </div>

      </div>

      {/* Right side */}
      {/* <div className="navbar-powered">
        
      </div> */}

    </nav>
  );
}