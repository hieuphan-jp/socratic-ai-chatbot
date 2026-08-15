import React, { useState } from 'react';
import { SearchBar } from '../features/learningTree/components/SearchBar';
import { ChatHistoryList } from '../features/learningTree/components/ChatHistoryList';
import { MOCK_CHAT_SESSIONS } from '../features/learningTree/api/mockData';
import type { SearchMode, HistoryFilterMode } from '../shared/types';

export const LearningTreePage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchMode, setSearchMode] = useState<SearchMode>('name');
  const [filterMode, setFilterMode] = useState<HistoryFilterMode>('time');

  // Lọc dữ liệu đơn giản theo từ khóa
  const filteredSessions = MOCK_CHAT_SESSIONS.filter((s) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      s.title.toLowerCase().includes(term) ||
      (s.titleJp && s.titleJp.toLowerCase().includes(term)) ||
      s.category.toLowerCase().includes(term)
    );
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header trang */}
      <div className="bg-gradient-to-r from-teal-50/60 via-indigo-50/40 to-slate-50 p-6 rounded-3xl border border-slate-100">
        <h2 className="text-lg font-semibold text-slate-800">Cây Học Tập & Lịch Sử Trò Chuyện</h2>
        <p className="text-xs text-slate-500 mt-0.5">学習ツリーとチャット履歴</p>
      </div>

      {/* Thanh tìm kiếm */}
      <SearchBar
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        searchMode={searchMode}
        onModeToggle={() => setSearchMode((prev) => (prev === 'name' ? 'semantic' : 'name'))}
      />

      {/* Danh sách Lịch sử Chat */}
      <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-sm">
        <ChatHistoryList
          sessions={filteredSessions}
          filterMode={filterMode}
          onFilterChange={setFilterMode}
        />
      </div>
    </div>
  );
};