import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, CalendarDays, CheckCircle2, FileSearch, RefreshCw } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { planningApi, practiceApi } from "../../api/client";
import type { RollingPlan } from "../../api/client";
import { useBackgroundTask, useElapsedSeconds } from "../../app/BackgroundTasks";

export function PlanPage() {
  const { jobId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["plan", jobId], queryFn: () => planningApi.latestPlan(jobId) });
  const create = useBackgroundTask<RollingPlan>(`plan:${jobId}`);
  const elapsedSeconds = useElapsedSeconds(create.startedAt, create.isPending);
  const createPlan = () => create.run(
    () => planningApi.createPlan(jobId),
    {
      label: "生成14天计划",
      onSuccess: (plan) => { queryClient.setQueryData(["plan", jobId], plan); },
    },
  ).catch(() => undefined);
  const materialize = useMutation({ mutationFn: (planId: string) => practiceApi.fromPlan(planId), onSuccess: () => navigate("/practice") });
  const plan = query.data ?? create.data;
  if (query.isLoading && !create.isPending && !plan) return <section className="page"><p className="empty-state">正在读取计划</p></section>;
  if (!plan) return <section className="page centered-action"><CalendarDays size={30} /><h1>尚未生成计划</h1><p>请先在加强选择中至少选择一项希望加强的内容.</p>{create.isPending && <div className="generation-status" aria-live="polite"><div className="activity-progress" role="progressbar" aria-label="计划生成进度"><span /></div><p>正在生成14天计划, 已等待 {elapsedSeconds} 秒. 可以离开此页面, 任务会继续运行.</p></div>}{create.status === "error" && <p className="form-error" role="alert">计划生成失败, 请稍后重新生成.</p>}<button disabled={create.isPending} onClick={() => void createPlan()}>{create.isPending ? "正在生成" : create.status === "error" ? "重新生成" : "生成14天计划"}</button></section>;
  return <section className="page"><div className="page-heading"><div><p className="eyebrow">版本 {plan.revision}</p><h1>14天滚动计划</h1><p>{plan.starts_on} 开始 · {plan.timezone}</p>{create.isPending && <p className="inline-task-progress" role="status">正在后台生成新版本, 已等待 {elapsedSeconds} 秒. 离开页面不会中断.</p>}{create.status === "error" && <p className="form-error" role="alert">计划生成失败, 当前版本未受影响.</p>}</div><div className="heading-actions"><button className="secondary" disabled={create.isPending} onClick={() => void createPlan()}><RefreshCw size={16} />{create.isPending ? "正在生成" : "重新生成计划"}</button><button onClick={() => materialize.mutate(plan.id)}>进入学习与实训</button></div></div><div className="plan-list">{plan.days.map((day) => <section className="plan-day" key={day.day_number}><div className="day-index"><span>DAY</span><strong>{String(day.day_number).padStart(2, "0")}</strong><time>{day.date.slice(5)}</time></div><div className="day-tasks">{day.tasks.map((task) => <article key={task.id}>{task.kind === "learning" ? <BookOpen size={18} /> : <FileSearch size={18} />}<div><h2>{task.title}</h2><p>{task.objective}</p><span><CheckCircle2 size={14} />{task.completion_condition}</span></div></article>)}</div></section>)}</div></section>;
}
