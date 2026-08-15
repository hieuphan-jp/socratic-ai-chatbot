import React from 'react';
import { Search, Sparkles, Tag } from 'lucide-react';
import type { SearchMode } from '../../../shared/types';

interface SearchBarProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  searchMode: SearchMode;
  onModeToggle: () => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  searchTerm,
  onSearchChange,
  searchMode,
  onModeToggle
}) => {
  return (
    <div className="flex flex-col sm:flex-row gap-3 items-center w-full">
      {/* Ô nhập từ khóa */}
      <div className="relative flex-1 w-full">
        <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
          <Search className="w-4 h-4" />
        </div>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={
            searchMode === 'name'
              ? 'Tìm theo tên bài học / chủ đề... (名前で検索)'
              : 'Mô tả ngữ cảnh hoặc câu hỏi bằng AI... (AI文脈検索)'
          }
          className={`w-full pl-10 pr-4 py-2.5 rounded-2xl border text-sm transition-all outline-none ${
            searchMode === 'semantic'
              ? 'border-indigo-200 bg-indigo-50/30 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100'
              : 'border-slate-200 bg-white focus:border-teal-400 focus:ring-2 focus:ring-teal-100'
          }`}
        />
      </div>

      {/* Nút chuyển đổi chế độ Tìm kiếm */}
      <button
        onClick={onModeToggle}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-medium border transition-all whitespace-nowrap shadow-sm ${
          searchMode === 'semantic'
            ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white border-transparent shadow-indigo-100'
            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
        }`}
      >
        {searchMode === 'semantic' ? (
          <>
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Ngữ cảnh (AI検索)</span>
          </>
        ) : (
          <>
            <Tag className="w-3.5 h-3.5 text-slate-400" />
            <span>Theo tên (名前検索)</span>
          </>
        )}
      </button>
    </div>
  );
};