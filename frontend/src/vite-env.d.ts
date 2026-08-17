/// <reference types="vite/client" />

interface ImportMetaEnv {
  // JA: 本番でバックエンドが別ドメインのときに使う。未設定ならローカルの '/api' 相対パスにフォールバックする。
  // VI: Dùng khi backend ở domain khác lúc production. Không đặt thì fallback về đường dẫn tương đối '/api' của local.
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
