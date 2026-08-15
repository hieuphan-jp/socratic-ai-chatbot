/**
 * main.tsx
 * JA: エントリポイント。#root に App を描画するだけ（全画面SPA構成の起点）。
 * VI: Điểm vào. Chỉ vẽ App vào #root (điểm khởi đầu kiến trúc SPA toàn trang).
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './app/App'

import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
