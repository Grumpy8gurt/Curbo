import { useState } from "react";

interface UploadPanelProps {
  onUpload: (file: File) => Promise<void>;
}

export function UploadPanel({ onUpload }: UploadPanelProps) {
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      return;
    }

    setSubmitting(true);
    try {
      await onUpload(file);
      setFile(null);
      event.currentTarget.reset();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="field-stack" onSubmit={handleSubmit}>
      <label className="upload-dropzone">
        <span>Upload street-level image</span>
        <input
          type="file"
          accept="image/*"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </label>
      <p className="helper-text">
        {file ? `Selected file: ${file.name}` : "No image selected yet."}
      </p>
      <button className="secondary-button" type="submit" disabled={!file || submitting}>
        {submitting ? "Running mock detection..." : "Upload and detect"}
      </button>
    </form>
  );
}
