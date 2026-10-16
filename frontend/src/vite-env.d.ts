interface ImportMetaEnv {
  /** API origin for builds served apart from the API; empty means same origin. */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
