import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Check } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import type { RollingPlan, SelectionState } from "../../api/client";
import { jobsApi, planningApi } from "../../api/client";
import { useBackgroundTask } from "../../app/BackgroundTasks";

const options: Array<{ value: Exclude<SelectionState, "unselected">; label: string }> = [
  { value: "strengthen", label: "希望加强" },
  { value: "already_have", label: "已有能力" },
  { value: "skip", label: "暂不加强" },
];

export function SelectionPage() {
  const { jobId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: job } = useQuery({ queryKey: ["job", jobId], queryFn: () => jobsApi.get(jobId) });
  const planTask = useBackgroundTask<RollingPlan>(`plan:${jobId}`);
  const [states, setStates] = useState<Record<string, SelectionState>>({});
  useEffect(() => { if (job) setStates(Object.fromEntries(job.requirements.map((item) => [item.id, item.selection]))); }, [job]);
  const save = useMutation({
    mutationFn: async () => {
      const selections = Object.entries(states).filter(([, state]) => state !== "unselected").map(([requirement_id, state]) => ({ requirement_id, state }));
      return planningApi.updateSelections(jobId, selections);
    },
    onSuccess: () => {
      void planTask.run(
        () => planningApi.createPlan(jobId),
        {
          label: "生成14天计划",
          onSuccess: (plan) => { queryClient.setQueryData(["plan", jobId], plan); },
        },
      ).catch(() => undefined);
      navigate(`/jobs/${jobId}/plan`);
    },
  });
  const canPlan = Object.values(states).some((state) => state === "strengthen");
  return <section className="page">
    <div className="page-heading"><div><p className="eyebrow">由你决定</p><h1>选择希望加强的内容</h1><p>未选择不代表不会, 系统不会自动替你判断.</p></div></div>
    <div className="requirement-list">{job?.requirements.map((requirement) => <article key={requirement.id}><div className="requirement-copy"><span>{requirement.category}</span><h2>{requirement.label}</h2><blockquote>{requirement.evidence_text}</blockquote></div><div className="choice-group">{options.map((option) => <label key={option.value} className={states[requirement.id] === option.value ? "chosen" : ""}><input type="radio" name={requirement.id} value={option.value} checked={states[requirement.id] === option.value} onChange={() => setStates({ ...states, [requirement.id]: option.value })} />{states[requirement.id] === option.value && <Check size={15} />}{option.label}</label>)}</div></article>)}</div>
    <div className="footer-action"><button disabled={!canPlan || save.isPending || planTask.isPending} onClick={() => save.mutate()}>{save.isPending ? "正在保存选择" : planTask.isPending ? "正在生成计划" : "生成14天计划"}<ArrowRight size={17} /></button></div>
  </section>;
}
