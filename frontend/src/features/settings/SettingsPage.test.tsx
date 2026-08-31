import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { modelSettingsApi, runtimeApi } from "../../api/client";
import { SettingsPage } from "./SettingsPage";

vi.mock("../../api/client", () => ({
  runtimeApi: { get: vi.fn() },
  modelSettingsApi: { get: vi.fn(), models: vi.fn(), update: vi.fn(), test: vi.fn() },
}));

afterEach(cleanup);

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(modelSettingsApi.get).mockResolvedValue({
    provider: "demo",
    base_url: "",
    model: "",
    api_key_configured: false,
  });
});

it("shows active provider and background collector commands", async () => {
  vi.mocked(runtimeApi.get).mockResolvedValue({
    provider: "openai-compatible",
    model: "deepseek-chat",
    model_configured: true,
    collector_sync_enabled: true,
  });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><SettingsPage /></MemoryRouter></QueryClientProvider>);

  expect(await screen.findByText("openai-compatible / deepseek-chat")).toBeVisible();
  expect(screen.getByText("career-collector start")).toBeVisible();
  expect(screen.getByText(/--background/)).toBeVisible();
});

it("provides editable model connection controls", async () => {
  vi.mocked(runtimeApi.get).mockResolvedValue({
    provider: "demo",
    model: "",
    model_configured: false,
    collector_sync_enabled: true,
  });
  vi.mocked(modelSettingsApi.models).mockResolvedValue({ items: ["gpt-5.4", "gpt-5.5"] });
  vi.mocked(modelSettingsApi.update).mockResolvedValue({
    provider: "openai-compatible",
    base_url: "https://api.example.com/v1",
    model: "gpt-5.5",
    api_key_configured: true,
  });
  vi.mocked(modelSettingsApi.test).mockResolvedValue({ status: "ok", model: "gpt-5.5", latency_ms: 120 });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><SettingsPage /></MemoryRouter></QueryClientProvider>);
  const user = userEvent.setup();

  await user.type(await screen.findByLabelText("服务地址"), "https://api.example.com/v1");
  await user.type(screen.getByLabelText("API Key"), "test-secret");
  expect(screen.getByLabelText("API Key")).toHaveAttribute("type", "password");
  expect(screen.getByLabelText("模型")).toBeVisible();
  await user.click(screen.getByRole("button", { name: "拉取模型" }));
  expect(await screen.findByRole("option", { name: "gpt-5.5" })).toBeVisible();
  expect(screen.getByLabelText("模型")).toHaveValue("gpt-5.5");
  await user.click(screen.getByRole("button", { name: "保存并测试" }));

  expect(modelSettingsApi.update).toHaveBeenCalledWith({
    base_url: "https://api.example.com/v1",
    api_key: "test-secret",
    model: "gpt-5.5",
  });
  expect(modelSettingsApi.test).toHaveBeenCalledWith({
    base_url: "https://api.example.com/v1",
    model: "gpt-5.5",
  });
  expect(await screen.findByText("已启用gpt-5.5, 连接测试120ms.")).toBeVisible();
});
