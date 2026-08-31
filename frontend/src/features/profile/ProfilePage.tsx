import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Save, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import type { ProfileFact, WorkspaceProfile } from "../../api/client";
import { workspaceApi } from "../../api/client";

const emptyProfile: Omit<WorkspaceProfile, "id"> = {
  target_role: "",
  cities: [],
  availability: "",
  raw_resume: "",
  facts: [],
};

export function ProfilePage() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["profile"], queryFn: workspaceApi.get });
  const [form, setForm] = useState(emptyProfile);
  useEffect(() => {
    if (data) {
      const { id: _, ...editable } = data;
      setForm(editable);
    }
  }, [data]);
  const mutation = useMutation({
    mutationFn: workspaceApi.update,
    onSuccess: (profile) => queryClient.setQueryData(["profile"], profile),
  });
  function updateFact(index: number, field: keyof ProfileFact, value: string) {
    setForm((current) => ({ ...current, facts: current.facts.map((fact, i) => i === index ? { ...fact, [field]: value } : fact) }));
  }
  return (
    <section className="page narrow-page">
      <div className="page-heading"><div><p className="eyebrow">事实来源</p><h1>求职档案</h1><p>这里只保存你明确提供的经历, 不根据缺失内容判断能力.</p></div><button onClick={() => mutation.mutate(form)}><Save size={17} />保存档案</button></div>
      <div className="form-grid">
        <label>目标岗位<input value={form.target_role} onChange={(e) => setForm({ ...form, target_role: e.target.value })} /></label>
        <label>目标城市<input value={form.cities.join(", ")} onChange={(e) => setForm({ ...form, cities: e.target.value.split(/[,，]/).map((value) => value.trim()).filter(Boolean) })} /></label>
        <label className="full-span">到岗条件<input value={form.availability} onChange={(e) => setForm({ ...form, availability: e.target.value })} /></label>
        <label className="full-span">原始简历<textarea rows={8} value={form.raw_resume} onChange={(e) => setForm({ ...form, raw_resume: e.target.value })} /></label>
      </div>
      <div className="section-heading"><div><h2>真实经历与成果</h2><p>每一项都可以成为简历内容的来源.</p></div><button className="secondary" onClick={() => setForm({ ...form, facts: [...form.facts, { kind: "project", title: "", content: "" }] })}><Plus size={16} />添加经历</button></div>
      <div className="fact-list">
        {form.facts.map((fact, index) => <div className="fact-editor" key={fact.id ?? index}>
          <select aria-label="经历类型" value={fact.kind} onChange={(e) => updateFact(index, "kind", e.target.value)}><option value="project">项目</option><option value="skill">技能</option><option value="experience">经历</option><option value="education">教育</option></select>
          <input aria-label="经历标题" placeholder="标题" value={fact.title} onChange={(e) => updateFact(index, "title", e.target.value)} />
          <textarea aria-label="经历内容" placeholder="具体做了什么, 有哪些可验证结果" value={fact.content} onChange={(e) => updateFact(index, "content", e.target.value)} />
          <button className="icon-button danger" aria-label="删除经历" onClick={() => setForm({ ...form, facts: form.facts.filter((_, i) => i !== index) })}><Trash2 size={17} /></button>
        </div>)}
      </div>
      {mutation.isSuccess && <p className="success-message">档案已保存</p>}
    </section>
  );
}
