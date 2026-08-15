import React from 'react';
import { Clock, FolderTree, MessageSquare, ChevronRight } from 'lucide-react';
import type { ChatSession } from '../types';
import type { HistoryFilterMode } from '../../../shared/types';

interface ChatHistoryListProps {
  sessions: ChatSession[];
  filterMode: HistoryFilterMode;
  onFilterChange: (mode: HistoryFilterMode) => void;
  onSelectSession?: (session: ChatSession) => void;
}

export const ChatHistoryList: React.FC<ChatHistoryListProps> = ({
  sessions,
  filterMode,
  onFilterChange,
  onSelectSession
}) => {
  // Gom nhóm theo Category nếu đang ở chế độ 'category'
  const categories = Array.from(new Set(sessions.map((s) => s.category)));

  return (
    <div className="space-y-4">
      {/* Thanh công cụ chọn bộ lọc */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h3 className="font-semibold text-slate-700 text-sm">Lịch sử cuộc hội thoại</h3>
          <p className="text-[11px] text-slate-400">会話履歴リスト</p>
        </div>

        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
          <button
            onClick={() => onFilterChange('time')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filterMode === 'time'
                ? 'bg-white text-slate-800 shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Gần nhất</span>
          </button>

          <button
            onClick={() => onFilterChange('category')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filterMode === 'category'
                ? 'bg-white text-slate-800 shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <FolderTree className="w-3.5 h-3.5" />
            <span>Thể loại</span>
          </button>
        </div>
      </div>

      {/* Hiển thị danh sách theo Filter Mode */}
      {sessions.length === 0 ? (
        <div className="text-center py-8 text-slate-400 text-sm">
          Không tìm thấy lịch sử phù hợp (履歴が見つかりません)
        </div>
      ) : filterMode === 'time' ? (
        // Hiển thị phẳng theo thời gian
        <div className="grid gap-3">
          {sessions.map((session) => (
            <SessionCard key={session.id} session={session} onClick={() => onSelectSession?.(session)} />
          ))}
        </div>
      ) : (
        // Hiển thị gom nhóm theo Category
        <div className="space-y-5">
          {categories.map((cat) => {
            const catSessions = sessions.filter((s) => s.category === cat);
            if (catSessions.length === 0) return null;
            return (
              <div key={cat} className="space-y-2">
                <div className="text-xs font-semibold text-indigo-600 bg-indigo-50/60 px-3 py-1 rounded-lg w-fit border border-indigo-100/50">
                  {cat}
                </div>
                <div className="grid gap-2 pl-2">
                  {catSessions.map((session) => (
                    <SessionCard key={session.id} session={session} onClick={() => onSelectSession?.(session)} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// Component thẻ nhỏ cho mỗi cuộc trò chuyện
const SessionCard: React.FC<{ session: ChatSession; onClick?: () => void }> = ({ session, onClick }) => {
  return (
    <div
      onClick={onClick}
      className="group p-4 bg-white rounded-2xl border border-slate-100 hover:border-teal-200 hover:shadow-md hover:shadow-teal-50/50 transition-all cursor-pointer flex items-center justify-between"
    >
      <div className="flex items-start gap-3">
        <div className="p-2.5 rounded-xl bg-teal-50 text-teal-600 group-hover:bg-teal-100 transition-colors mt-0.5">
          <MessageSquare className="w-4 h-4" />
        </div>
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-slate-800 text-sm group-hover:text-teal-600 transition-colors">
              {session.title}
            </h4>
            {session.titleJp && (
              <span className="text-[10px] text-slate-400 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-100">
                {session.titleJp}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 line-clamp-1">{session.previewText}</p>
          <div className="text-[10px] text-slate-400 pt-1">
            {new Date(session.updatedAt).toLocaleDateString('vi-VN')}
          </div>
        </div>
      </div>
      <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-teal-500 group-hover:translate-x-0.5 transition-all" />
    </div>
  );
};