import { useQuery } from "@tanstack/react-query";
import {
  BriefcaseBusiness,
  CalendarDays,
  FileCheck2,
  FileText,
  LayoutDashboard,
  Settings,
  SlidersHorizontal,
  Target,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { runtimeApi } from "../api/client";
import { useBackgroundTasks } from "./BackgroundTasks";

const CURRENT_JOB_STORAGE_KEY = "career-agent.current-job-id";

type NavigationItem = {
  label: string;
  path: string;
  icon: LucideIcon;
};

const flowNavigation: NavigationItem[] = [
  { label: "求职概览", path: "/dashboard", icon: LayoutDashboard },
  { label: "目标职位", path: "/jobs", icon: BriefcaseBusiness },
  { label: "学习与实训", path: "/practice", icon: Target },
  { label: "证据记录", path: "/evidence", icon: FileCheck2 },
  { label: "投递进展", path: "/applications", icon: CalendarDays },
];

function NavigationGroup({ label, items }: { label: string; items: NavigationItem[] }) {
  return (
    <div className="navigation-group">
      <span className="navigation-label">{label}</span>
      {items.map(({ label: itemLabel, path, icon: Icon }) => (
        <NavLink key={path} to={path} className={({ isActive }) => (isActive ? "active" : "")}>
          <Icon size={16} strokeWidth={1.7} aria-hidden="true" />
          {itemLabel}
        </NavLink>
      ))}
    </div>
  );
}

export function AppShell() {
  const location = useLocation();
  const routeJobId = location.pathname.match(/^\/jobs\/([^/]+)/)?.[1];
  const [recentJobId, setRecentJobId] = useState(() => window.localStorage.getItem(CURRENT_JOB_STORAGE_KEY));
  useEffect(() => {
    if (!routeJobId) return;
    setRecentJobId(routeJobId);
    window.localStorage.setItem(CURRENT_JOB_STORAGE_KEY, routeJobId);
  }, [routeJobId]);
  const { data: runtime } = useQuery({ queryKey: ["runtime"], queryFn: runtimeApi.get });
  const backgroundTasks = useBackgroundTasks();
  const pendingTasks = backgroundTasks.filter((task) => task.status === "pending");
  const currentJobId = routeJobId ?? recentJobId;
  const jobNavigation: NavigationItem[] = currentJobId
    ? [
        { label: "求职材料", path: `/jobs/${currentJobId}/materials`, icon: FileText },
        { label: "加强选择", path: `/jobs/${currentJobId}/selection`, icon: SlidersHorizontal },
        { label: "14天计划", path: `/jobs/${currentJobId}/plan`, icon: CalendarDays },
      ]
    : [];
  const runtimeLabel = runtime
    ? `${runtime.provider}${runtime.model ? ` / ${runtime.model}` : ""}`
    : "正在读取运行状态";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <strong>CAREER AGENT</strong>
          <span>求职成长工作台</span>
        </div>
        <nav aria-label="主导航">
          <NavigationGroup label="求职流程" items={flowNavigation} />
          {jobNavigation.length > 0 && <NavigationGroup label="当前职位" items={jobNavigation} />}
          <NavigationGroup label="系统" items={[{ label: "设置", path: "/settings", icon: Settings }]} />
        </nav>
        <div className="sidebar-note">
          <strong>本地工作区</strong>
          <span>{runtimeLabel}</span>
        </div>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <span>真实职位驱动的求职工作台</span>
          <div className="topbar-statuses">
            {pendingTasks.length > 0 && (
              <span className="background-task-status" role="status">
                后台生成中 {pendingTasks.length} 项
              </span>
            )}
            <span className={`status-dot ${runtime ? "online" : ""}`}>
              {runtime ? "系统正常" : "正在连接"}
            </span>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
