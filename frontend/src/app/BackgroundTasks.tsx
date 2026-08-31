import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

export type BackgroundTaskStatus = "idle" | "pending" | "success" | "error";

export type BackgroundTaskState<T = unknown> = {
  key: string;
  label: string;
  status: BackgroundTaskStatus;
  startedAt: number | null;
  data: T | undefined;
  error: unknown;
};

type RunOptions<T> = {
  label?: string;
  onSuccess?: (data: T) => void | Promise<void>;
};

type BackgroundTaskContextValue = {
  tasks: Record<string, BackgroundTaskState>;
  runTask: <T>(key: string, execute: () => Promise<T>, options?: RunOptions<T>) => Promise<T>;
};

const BackgroundTaskContext = createContext<BackgroundTaskContextValue | null>(null);

export function BackgroundTaskProvider({ children }: { children: ReactNode }) {
  const [tasks, setTasks] = useState<Record<string, BackgroundTaskState>>({});
  const running = useRef(new Map<string, Promise<unknown>>());

  const runTask = useCallback(<T,>(key: string, execute: () => Promise<T>, options?: RunOptions<T>) => {
    const existing = running.current.get(key);
    if (existing) return existing as Promise<T>;

    const startedAt = Date.now();
    setTasks((current) => ({
      ...current,
      [key]: {
        key,
        label: options?.label ?? key,
        status: "pending",
        startedAt,
        data: undefined,
        error: undefined,
      },
    }));

    const promise = Promise.resolve()
      .then(execute)
      .then(async (data) => {
        await options?.onSuccess?.(data);
        setTasks((current) => ({
          ...current,
          [key]: { ...current[key], status: "success", data, error: undefined },
        }));
        return data;
      })
      .catch((error: unknown) => {
        setTasks((current) => ({
          ...current,
          [key]: { ...current[key], status: "error", data: undefined, error },
        }));
        throw error;
      })
      .finally(() => running.current.delete(key));

    running.current.set(key, promise);
    return promise;
  }, []);

  const value = useMemo(() => ({ tasks, runTask }), [runTask, tasks]);
  return <BackgroundTaskContext.Provider value={value}>{children}</BackgroundTaskContext.Provider>;
}

function useBackgroundTaskContext() {
  const context = useContext(BackgroundTaskContext);
  if (!context) throw new Error("BackgroundTaskProvider is required");
  return context;
}

export function useBackgroundTask<T>(key: string) {
  const { tasks, runTask } = useBackgroundTaskContext();
  const task = tasks[key] as BackgroundTaskState<T> | undefined;
  const state: BackgroundTaskState<T> = task ?? {
    key,
    label: key,
    status: "idle",
    startedAt: null,
    data: undefined,
    error: undefined,
  };
  const run = useCallback(
    (execute: () => Promise<T>, options?: RunOptions<T>) => runTask(key, execute, options),
    [key, runTask],
  );
  return { ...state, run, isPending: state.status === "pending" };
}

export function useBackgroundTasks() {
  const { tasks } = useBackgroundTaskContext();
  return Object.values(tasks);
}

export function useElapsedSeconds(startedAt: number | null, running: boolean) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!running || startedAt === null) {
      setElapsed(0);
      return;
    }
    const update = () => setElapsed(Math.max(0, Math.floor((Date.now() - startedAt) / 1000)));
    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, [running, startedAt]);
  return elapsed;
}
