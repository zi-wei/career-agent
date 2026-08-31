import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bookmark, BookmarkCheck, FilePlus2, Search, SearchCheck, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import type { JobDetail, JobList } from "../../api/client";
import { collectorApi, jobsApi } from "../../api/client";
import { CollectorDialog } from "./CollectorDialog";
import { CollectorStatus } from "./CollectorStatus";
import { JobImportDialog } from "./JobImportDialog";

type JobTab = "review" | "saved";

export function JobsPage() {
  const queryClient = useQueryClient();
  const [importing, setImporting] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [notice, setNotice] = useState("");
  const [localJobs, setLocalJobs] = useState<JobDetail[]>([]);
  const [tab, setTab] = useState<JobTab>("review");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const { data, isLoading } = useQuery({ queryKey: ["jobs"], queryFn: jobsApi.list });
  const collector = useQuery({
    queryKey: ["collector-status"],
    queryFn: collectorApi.status,
    retry: false,
    refetchInterval: 2000,
  });
  const previousTaskState = useRef("");
  useEffect(() => {
    const task = collector.data?.task;
    if (!task) return;
    const signature = `${task.id}:${task.status}:${task.captured_count}:${task.pending_sync_count}`;
    if (signature !== previousTaskState.current && (task.captured_count > 0 || task.status === "completed")) {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    }
    previousTaskState.current = signature;
  }, [collector.data?.task, queryClient]);

  const refreshCollector = () => queryClient.invalidateQueries({ queryKey: ["collector-status"] });
  const pause = useMutation({ mutationFn: collectorApi.pause, onSuccess: refreshCollector });
  const resume = useMutation({ mutationFn: collectorApi.resume, onSuccess: refreshCollector });
  const login = useMutation({
    mutationFn: collectorApi.login,
    onSuccess: () => {
      setNotice("BOSS专用窗口已打开, 完成登录或验证后请保持窗口开启, 然后继续采集.");
      refreshCollector();
    },
  });

  const jobs = [
    ...localJobs,
    ...(data?.items ?? []).filter((job) => !localJobs.some((item) => item.id === job.id)),
  ];
  const reviewJobs = jobs.filter((job) => !job.is_saved);
  const savedJobs = jobs.filter((job) => job.is_saved);
  const visibleJobs = tab === "saved" ? savedJobs : reviewJobs;

  const replaceCachedJob = (updated: JobDetail) => {
    setLocalJobs((items) => items.map((item) => (item.id === updated.id ? updated : item)));
    queryClient.setQueryData<JobList>(["jobs"], (current) => ({
      items: (current?.items ?? []).map((item) => (item.id === updated.id ? updated : item)),
    }));
  };
  const removeCachedJobs = (ids: string[]) => {
    const removed = new Set(ids);
    setLocalJobs((items) => items.filter((item) => !removed.has(item.id)));
    queryClient.setQueryData<JobList>(["jobs"], (current) => ({
      items: (current?.items ?? []).filter((item) => !removed.has(item.id)),
    }));
    setSelectedIds((items) => items.filter((id) => !removed.has(id)));
  };
  const saved = useMutation({
    mutationFn: ({ id, value }: { id: string; value: boolean }) => jobsApi.updateSaved(id, value),
    onSuccess: (updated) => {
      replaceCachedJob(updated);
      setSelectedIds((items) => items.filter((id) => id !== updated.id));
      setNotice(updated.is_saved ? "已收藏目标职位." : "已移回待筛选职位.");
    },
    onError: () => setNotice("更新收藏状态失败, 请稍后重试."),
  });
  const remove = useMutation({
    mutationFn: (jobId: string) => jobsApi.remove(jobId),
    onSuccess: (_, jobId) => {
      removeCachedJobs([jobId]);
      setNotice("已删除 1 个职位.");
    },
    onError: () => setNotice("删除职位失败, 请稍后重试."),
  });
  const batch = useMutation({
    mutationFn: ({ ids, action }: { ids: string[]; action: "save" | "unsave" | "delete" }) =>
      jobsApi.batchAction(ids, action),
    onSuccess: ({ affected_count }, { ids, action }) => {
      if (action === "delete") {
        removeCachedJobs(ids);
        setNotice(`已删除 ${affected_count} 个职位.`);
        return;
      }
      const value = action === "save";
      const selected = new Set(ids);
      setLocalJobs((items) => items.map((item) => selected.has(item.id) ? { ...item, is_saved: value } : item));
      queryClient.setQueryData<JobList>(["jobs"], (current) => ({
        items: (current?.items ?? []).map((item) => selected.has(item.id) ? { ...item, is_saved: value } : item),
      }));
      setSelectedIds([]);
      setNotice(value ? `已收藏 ${affected_count} 个职位.` : `已取消收藏 ${affected_count} 个职位.`);
    },
    onError: () => setNotice("批量操作失败, 请稍后重试."),
  });
  const clear = useMutation({
    mutationFn: jobsApi.clear,
    onSuccess: ({ deleted_count }) => {
      setLocalJobs([]);
      queryClient.setQueryData(["jobs"], { items: [] });
      setSelectedIds([]);
      setNotice(`已清空 ${deleted_count} 个职位.`);
    },
    onError: () => setNotice("清空职位失败, 请稍后重试."),
  });

  const handleRemove = (job: JobDetail) => {
    if (window.confirm(`确认删除职位“${job.title}”? 关联材料、计划和投递记录也会删除.`)) {
      remove.mutate(job.id);
    }
  };
  const handleBatchDelete = () => {
    if (window.confirm(`确认删除选中的 ${selectedIds.length} 个职位? 此操作不可撤销.`)) {
      batch.mutate({ ids: selectedIds, action: "delete" });
    }
  };
  const handleClear = () => {
    if (window.confirm("确认清空全部职位? 关联的求职材料、计划和投递记录也会删除, 此操作不可撤销.")) {
      clear.mutate();
    }
  };
  const toggleSelected = (jobId: string) => {
    setSelectedIds((items) => items.includes(jobId) ? items.filter((id) => id !== jobId) : [...items, jobId]);
  };
  const actionPending = pause.isPending || resume.isPending || login.isPending;

  return (
    <section className="page">
      <div className="page-heading">
        <div><p className="eyebrow">职位池</p><h1>真实职位</h1><p>先筛选采集结果, 再围绕收藏职位准备材料和实训.</p></div>
        <div className="heading-actions">
          <button onClick={() => setCollecting(true)} disabled={collector.isError}><SearchCheck size={17} />采集职位</button>
          <button className="secondary" onClick={() => setImporting(true)}><FilePlus2 size={17} />导入职位</button>
          <button className="secondary danger" onClick={handleClear} disabled={jobs.length === 0 || clear.isPending}>
            <Trash2 size={17} />{clear.isPending ? "正在清空" : "清空职位"}
          </button>
        </div>
      </div>
      <CollectorStatus data={collector.data} offline={collector.isError} actionPending={actionPending} onPause={() => pause.mutate()} onResume={() => resume.mutate()} onLogin={() => login.mutate()} />
      {notice && <p className="collector-notice">{notice}</p>}

      <div className="job-tabs" role="tablist" aria-label="职位分类">
        <button className={tab === "review" ? "active" : ""} aria-label={`待筛选 ${reviewJobs.length}`} onClick={() => { setTab("review"); setSelectedIds([]); }}>待筛选<span>{reviewJobs.length}</span></button>
        <button className={tab === "saved" ? "active" : ""} aria-label={`已收藏 ${savedJobs.length}`} onClick={() => { setTab("saved"); setSelectedIds([]); }}>已收藏<span>{savedJobs.length}</span></button>
      </div>
      <div className="job-toolbar">
        <div><Search size={16} /><span>{visibleJobs.length} 个职位</span></div>
        {selectedIds.length > 0 && <div className="batch-actions">
          <span>已选 {selectedIds.length} 个</span>
          <button className="secondary" onClick={() => batch.mutate({ ids: selectedIds, action: tab === "saved" ? "unsave" : "save" })}>
            {tab === "saved" ? <Bookmark size={15} /> : <BookmarkCheck size={15} />}{tab === "saved" ? "取消收藏" : "批量收藏"}
          </button>
          <button className="secondary danger" onClick={handleBatchDelete}><Trash2 size={15} />批量删除</button>
        </div>}
      </div>

      {isLoading ? <p className="empty-state">正在读取职位</p> : visibleJobs.length === 0 ? (
        <p className="empty-state">{tab === "saved" ? "暂无收藏职位" : "暂无待筛选职位"}</p>
      ) : (
        <div className="job-list selectable-job-list">
          {visibleJobs.map((job) => (
            <article className="selectable-job-row" key={job.id}>
              <label className="job-checkbox"><input type="checkbox" checked={selectedIds.includes(job.id)} onChange={() => toggleSelected(job.id)} aria-label={`选择 ${job.title}`} /></label>
              <Link to={`/jobs/${job.id}`} className="job-row-main">
                <div><strong>{job.title}</strong><span>{job.company}</span></div>
                <div className="job-meta"><span>{job.city || "城市未填写"}</span><span>v{job.current_version.ordinal}</span><span>{job.source}</span></div>
              </Link>
              <div className="job-row-actions">
                <button className={`icon-button ${job.is_saved ? "saved" : ""}`} onClick={() => saved.mutate({ id: job.id, value: !job.is_saved })} aria-label={`${job.is_saved ? "取消收藏" : "收藏"} ${job.title}`} title={job.is_saved ? "取消收藏" : "收藏职位"}>{job.is_saved ? <BookmarkCheck size={17} /> : <Bookmark size={17} />}</button>
                <button className="icon-button danger" onClick={() => handleRemove(job)} aria-label={`删除 ${job.title}`} title="删除职位"><Trash2 size={17} /></button>
              </div>
            </article>
          ))}
        </div>
      )}
      {importing && <JobImportDialog onClose={() => setImporting(false)} onImported={(job) => {
        setLocalJobs((items) => [job, ...items.filter((item) => item.id !== job.id)]);
        if (job.is_saved) setTab("saved");
        setImporting(false);
      }} />}
      {collecting && <CollectorDialog onClose={() => setCollecting(false)} onCreated={() => {
        setCollecting(false);
        setTab("review");
        setNotice("任务已加入后台队列.");
        refreshCollector();
      }} />}
    </section>
  );
}
