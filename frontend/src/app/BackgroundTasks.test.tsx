import { act, cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, expect, it, vi } from "vitest";

import { BackgroundTaskProvider, useBackgroundTask } from "./BackgroundTasks";

afterEach(() => cleanup());

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

function TaskView({ execute }: { execute: () => Promise<string> }) {
  const task = useBackgroundTask<string>("materials:job-1");
  return <div>
    <span>{task.status}</span>
    {task.data && <strong>{task.data}</strong>}
    <button onClick={() => task.run(execute)}>生成</button>
  </div>;
}

function Harness({ execute }: { execute: () => Promise<string> }) {
  const [visible, setVisible] = useState(true);
  return <BackgroundTaskProvider>
    <button onClick={() => setVisible((current) => !current)}>切换页面</button>
    {visible && <TaskView execute={execute} />}
  </BackgroundTaskProvider>;
}

it("keeps a pending task alive while its page is unmounted and restores its result", async () => {
  const pending = deferred<string>();
  const execute = vi.fn(() => pending.promise);
  const user = userEvent.setup();
  render(<Harness execute={execute} />);

  await user.click(screen.getByRole("button", { name: "生成" }));
  expect(screen.getByText("pending")).toBeVisible();
  await user.click(screen.getByRole("button", { name: "切换页面" }));
  await act(async () => pending.resolve("生成完成"));
  await user.click(screen.getByRole("button", { name: "切换页面" }));

  expect(screen.getByText("success")).toBeVisible();
  expect(screen.getByText("生成完成")).toBeVisible();
  expect(execute).toHaveBeenCalledTimes(1);
});

it("deduplicates repeated starts for the same pending task", async () => {
  const pending = deferred<string>();
  const execute = vi.fn(() => pending.promise);
  const user = userEvent.setup();
  render(<BackgroundTaskProvider><TaskView execute={execute} /></BackgroundTaskProvider>);

  const button = screen.getByRole("button", { name: "生成" });
  await user.click(button);
  await user.click(button);

  expect(execute).toHaveBeenCalledTimes(1);
});
