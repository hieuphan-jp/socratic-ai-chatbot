import React from 'react';
import { MessageSquareCode, Network, Sparkles } from 'lucide-react';
import type { MainTab } from '../types';

interface NavbarProps {
  activeTab: MainTab;
  onTabChange: (tab: MainTab) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange }) => {
  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100 px-6 py-3 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand / App Title (Việt - Nhật) */}
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-indigo-50 rounded-xl text-indigo-600">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-semibold text-slate-800 text-base leading-tight">
              AI Tutor <span className="text-xs font-normal text-indigo-500 ml-1">AI学習助手</span>
            </h1>
            <p className="text-[11px] text-slate-400">Hỗ trợ học tập thông minh</p>
          </div>
        </div>

        {/* Navigation Tabs (Thiết kế Pastel Pill) */}
        <nav className="flex items-center gap-1.5 p-1 bg-slate-100/70 rounded-2xl border border-slate-200/50">
          
          {/* Tab 1: Hint Chat */}
          <button
            onClick={() => onTabChange('hintChat')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
              activeTab === 'hintChat'
                ? 'bg-white text-indigo-600 shadow-sm shadow-slate-200/50'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/40'
            }`}
          >
            <MessageSquareCode className="w-4 h-4" />
            <div className="flex flex-col items-start leading-tight">
              <span>Hỏi đáp AI</span>
              <span className="text-[9px] opacity-70">ヒントチャット</span>
            </div>
          </button>

          {/* Tab 2: Learning Tree */}
          <button
            onClick={() => onTabChange('learningTree')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
              activeTab === 'learningTree'
                ? 'bg-white text-teal-600 shadow-sm shadow-slate-200/50'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/40'
            }`}
          >
            <Network className="w-4 h-4" />
            <div className="flex flex-col items-start leading-tight">
              <span>Cây học tập</span>
              <span className="text-[9px] opacity-70">学習ツリー</span>
            </div>
          </button>

        </nav>

        {/* User Profile Badge */}
        <div className="hidden md:flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center font-medium text-xs border border-rose-200">
            H
          </div>
        </div>

      </div>
    </header>
  );
};