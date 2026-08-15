/**
 * features/hintChat/components/ChatInputForm.tsx
 *
 * JA: メッセージ入力フォームコンポーネント (Tailwind CSS版)
 * VI: Component Form nhập liệu và gửi tin nhắn (Dùng Tailwind CSS v4)
 */

import React, { useState } from 'react'

interface ChatInputFormProps {
  onSendMessage: (text: string) => void
  disabled?: boolean
  isPending?: boolean
}

export const ChatInputForm: React.FC<ChatInputFormProps> = ({
  onSendMessage,
  disabled = false,
  isPending = false,
}) => {
  const [inputText, setInputText] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || disabled) return
    onSendMessage(inputText)
    setInputText('')
  }

  const isButtonDisabled = disabled || !inputText.trim()

  return (
    <form onSubmit={handleSubmit} className="flex w-full gap-2 box-border">
      <input
        type="text"
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        placeholder="質問を入力 / Nhập câu hỏi"
        className="flex-1 rounded-md border border-gray-300 px-3.5 py-2.5 text-xs outline-none focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        disabled={disabled}
      />
      <button
        type="submit"
        disabled={isButtonDisabled}
        className={`rounded-md border border-gray-300 bg-gray-100 px-6 py-2.5 text-xs font-medium text-gray-700 transition-opacity ${
          isButtonDisabled
            ? 'opacity-60 cursor-not-allowed'
            : 'hover:bg-gray-200 cursor-pointer'
        }`}
      >
        {isPending ? '送信中...' : '送信 / Gửi'}
      </button>
    </form>
  )
}