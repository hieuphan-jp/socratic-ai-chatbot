/**
 * vite.config.ts
 *
 * JA: 開発サーバの設定。/api を Django(:8000) にプロキシする。
 *     こうするとブラウザから見て同一オリジン(localhost:5173)になり、
 *     セッション Cookie と CSRF が素直に動く（クロスオリジンの Cookie 問題を回避）。
 * VI: Cấu hình dev server. Proxy /api sang Django(:8000).
 *     Nhờ đó trình duyệt xem như cùng origin (localhost:5173), Cookie session và CSRF
 *     hoạt động trơn tru (tránh vấn đề Cookie cross-origin).
 *
 * JA: Tailwind は ai-learning-app02(Figmaデザイン移植) の見た目を機能ごとに取り込むために導入。
 *     src/index.css で preflight(全体リセット)を外しているので、Tailwind未使用の画面は影響を受けない。
 * VI: Thêm Tailwind để đưa dần giao diện của ai-learning-app02 (chuyển từ Figma) vào từng tính năng.
 *     src/index.css đã tắt preflight (reset toàn cục) nên màn hình chưa dùng Tailwind không bị ảnh hưởng.
 */
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // JA: '@/...' で src 直下を参照できるようにする（tsconfig の paths と一致）。
    // VI: Cho phép tham chiếu src bằng '@/...' (khớp với paths trong tsconfig).
    alias: { '@': '/src' },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: false,
      },
    },
  },
})
