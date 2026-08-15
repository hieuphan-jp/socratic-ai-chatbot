/**
 * src/pages/HintChatPage.tsx
 *
 * JA: ヒントチャットページ (日英対応)
 * VI: Trang Hint Chat chính (Hỗ trợ Việt - Nhật)
 */

import React, { useState } from 'react'
import { HintChatView } from '../features/hintChat/components/HintChatView'

export const HintChatPage: React.FC = () => {
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>(undefined)

  return (
    <div className="container mx-auto max-w-6xl p-4">
      <h1 className="mb-4 text-xl font-bold text-gray-800">
        💡 ヒントチャット / Hint Chat
      </h1>

      {/* Gọi trực tiếp HintChatView */}
      <HintChatView
        activeSessionId={activeSessionId}
        onSessionCreated={(newId) => setActiveSessionId(newId)}
      />
    </div>
  )
}

export default HintChatPage