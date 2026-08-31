import { CirclePause, LogIn, Play, Radio } from "lucide-react";

import type { CollectorStatusView } from "../../api/client";

const statusLabels: Record<string, string> = {
  queued: "等待后台处理",
  running: "正在采集",
  paused: "已暂停",
  needs_login: "需要登录BOSS",
  needs_user_action: "需要用户处理",
  retry_wait: "等待重试",
  completed: "采集完成",
  failed: "采集失败",
  source_changed: "BOSS响应发生变化",
  rate_limited: "访问频率受限",
};

const reasonLabels: Record<string, string> = {
  risk_control: "BOSS返回访问环境异常, 请在专用窗口完成验证并保持窗口开启, 然后继续采集.",
  browser_not_open: "BOSS专用窗口未开启, 请先打开并登录.",
  unauthenticated: "BOSS登录状态已失效, 请重新登录.",
  truncated_response: "BOSS未返回完整职位信息, 请重新登录.",
  invalid_response: "BOSS响应未能读取, 请打开窗口检查当前页面.",
  source_error: "采集过程发生异常, 请重新创建任务.",
};

type Props = {
  data?: CollectorStatusView;
  offline: boolean;
  actionPending: boolean;
  onPause: () => void;
  onResume: () => void;
  onLogin: () => void;
};

export function CollectorStatus({ data, offline, actionPending, onPause, onResume, onLogin }: Props) {
  if (offline) {
    return (
      <section className="collector-status offline" aria-label="采集状态">
        <Radio size={18} />
        <div><strong>本机采集伴侣未启动</strong><p>运行 <code>career-collector start</code> 后即可从网页创建任务.</p></div>
      </section>
    );
  }
  if (!data) {
    return <section className="collector-status" aria-label="采集状态"><Radio size={18} /><div><strong>正在连接采集伴侣</strong></div></section>;
  }
  const task = data.task;
  if (!task) {
    return <section className="collector-status" aria-label="采集状态"><Radio size={18} /><div><strong>采集伴侣已连接</strong><p>可以创建BOSS职位后台采集任务.</p></div></section>;
  }
  const loginReady = data.login.status === "browser_open";
  const canLogin = task.status === "needs_user_action" || (task.status === "needs_login" && !loginReady);
  const canResume = task.status === "paused" || task.status === "retry_wait" || (["needs_login", "needs_user_action"].includes(task.status) && loginReady);
  const canPause = ["queued", "running"].includes(task.status);
  const progress = Math.min(100, Math.round((task.captured_count / Math.max(1, task.requested_limit)) * 100));

  return (
    <section className="collector-status" aria-label="采集状态">
      <Radio size={18} />
      <div className="collector-status-copy">
        <div><strong>{statusLabels[task.status] ?? task.status}</strong><span>{task.keyword} · {task.city}</span></div>
        {task.reason_code && reasonLabels[task.reason_code] && <p>{reasonLabels[task.reason_code]}</p>}
        <p>已采集 {task.captured_count}/{task.requested_limit}, 待同步 {task.pending_sync_count}</p>
        <div className="collector-progress" aria-label="采集进度"><span style={{ width: `${progress}%` }} /></div>
      </div>
      <div className="collector-status-actions">
        {canLogin && <button className="secondary" disabled={actionPending} onClick={onLogin}><LogIn size={15} />{task.status === "needs_user_action" ? "打开BOSS处理" : "登录BOSS"}</button>}
        {canResume && <button className="secondary" disabled={actionPending} onClick={onResume}><Play size={15} />继续采集</button>}
        {canPause && <button className="secondary" disabled={actionPending} onClick={onPause}><CirclePause size={15} />暂停采集</button>}
      </div>
    </section>
  );
}
