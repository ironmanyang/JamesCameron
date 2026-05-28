export function buildWorkspaceContextValue({
  core,
  derived,
  options,
  helpers,
  editing,
  localHelpers,
  formatters,
  parsedScriptEditor,
  sceneDirect,
  actions
}) {
  return {
    ...core,
    ...derived,
    ...options,
    ...helpers,
    ...editing,
    ...localHelpers,
    ...formatters,
    ...parsedScriptEditor,
    ...sceneDirect,
    ...actions
  };
}
