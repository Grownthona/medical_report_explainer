import { useRef, useCallback } from "react";
import "../styles/DropZone.css";

export default function DropZone({ files = [], onFileChange }) {
  const fileRef = useRef();

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      const droppedFiles = Array.from(e.dataTransfer.files);
      if (droppedFiles.length) onFileChange(droppedFiles);
    },
    [onFileChange]
  );

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length) onFileChange(selectedFiles);
  };

  return (
    <div
      className={`dropzone ${files.length ? "dropzone-active" : ""}`}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      onClick={() => fileRef.current.click()}
    >
      <input
        ref={fileRef}
        type="file"
        multiple
        accept=".pdf,.jpg,.jpeg,.png,.webp"
        className="dropzone-input"
        onChange={handleFileSelect}
      />

      <div className="dropzone-icon">{files.length ? "📋" : "☁️"}</div>

      <div className="dropzone-title">
        {files.length
          ? `${files.length} file(s) selected`
          : "Drag & drop your medical reports"}
      </div>

      {files.length > 0 && (
        <ul className="dropzone-filelist">
          {files.map((f, i) => (
            <li key={i}>{f.name}</li>
          ))}
        </ul>
      )}

      <div className="dropzone-subtitle">
        PDF, JPG, PNG — up to 10 MB each
      </div>

      {!files.length && <div className="dropzone-browse">Or browse files</div>}
    </div>
  );
}