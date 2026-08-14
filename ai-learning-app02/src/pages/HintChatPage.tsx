import React, { useState, useEffect, useRef } from 'react';
import { HintChatView } from '../features/hintChat/components/HintChatView';
import { StepTreeFlow } from '../features/hintChat/components/StepTreeFlow';
import { 
  useSendMessage, 
  useChatGraph, 
  useCreateChatSession, 
  useChatSessions 
} from '../features/hintChat/api/useChat';
import { Network, Loader2, Plus, AlertCircle } from 'lucide-react';
import type { ChatMessage, StepNode, ChatSession } from '@/shared/types';

export const HintChatPage: React.FC = () => {
  const [isSplitView, setIsSplitView] = useState<boolean>(true);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [initError, setInitError] = useState<string | null>(null);
  
  const isInitialized = useRef<boolean>(false);

  const { data: sessions, isLoading: isSessionsLoading, refetch: refetchSessions } = useChatSessions();
  const createSessionMutation = useCreateChatSession();

  // 1. Khởi tạo Session
  useEffect(() => {
    // Nếu đã chọn session hoặc đang khởi tạo thì bỏ qua
    if (isInitialized.current) return;

    // Nếu đã có danh sách sessions từ server và có ít nhất 1 session -> dùng luôn session mới nhất
    if (sessions && sessions.length > 0) {
      isInitialized.current = true;
      setActiveSessionId(String(sessions[0].id));
      return;
    }

    // Nếu chưa có session nào và danh sách sessions đã load xong -> Tạo session mới
    if (!isSessionsLoading && !sessions?.length) {
      isInitialized.current = true;
      setInitError(null);

      createSessionMutation.mutate(`Session ${new Date().toLocaleTimeString('vi-VN')}`, {
        onSuccess: (data: ChatSession) => {
          if (data?.id) {
            setActiveSessionId(String(data.id));
          } else {
            setInitError('Dữ liệu session trả về không hợp lệ.');
          }
        },
        onError: (err: Error) => {
          console.error("❌ Lỗi tạo session:", err);
          setInitError('Không thể kết nối đến máy chủ để tạo session.');
        }
      });
    }
  }, [sessions, isSessionsLoading]);

  // Tìm session hiện tại
  const currentSession = sessions?.find((s: ChatSession) => String(s.id) === String(activeSessionId));
  const sessionId = activeSessionId || (currentSession ? String(currentSession.id) : '');

  // 2. Sắp xếp tin nhắn
  const dbMessages: ChatMessage[] = (currentSession?.messages || []).map((msg: ChatMessage) => ({
    ...msg,
    sender: msg.sender ? (msg.sender.toLowerCase() as 'user' | 'ai') : 'ai',
    message_text: msg.message_text || msg.text || '',
    text: msg.message_text || msg.text || '',
  }));

  const sortedDbMessages = [...dbMessages].sort((a: ChatMessage, b: ChatMessage) => {
    const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
    const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
    return timeA - timeB;
  });

  const displayedMessages = [...sortedDbMessages, ...localMessages];

  // Graph & Send message hooks
  const { data: graphData, isLoading: isGraphLoading } = useChatGraph(sessionId);
  const sendMessageMutation = useSendMessage();

  const handleSendMessage = (text: string) => {
    if (!text.trim() || !sessionId) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      message_text: text,
      text: text,
      created_at: new Date().toISOString(),
    };
    setLocalMessages((prev) => [...prev, userMsg]);

    sendMessageMutation.mutate(
      {
        sessionId,
        payload: { message: text },
      },
      {
        onSuccess: () => {
          refetchSessions();
          setLocalMessages([]);
        },
        onError: (err: Error) => {
          console.error("❌ Lỗi gửi tin nhắn:", err);
        }
      }
    );
  };

  const handleNewSession = () => {
    setInitError(null);
    createSessionMutation.mutate(`Session ${new Date().toLocaleTimeString('vi-VN')}`, {
      onSuccess: (data: ChatSession) => {
        if (data?.id) {
          setActiveSessionId(String(data.id));
          setLocalMessages([]);
          refetchSessions();
        }
      },
      onError: (err: Error) => {
        console.error("❌ Lỗi tạo session mới:", err);
      }
    });
  };

  const stepNodes: StepNode[] = graphData?.nodes || [];

  // Màn hình báo lỗi nếu khởi tạo thất bại
  if (initError) {
    return (
      <div className="w-full h-screen flex flex-col items-center justify-center gap-3 text-slate-600 text-sm p-4">
        <AlertCircle className="w-8 h-8 text-rose-500" />
        <span className="font-medium text-slate-800">{initError}</span>
        <button
          onClick={() => {
            isInitialized.current = false;
            refetchSessions();
          }}
          className="px-4 py-2 bg-indigo-600 text-white text-xs font-medium rounded-xl hover:bg-indigo-700 transition-all shadow-sm"
        >
          Thử lại
        </button>
      </div>
    );
  }

  // Màn hình Loading
  if (isSessionsLoading || (!sessionId && createSessionMutation.isPending)) {
    return (
      <div className="w-full h-screen flex flex-col items-center justify-center gap-3 text-slate-500 text-sm">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
        <span>Đang khởi tạo phiên trò chuyện mới...</span>
      </div>
    );
  }

  return (
    <div className="w-full h-[calc(100vh-80px)] flex flex-col p-2 gap-3">
      {/* Topbar */}
      <div className="flex justify-between items-center px-2 py-1 bg-white rounded-2xl border border-slate-100 shadow-sm">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-medium">Phiên làm việc:</span>
          <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-lg border border-indigo-100">
            {sessionId ? `ID: ${sessionId}` : 'Khởi tạo...'}
          </span>
        </div>

        <button
          onClick={handleNewSession}
          disabled={createSessionMutation.isPending}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-medium transition-all shadow-sm active:scale-95 disabled:opacity-50"
        >
          {createSessionMutation.isPending ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Plus className="w-3.5 h-3.5" />
          )}
          Tạo Session Mới
        </button>
      </div>

      {/* Layout Main */}
      <div className={`grid gap-4 flex-1 min-h-0 transition-all duration-300 ${isSplitView ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
        <div className="w-full h-full min-h-0 flex flex-col">
          <HintChatView
            messages={displayedMessages}
            onSendMessage={handleSendMessage}
            isSplitView={isSplitView}
            onToggleSplitView={() => setIsSplitView((prev) => !prev)}
          />
        </div>

        {isSplitView && (
          <div className="w-full h-full min-h-[400px] flex flex-col bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden p-3">
            <div className="flex items-center justify-between px-3 py-2 border-b border-slate-100 mb-2">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-indigo-50 text-indigo-600 rounded-xl">
                  <Network className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-semibold text-slate-800">Sơ đồ thực hiện (Step Tree)</h4>
              </div>

              {isGraphLoading ? (
                <div className="flex items-center gap-1.5 text-xs text-indigo-600">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Cập nhật...</span>
                </div>
              ) : (
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
                  {stepNodes.length} bước
                </span>
              )}
            </div>

            <div className="flex-1 w-full h-full min-h-[350px] relative">
              <StepTreeFlow stepNodes={stepNodes} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};