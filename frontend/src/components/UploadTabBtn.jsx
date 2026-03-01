import { useRef, useState } from "react";
import { ACCEPTED } from "../utils/constants";
import "../styles/AppShell.css";

export default function UploadTabBtn({ onFiles }) {
  const ref = useRef();
  const [drag, setDrag] = useState(false);

  const go = (files) => {
    const arr = Array.from(files);
    if (!arr.length || arr.find((f) => !ACCEPTED.includes(f.type))) return;
    onFiles(arr);
  };

  return (
    <div
      className={`app-add-tab${drag ? " app-add-tab--drag" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => { e.preventDefault(); setDrag(false); go(e.dataTransfer.files); }}
      onClick={() => ref.current.click()}
    >
      <input
        ref={ref}
        type="file"
        multiple
        accept=".jpg,.jpeg,.png,.webp,.pdf"
        style={{ display: "none" }}
        onChange={(e) => go(e.target.files)}
      />
      <span className="app-add-tab__icon">＋</span>
      <span className="app-add-tab__label">New Patient</span>
    </div>
  );
}
