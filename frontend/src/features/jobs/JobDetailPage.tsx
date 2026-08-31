import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, FileText } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { jobsApi } from "../../api/client";

export function JobDetailPage() {
  const { jobId = "" } = useParams();
  const { data: job, isLoading } = useQuery({ queryKey: ["job", jobId], queryFn: () => jobsApi.get(jobId) });
  if (isLoading || !job) return <section className="page"><p className="empty-state">正在读取职位</p></section>;
  return (
    <section className="page">
      <Link to="/jobs" className="back-link"><ArrowLeft size={16} />返回职位</Link>
      <div className="page-heading">
        <div><p className="eyebrow">{job.company}</p><h1>{job.title}</h1><p>{job.city || "城市未填写"} · {job.source} · 版本 {job.current_version.ordinal}</p></div>
        <Link className="button-link" to={`/jobs/${job.id}/materials`}><FileText size={17} />准备求职材料</Link>
      </div>
      <div className="two-column">
        <article className="content-panel"><h2>JD 原文</h2><p className="jd-text">{job.current_version.description}</p></article>
        <aside className="content-panel"><h2>岗位要求</h2>{job.requirements.length === 0 ? <p className="muted">生成求职材料后提取岗位要求.</p> : job.requirements.map((item) => <div className="requirement-brief" key={item.id}><strong>{item.label}</strong><p>{item.evidence_text}</p></div>)}</aside>
      </div>
    </section>
  );
}
