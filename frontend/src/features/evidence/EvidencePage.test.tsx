import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";

import { evidenceApi } from "../../api/client";
import { EvidencePage } from "./EvidencePage";

vi.mock("../../api/client", () => ({
  evidenceApi: { list: vi.fn(), remove: vi.fn() },
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

it("deletes an evidence record after confirmation", async () => {
  vi.mocked(evidenceApi.list).mockResolvedValue({
    items: [{
      id: "evidence-1", job_version_id: "version-1", requirement_ids: ["r1"],
      source_type: "practice_submission", source_id: "submission-1", title: "巡检记录",
      description: "服务运行正常.", verification_level: "self_reported",
      created_at: "2026-08-31T00:00:00Z",
    }],
  });
  vi.mocked(evidenceApi.remove).mockResolvedValue(undefined);
  vi.spyOn(window, "confirm").mockReturnValue(true);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><EvidencePage /></MemoryRouter></QueryClientProvider>);
  const user = userEvent.setup();

  await user.click(await screen.findByRole("button", { name: "删除证据记录" }));

  await waitFor(() => expect(evidenceApi.remove).toHaveBeenCalledWith("evidence-1"));
  expect(window.confirm).toHaveBeenCalled();
});
