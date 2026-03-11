import "../styles/SectionTabs.css";
import { TAB_ICONS } from "../utils/constants";

export default function SectionTabs({ keys, activeTab, onTabChange }) {
  if (keys.length <= 1) return null;

  return (
    <div className="section-tabs">
      {keys.map((key) => (
        <button
          key={key}
          onClick={() => onTabChange(key)}
          className={`section-tab ${
            activeTab === key ? "section-tab-active" : ""
          }`}
        >
          {TAB_ICONS[key] || "📄"} {key}
        </button>
      ))}
    </div>
  );
}