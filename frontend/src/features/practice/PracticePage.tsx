import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Play, Send, Trash2 } from "lucide-react";
import { useState } from "react";

import type { KnowledgeGuidance, PracticeEvaluation, PracticeTask, ProjectGuidance } from "../../api/client";
import { practiceApi } from "../../api/client";
import { useBackgroundTask, useElapsedSeconds } from "../../app/BackgroundTasks";

function GuidanceContent({ task }: { task: PracticeTask }) {
  const guidance = task.guidance;
  if ("explanation" in guidance) {
    const knowledge = guidance as KnowledgeGuidance;
    return <section className="guidance-content" aria-label="知识讲解">
      <div className="guidance-intro"><h3>知识讲解</h3><p>{knowledge.explanation}</p></div>
      <div><h3>关键概念</h3><dl>{knowledge.key_concepts.map((concept) => <div key={concept.name}><dt>{concept.name}</dt><dd>{concept.explanation}</dd></div>)}</dl></div>
      <div className="scenario-block"><h3>场景题</h3><p>{knowledge.scenario_question}</p><h4>回答框架</h4><ol>{knowledge.answer_framework.map((item) => <li key={item}>{item}</li>)}</ol></div>
      <div><h3>自检</h3><ul>{knowledge.self_checks.map((item) => <li key={item}>{item}</li>)}</ul></div>
    </section>;
  }
  if ("business_context" in guidance) {
    const project = guidance as ProjectGuidance;
    return <section className="guidance-content" aria-label="项目指导">
      <div className="guidance-intro"><h3>业务背景</h3><p>{project.business_context}</p></div>
      <div><h3>项目阶段</h3><ol className="milestone-list">{project.milestones.map((milestone) => <li key={milestone.title}><strong>{milestone.title}</strong><ul>{milestone.actions.map((action) => <li key={action}>{action}</li>)}</ul><span>产出: {milestone.expected_output}</span></li>)}</ol></div>
      <div className="guidance-columns"><div><h3>验收标准</h3><ul>{project.acceptance_criteria.map((item) => <li key={item}>{item}</li>)}</ul></div><div><h3>交付物</h3><ul>{project.deliverables.map((item) => <li key={item}>{item}</li>)}</ul></div></div>
      <div><h3>复盘问题</h3><ul>{project.reflection_questions.map((item) => <li key={item}>{item}</li>)}</ul></div>
    </section>;
  }
  if ("instructions" in guidance) {
    return <section className="guidance-content"><h3>任务说明</h3><p>{guidance.instructions}</p><ul>{guidance.checklist.map((item) => <li key={item}>{item}</li>)}</ul></section>;
  }
  return null;
}

export function PracticePage() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["practice"], queryFn: practiceApi.list });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [summary, setSummary] = useState("");
  const selected = data?.items.find((item) => item.id === selectedId) ?? data?.items[0];
  const evaluation = useBackgroundTask<PracticeEvaluation>(`practice-evaluation:${selected?.id ?? "none"}`);
  const evaluationSeconds = useElapsedSeconds(evaluation.startedAt, evaluation.isPending);
  const start = useMutation({
    mutationFn: (id: string) => practiceApi.start(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["practice"] }),
  });
  const remove = useMutation({
    mutationFn: (id: string) => practiceApi.remove(id),
    onSuccess: (_, deletedId) => {
      queryClient.setQueryData<{ items: PracticeTask[] }>(["practice"], (current) => ({
        items: current?.items.filter((item) => item.id !== deletedId) ?? [],
      }));
      setSelectedId(null);
      queryClient.invalidateQueries({ queryKey: ["evidence"] });
    },
  });
  const submitAndEvaluate = () => {
    if (!selected) return Promise.resolve(undefined);
    const selectedTask = selected;
    return evaluation.run(async () => {
      const submission = await practiceApi.submit(selectedTask.id, {
        content, artifact_refs: [], report_summary: summary,
      });
      return practiceApi.evaluate(submission.id);
    }, {
      label: "评价实训并生成证据",
      onSuccess: async () => {
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ["practice"] }),
          queryClient.invalidateQueries({ queryKey: ["evidence"] }),
        ]);
      },
    }).catch(() => undefined);
  };
  return <section className="page">
    <div className="page-heading"><div><p className="eyebrow">学习闭环</p><h1>学习与实训</h1><p>完成知识训练和岗位项目, 将过程沉淀为可追溯证据.</p></div></div>
    {!data?.items.length ? <div className="empty-state"><p>尚无实训任务. 请先生成14天计划.</p></div> :
      <div className="workbench-grid">
        <div className="task-rail" aria-label="实训任务列表">{data.items.map((task) =>
          <button className={selected?.id === task.id ? "task-row selected" : "task-row"} key={task.id} onClick={() => setSelectedId(task.id)}>
            <span className={`state-badge ${task.status}`}>{task.status}</span><strong>{task.title}</strong><small>{task.kind}</small>
          </button>)}</div>
        {selected && <div className="practice-detail"><div className="section-heading"><div><h2>{selected.title}</h2><p>{selected.objective}</p></div><div className="section-actions">{selected.status === "pending" && <button onClick={() => start.mutate(selected.id)}><Play size={16} />开始任务</button>}<button className="icon-button danger" aria-label="删除实训任务" title="删除实训任务" disabled={remove.isPending} onClick={() => { if (window.confirm("删除该实训任务及其提交、评价和自动生成的证据?")) remove.mutate(selected.id); }}><Trash2 size={16} /></button></div></div>
          <GuidanceContent task={selected} />
          <div className="criteria-grid"><div><h3>验收标准</h3>{selected.acceptance_criteria.map((item) => <p key={item}><CheckCircle2 size={14} />{item}</p>)}</div><div><h3>交付物</h3>{selected.deliverables.map((item) => <p key={item}>{item}</p>)}</div></div>
          <label>提交内容<textarea rows={7} value={content} onChange={(event) => setContent(event.target.value)} placeholder="记录过程、关键命令说明、结果和复盘" /></label>
          <label>测试或结果摘要<textarea rows={3} value={summary} onChange={(event) => setSummary(event.target.value)} /></label>
          {evaluation.isPending && <p className="inline-task-progress" role="status">正在评价并生成证据, 已等待 {evaluationSeconds} 秒. 离开页面不会中断.</p>}
          {evaluation.status === "error" && <p className="form-error" role="alert">评价生成失败, 请重新提交.</p>}
          <div className="footer-action"><button disabled={!content.trim() || selected.status === "pending" || evaluation.isPending} onClick={() => void submitAndEvaluate()}><Send size={16} />{evaluation.isPending ? "正在评价" : evaluation.status === "error" ? "重新提交并评价" : "提交并评价"}</button></div>
          {evaluation.status === "success" && <p className="success-message">已生成证据</p>}
        </div>}
      </div>}
  </section>;
}
