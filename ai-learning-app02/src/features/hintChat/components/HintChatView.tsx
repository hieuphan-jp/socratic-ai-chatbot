import React, { useState } from 'react';
import { Send, Bot, User, Columns, PanelRightClose } from 'lucide-react';
import type { ChatMessage } from '../types';

interface HintChatViewProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  isSplitView: boolean;
  onToggleSplitView: () => void;
}

export const HintChatView: React.FC<HintChatViewProps> = ({
  messages,
  onSendMessage,
  isSplitView,
  onToggleSplitView,
}) => {
  const [input, setInput] = useState('');

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
      {/* Header Khung Chat */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-100 text-indigo-600 rounded-2xl">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-800 text-sm">Trợ lý AI Hint Chat</h3>
            <p className="text-[11px] text-slate-400">AI ヒントチャットアシスタント</p>
          </div>
        </div>

        {/* Nút Toggle Chia đôi màn hình */}
        <button
          onClick={onToggleSplitView}
          className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium transition-all border ${
            isSplitView
              ? 'bg-indigo-50 border-indigo-200 text-indigo-600'
              : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
          title="Bật/Tắt sơ đồ cây từng bước"
        >
          {isSplitView ? (
            <>
              <PanelRightClose className="w-4 h-4" />
              <span className="hidden sm:inline">Thu gọn sơ đồ (ツリーを閉じる)</span>
            </>
          ) : (
            <>
              <Columns className="w-4 h-4 text-indigo-500" />
              <span className="hidden sm:inline">Xem Sơ đồ các bước (ステップツリー)</span>
            </>
          )}
        </button>
      </div>

      {/* Nội dung danh sách tin nhắn */}
      <div className="flex-1 p-6 space-y-4 overflow-y-auto min-h-[400px] max-h-[550px]">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${
              msg.sender === 'user' ? 'flex-row-reverse' : ''
            }`}
          >
            <div
              className={`w-8 h-8 rounded-2xl flex items-center justify-center text-xs font-medium shrink-0 ${
                msg.sender === 'user'
                  ? 'bg-teal-100 text-teal-700'
                  : 'bg-indigo-100 text-indigo-700'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`max-w-[80%] p-4 rounded-3xl text-sm leading-relaxed whitespace-pre-wrap ${
                msg.sender === 'user'
                  ? 'bg-teal-500 text-white rounded-tr-none'
                  : 'bg-slate-100/80 text-slate-800 rounded-tl-none border border-slate-200/50'
              }`}
            >
              {msg.text}
              <div
                className={`text-[10px] mt-1.5 text-right ${
                  msg.sender === 'user' ? 'text-teal-100' : 'text-slate-400'
                }`}
              >
                {msg.timestamp}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Input gửi tin nhắn */}
      <form onSubmit={handleSend} className="p-4 border-t border-slate-100 bg-slate-50/30 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Nhập câu hỏi của bạn... (質問を入力してください)"
          className="flex-1 px-4 py-3 bg-white rounded-2xl border border-slate-200 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all"
        />
        <button
          type="submit"
          className="px-5 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl text-sm font-medium transition-all flex items-center gap-2 shadow-sm shadow-indigo-100"
        >
          <Send className="w-4 h-4" />
          <span className="hidden sm:inline">Gửi (送信)</span>
        </button>
      </form>
    </div>
  );
};