export function apiBase() {
  return useRuntimeConfig().public.apiBase
}

export function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`
}
