import { useState } from "react";
import axios from "axios";

function UploadMedicalFile() {
  const [files, setFiles] = useState([]);

  const handleUpload = async () => {
    const formData = new FormData();
    files.forEach(file => formData.append("medicalFiles", file));

    try {
      const res = await axios.post(
        "http://localhost:5000/api/upload/multiple",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      console.log(res.data);
      alert("Files uploaded successfully");
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    }
  };

  return (
    <div>
      <input
        type="file"
        multiple
        accept=".pdf,.jpg,.jpeg,.png"
        onChange={(e) => setFiles(Array.from(e.target.files))}
      />
      <button onClick={handleUpload}>Upload</button>
    </div>
  );
}

export default UploadMedicalFile;
