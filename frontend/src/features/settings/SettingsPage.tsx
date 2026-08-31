import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Database, KeyRound, MonitorCog, RefreshCw, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, modelSettingsApi, runtimeApi } from "../../api/client";

const errorMessages: Record<string, string> = {
  invalid_model_base_url: "服务地址必须使用HTTPS, 本地服务可使用localhost HTTP.",
  model_api_key_required: "请输入API Key.",
  model_name_required: "请选择模型.",
  model_service_auth_failed: "API Key无效或没有访问权限.",
  model_service_request_failed: "模型服务拒绝了请求.",
  invalid_model_response: "模型服务返回的数据格式不兼容.",
  model_service_unavailable: "模型服务暂时不可用.",
  model_service_unreachable: "无法连接模型服务, 请检查地址和网络.",
  model_settings_write_failed: "本地配置写入失败.",
};

function errorMessage(error: unknown) {
  if (error instanceof ApiError) return errorMessages[error.code] ?? `配置失败: ${error.code}`;
  return "配置失败, 请稍后重试.";
}

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: runtime } = useQuery({ queryKey: ["runtime"], queryFn: runtimeApi.get });
  const settings = useQuery({ queryKey: ["model-settings"], queryFn: modelSettingsApi.get });
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [models, setModels] = useState<string[]>([]);
  const [savedMessage, setSavedMessage] = useState("");

  useEffect(() => {
    if (settings.data) {
      setBaseUrl(settings.data.base_url);
      setModel(settings.data.model);
      setModels(settings.data.model ? [settings.data.model] : []);
    }
  }, [settings.data]);

  const connectionPayload = () => ({
    base_url: baseUrl.trim(),
    ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
  });
  const pullModels = useMutation({
    mutationFn: () => modelSettingsApi.models(connectionPayload()),
    onSuccess: ({ items }) => {
      setModels(items);
      if (items.includes("gpt-5.5")) setModel("gpt-5.5");
      else if (!items.includes(model)) setModel(items[0] ?? "");
      setSavedMessage(`已读取${items.length}个模型.`);
    },
  });
  const saveAndTest = useMutation({
    mutationFn: async () => {
      const saved = await modelSettingsApi.update({
        ...connectionPayload(),
        model,
      });
      const tested = await modelSettingsApi.test({
        base_url: saved.base_url,
        model: saved.model,
      });
      return { saved, tested };
    },
    onSuccess: ({ saved, tested }) => {
      setApiKey("");
      setSavedMessage(`已启用${saved.model}, 连接测试${tested.latency_ms}ms.`);
      queryClient.setQueryData(["model-settings"], saved);
      queryClient.invalidateQueries({ queryKey: ["runtime"] });
    },
  });

  const providerLabel = runtime
    ? `${runtime.provider}${runtime.model ? ` / ${runtime.model}` : ""}`
    : "读取中";
  const hasKey = Boolean(apiKey.trim() || settings.data?.api_key_configured);
  const modelOptions = Array.from(new Set([...(model ? [model] : []), ...models]));

  return (
    <section className="page narrow-page">
      <div className="page-heading">
        <div><p className="eyebrow">本地配置</p><h1>设置</h1><p>管理档案、模型服务和本地职位采集伴侣.</p></div>
      </div>
      <div className="settings-list">
        <article>
          <Database />
          <div><h2>求职档案</h2><p>目标岗位、城市和真实经历是所有生成内容的事实来源.</p></div>
          <Link className="button-link secondary" to="/profile">编辑档案</Link>
        </article>
        <article className="settings-model">
          <KeyRound />
          <div>
            <h2>模型服务</h2>
            <p>密钥保存在本机后端独立配置中, 不进入业务数据库且不会回显.</p>
            <code>{providerLabel}</code>
          </div>
          <span className={`state-badge ${runtime?.model_configured ? "completed" : ""}`}>
            {runtime?.model_configured ? "已启用" : "待配置"}
          </span>
          <div className="model-settings-form">
            <label className="base-url-field">服务地址
              <input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} placeholder="https://api.example.com/v1" autoComplete="url" />
            </label>
            <label>API Key
              <input type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder={settings.data?.api_key_configured ? "已保存, 留空则继续使用" : "输入API Key"} autoComplete="off" />
            </label>
            <label>模型
              <select value={model} onChange={(event) => setModel(event.target.value)} disabled={modelOptions.length === 0}>
                {modelOptions.length === 0 && <option value="">先拉取模型</option>}
                {modelOptions.map((item) => <option value={item} key={item}>{item}</option>)}
              </select>
            </label>
            <div className="model-settings-actions">
              <button className="secondary" disabled={!baseUrl.trim() || !hasKey || pullModels.isPending} onClick={() => pullModels.mutate()}>
                <RefreshCw size={16} />{pullModels.isPending ? "正在拉取" : "拉取模型"}
              </button>
              <button disabled={!baseUrl.trim() || !hasKey || !model || saveAndTest.isPending} onClick={() => saveAndTest.mutate()}>
                <Save size={16} />{saveAndTest.isPending ? "正在测试" : "保存并测试"}
              </button>
            </div>
            {(pullModels.error || saveAndTest.error) && <p className="form-error">{errorMessage(pullModels.error ?? saveAndTest.error)}</p>}
            {savedMessage && !pullModels.error && !saveAndTest.error && <p className="success-message">{savedMessage}</p>}
          </div>
        </article>
        <article>
          <MonitorCog />
          <div>
            <h2>职位采集伴侣</h2>
            <p>后台采集使用独立Edge Profile, 遇到登录或验证码会暂停并保留检查点.</p>
            <div className="command-list">
              <code>career-collector start</code>
              <code>career-collector collect --source boss --keyword "运维实习生" --city "上海" --limit 20 --background</code>
              <code>career-collector status</code>
              <code>career-collector stop</code>
            </div>
          </div>
          <span className={`state-badge ${runtime?.collector_sync_enabled ? "completed" : ""}`}>
            {runtime?.collector_sync_enabled ? "同步已启用" : "待配置"}
          </span>
        </article>
      </div>
    </section>
  );
}
