import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BadgeCheck, FileCheck2, Trash2 } from "lucide-react";

import type { EvidenceItem } from "../../api/client";
import { evidenceApi } from "../../api/client";

export function EvidencePage() {
  const queryClient = useQueryClient();
  const { data } = useQuery({ queryKey: ["evidence"], queryFn: evidenceApi.list });
  const remove = useMutation({
    mutationFn: (id: string) => evidenceApi.remove(id),
    onSuccess: (_, deletedId) => {
      queryClient.setQueryData<{ items: EvidenceItem[] }>(["evidence"], (current) => ({
        items: current?.items.filter((item) => item.id !== deletedId) ?? [],
      }));
    },
  });
  return <section className="page"><div className="page-heading"><div><p className="eyebrow">可验证成果</p><h1>证据库</h1><p>集中查看学习、实训和外部验证形成的成果记录.</p></div></div>
    <div className="evidence-list">{data?.items.map((item) => <article key={item.id}><FileCheck2 size={20} /><div><div className="row-title"><h2>{item.title}</h2><span className="state-badge"><BadgeCheck size={13} />{item.verification_level}</span></div><p>{item.description}</p><small>{new Date(item.created_at).toLocaleString("zh-CN")}</small></div><button className="icon-button danger" aria-label="删除证据记录" title="删除证据记录" disabled={remove.isPending} onClick={() => { if (window.confirm("删除这条证据记录?")) remove.mutate(item.id); }}><Trash2 size={16} /></button></article>)}</div>
    {!data?.items.length && <div className="empty-state">完成一次实训提交后, 证据会出现在这里.</div>}
  </section>;
}
