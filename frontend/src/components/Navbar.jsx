import { useNavigate, useLocation } from "react-router-dom";
import "../styles/Navbar.css";

export default function Navbar({ onBack }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogoClick = () => {
    if (location.pathname === "/results") {
      navigate("/");
    } else if (location.pathname === "/" || location.pathname === "/upload") {
      if (location.state?.reportData) {
        navigate("/results", { state: location.state });
      } else {
        navigate("/");
      }
    }
  };
  return (
    <nav className={`navbar ${onBack ? "navbar-sticky" : ""}`}>
      
      {/* Left side */}
      <div className={`navbar-left ${onBack ? "navbar-left-back" : ""}`}>
        
        {onBack && (
          <button className="navbar-back-btn" onClick={onBack}>
            ← Back
          </button>
        )}

        <div className="navbar-brand" onClick={handleLogoClick} style={{ cursor: "pointer" }}>
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