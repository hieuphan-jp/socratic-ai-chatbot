import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { MainTab } from './shared/types/index';
import { Navbar } from './shared/components/Navbar';
import { LearningTreePage } from './pages/LearningTreePage';
import { HintChatPage } from './pages/HintChatPage';

// Khởi tạo QueryClient cho React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // Tránh tự động reload dữ liệu mỗi khi switch tab trình duyệt
      retry: 1,                    // Thử lại 1 lần nếu request thất bại
    },
  },
});

export function App() {
  const [activeTab, setActiveTab] = useState<MainTab>('hintChat');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-slate-50/50 text-slate-800 flex flex-col font-sans">
        <Navbar activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
          {activeTab === 'hintChat' ? <HintChatPage /> : <LearningTreePage />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;