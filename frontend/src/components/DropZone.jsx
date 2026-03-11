import { useRef, useCallback } from "react";
import "../styles/DropZone.css";

export default function DropZone({ file, onFileChange }) {
  const fileRef = useRef();

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      const f = e.dataTransfer.files[0];
      if (f) onFileChange(f);
    },
    [onFileChange]
  );

  return (
    <div
      className={`dropzone ${file ? "dropzone-active" : ""}`}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      onClick={() => fileRef.current.click()}
    >
      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png,.webp"
        className="dropzone-input"
        onChange={(e) => onFileChange(e.target.files[0])}
      />

      <div className="dropzone-icon">{file ? "📋" : "☁️"}</div>

      <div className="dropzone-title">
        {file ? file.name : "Drag & drop your medical report"}
      </div>

      <div className="dropzone-subtitle">
        PDF, JPG, PNG, WebP — up to 10 MB
      </div>

      {!file && <div className="dropzone-browse">Or browse files</div>}
    </div>
  );
}