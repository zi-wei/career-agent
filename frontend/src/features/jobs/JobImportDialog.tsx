import { useState } from "react";
import { X } from "lucide-react";

import type { JobDetail } from "../../api/client";
import { jobsApi } from "../../api/client";

type Props = { onClose: () => void; onImported: (job: JobDetail) => void };

export function JobImportDialog({ onClose, onImported }: Props) {
  const [mode, setMode] = useState<"paste" | "json">("paste");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [city, setCity] = useState("");
  const [description, setDescription] = useState("");
  const [jsonText, setJsonText] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const job =
        mode === "paste"
          ? await jobsApi.paste({ title, company, city, description })
          : await jobsApi.importJson(JSON.parse(jsonText));
      onImported(job);
    } catch (reason) {
      setError(reason instanceof SyntaxError ? "JSON 格式不正确" : "职位导入失败, 请检查字段");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal" role="dialog" aria-modal="true" aria-label="导入职位">
        <div className="modal-header">
          <h2>导入职位</h2>
          <button className="icon-button" onClick={onClose} aria-label="关闭">
            <X size={18} />
          </button>
        </div>
        <div className="segmented">
          <button className={mode === "paste" ? "selected" : ""} onClick={() => setMode("paste")}>
            粘贴 JD
          </button>
          <button className={mode === "json" ? "selected" : ""} onClick={() => setMode("json")}>
            导入 JSON
          </button>
        </div>
        <form onSubmit={submit}>
          {mode === "paste" ? (
            <>
              <label>职位名称<input value={title} onChange={(e) => setTitle(e.target.value)} required /></label>
              <label>公司<input value={company} onChange={(e) => setCompany(e.target.value)} required /></label>
              <label>城市<input value={city} onChange={(e) => setCity(e.target.value)} /></label>
              <label>JD 原文<textarea value={description} onChange={(e) => setDescription(e.target.value)} required rows={10} /></label>
            </>
          ) : (
            <label>JobPosting v1 JSON<textarea value={jsonText} onChange={(e) => setJsonText(e.target.value)} required rows={16} /></label>
          )}
          {error && <p className="form-error">{error}</p>}
          <div className="form-actions">
            <button type="button" className="secondary" onClick={onClose}>取消</button>
            <button type="submit" disabled={submitting}>{submitting ? "导入中" : "确认导入"}</button>
          </div>
        </form>
      </section>
    </div>
  );
}
