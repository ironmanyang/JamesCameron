import { inject, provide } from "vue";

const WORKSPACE_CONTEXT_KEY = Symbol("workspace-context");

export function provideWorkspaceContext(value) {
  provide(WORKSPACE_CONTEXT_KEY, value);
}

export function useWorkspaceContext() {
  const context = inject(WORKSPACE_CONTEXT_KEY, null);
  if (!context) {
    throw new Error("Workspace context is not available.");
  }
  return context;
}
