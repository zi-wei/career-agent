import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { useEffect, useState } from "react";

import type { ApplicationStatus } from "../../api/client";
import { applicationsApi } from "../../api/client";
import { useBackgroundTask, useElapsedSeconds } from "../../app/BackgroundTasks";

type ApplicationAdvice = { summary: string; source_facts: string[]; next_actions: string[] };

const statuses: ApplicationStatus[] = ["lead", "planned", "applied", "contacted", "interview", "offer", "rejected", "silent", "withdrawn"];

export function ApplicationsPage() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["applications"], queryFn: applicationsApi.list });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const current = data?.items.find((item) => item.id === selectedId) ?? data?.items[0];
  const [status, setStatus] = useState<ApplicationStatus>("lead");
  const [reason, setReason] = useState("");
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const adviceTask = useBackgroundTask<ApplicationAdvice>(`application-advice:${current?.id ?? "none"}`);
  const adviceSeconds = useElapsedSeconds(adviceTask.startedAt, adviceTask.isPending);
  useEffect(() => { if (current) setStatus(current.status); }, [current]);
  const update = useMutation({
    mutationFn: () => applicationsApi.updateStatus(current!.id, status, ""),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });
  const generateAdvice = () => {
    if (!current) return Promise.resolve(undefined);
    const selectedApplication = current;
    return adviceTask.run(async () => {
      await applicationsApi.addFeedback(selectedApplication.id, {
        stage: selectedApplication.status, outcome: selectedApplication.status, question: "",
        recorded_reason: reason, notes: feedbackNotes,
      });
      return applicationsApi.advice(selectedApplication.id);
    }, {
      label: "生成投递反馈建议",
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
    }).catch(() => undefined);
  };
  return <section className="page"><div className="page-heading"><div><p className="eyebrow">反馈迭代</p><h1>投递看板</h1><p>记录每次投递使用的职位版本、简历版本和后续反馈.</p></div></div>
    <div className="application-board">{statuses.map((column) => <section key={column}><header><strong>{column}</strong><span>{data?.items.filter((item) => item.status === column).length ?? 0}</span></header>{data?.items.filter((item) => item.status === column).map((item) => <button className={current?.id === item.id ? "application-card selected" : "application-card"} key={item.id} onClick={() => setSelectedId(item.id)}><span>{item.channel}</span><strong>职位 {item.job_id.slice(0, 8)}</strong><small>简历 v{item.resume_id.slice(0, 6)}</small></button>)}</section>)}</div>
    {current && <div className="application-controls"><div className="inline-editor"><label>更新投递状态<select value={status} onChange={(event) => setStatus(event.target.value as ApplicationStatus)}>{statuses.map((item) => <option key={item} value={item}>{item}</option>)}</select></label><button disabled={status === current.status} onClick={() => update.mutate()}><Save size={16} />保存状态</button></div>
      <div className="feedback-editor"><label>记录的反馈原因<input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="只填写对方明确说明或你实际观察到的事实" /></label><label>补充记录<textarea rows={3} value={feedbackNotes} onChange={(event) => setFeedbackNotes(event.target.value)} /></label>{adviceTask.isPending && <p className="inline-task-progress" role="status">正在生成反馈建议, 已等待 {adviceSeconds} 秒. 离开页面不会中断.</p>}{adviceTask.status === "error" && <p className="form-error" role="alert">反馈已保留, 建议生成失败, 请重新生成.</p>}<button disabled={(!reason.trim() && !feedbackNotes.trim()) || adviceTask.isPending} onClick={() => void generateAdvice()}>{adviceTask.isPending ? "正在生成建议" : adviceTask.status === "error" ? "重新生成建议" : "记录反馈并生成建议"}</button></div>
      {adviceTask.data && <div className="advice-panel"><h2>下一轮建议</h2><p>{adviceTask.data.summary}</p><strong>事实引用</strong>{adviceTask.data.source_facts.map((fact) => <p key={fact}>{fact}</p>)}<strong>行动</strong>{adviceTask.data.next_actions.map((action) => <p key={action}>{action}</p>)}</div>}
    </div>}
    {!current && <div className="empty-state">从已生成的求职材料创建首条投递记录.</div>}
  </section>;
}
