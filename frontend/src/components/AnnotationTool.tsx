import { useState } from "react";
import type { AnnotationDraft, AnnotationKind } from "../types/annotations";

interface AnnotationToolProps {
  onCreate: (annotation: AnnotationDraft) => Promise<void>;
}

const DEFAULT_FORM: AnnotationDraft = {
  annotationType: "missing curb cut",
  description: "",
  latitude: 44.0521,
  longitude: -123.0868
};

export function AnnotationTool({ onCreate }: AnnotationToolProps) {
  const [form, setForm] = useState<AnnotationDraft>(DEFAULT_FORM);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);

    try {
      await onCreate(form);
      setForm({
        ...DEFAULT_FORM,
        description: ""
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="field-stack" onSubmit={handleSubmit}>
      <label className="field-label">
        Type
        <select
          className="select-input"
          value={form.annotationType}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              annotationType: event.target.value as AnnotationKind
            }))
          }
        >
          <option value="missing curb cut">Missing curb cut</option>
          <option value="bad data">Bad data</option>
          <option value="obstruction">Obstruction</option>
          <option value="other">Other</option>
        </select>
      </label>

      <label className="field-label">
        Description
        <textarea
          className="text-input textarea-input"
          value={form.description}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              description: event.target.value
            }))
          }
          placeholder="Describe the curb issue or field note."
          required
        />
      </label>

      <div className="form-row">
        <label className="field-label">
          Latitude
          <input
            className="text-input"
            type="number"
            step="0.0001"
            value={form.latitude}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                latitude: Number(event.target.value)
              }))
            }
            required
          />
        </label>
        <label className="field-label">
          Longitude
          <input
            className="text-input"
            type="number"
            step="0.0001"
            value={form.longitude}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                longitude: Number(event.target.value)
              }))
            }
            required
          />
        </label>
      </div>

      <button className="primary-button" type="submit" disabled={submitting}>
        {submitting ? "Saving..." : "Add annotation"}
      </button>
    </form>
  );
}
