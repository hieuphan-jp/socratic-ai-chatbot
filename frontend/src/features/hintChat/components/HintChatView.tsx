/**
 * features/hintChat/components/HintChatView.tsx
 *
 * JA: ヒントチャットと思考ツリーのメイン表示コンポーネント。
 * VI: Component hiển thị chính của Hint Chat và Sơ đồ tư duy.
 */
import React, { useState, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { chatApi } from '../api/chatApi';
import type { ChatMessage } from '@/shared/types';

interface HintChatViewProps {
  activeSessionId?: string;
  onSessionCreated?: (newSessionId: string) => void;
}

export const HintChatView: React.FC<HintChatViewProps> = ({
  activeSessionId: propSessionId,
  onSessionCreated,
}) => {
  const queryClient = useQueryClient();
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(propSessionId);
  const [inputText, setInputText] = useState('');
  const [showTree, setShowTree] = useState(true);

  // JA: 親コンポーネントからのアクティブセッションID変更を監視 / VI: Đồng bộ session ID khi props thay đổi
  useEffect(() => {
    if (propSessionId) {
      setCurrentSessionId(propSessionId);
    }
  }, [propSessionId]);

  // JA: 新しいチャットセッションを作成するミューテーション / VI: Mutation tạo phiên chat mới
  const createSessionMutation = useMutation({
    mutationFn: (title?: string) => chatApi.createSession(title || 'Hint Chat Session'),
    onSuccess: (newSession: any) => {
      const newId = newSession.id;
      setCurrentSessionId(newId);
      if (onSessionCreated) {
        onSessionCreated(newId);
      }
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
    },
  });

  // JA: 1. 現在のセッションのメッセージ一覧を取得 / VI: 1. Fetch danh sách tin nhắn của session hiện tại
  const { data: messages = [], isLoading: isLoadingMessages } = useQuery<ChatMessage[]>({
    queryKey: ['chatMessages', currentSessionId],
    queryFn: async () => {
      if (!currentSessionId) return [];
      const res = await chatApi.getMessages(currentSessionId);
      return Array.isArray(res) ? res : (res as any).results || [];
    },
    enabled: !!currentSessionId,
  });

  // JA: 2. React Flow用のノードとエッジを生成（思考ツリー） / VI: 2. Tạo Node & Edge cho Sơ đồ tư duy (React Flow)
  const { nodes, edges } = useMemo(() => {
    const generatedNodes: Node[] = [];
    const generatedEdges: Edge[] = [];

    // JA: ユーザーの質問のみを抽出してステップ化 / VI: Lọc tin nhắn USER làm các bước suy luận
    const userMsgs = messages.filter((msg: any) => {
      const sender = (msg.sender || msg.node_type || msg.sender_type || '').toUpperCase();
      return sender === 'USER' || sender === 'HUMAN';
    });

    if (userMsgs.length === 0) {
      // JA: 初期状態のデモ用ノード / VI: Node demo khi chưa có tin nhắn
      generatedNodes.push(
        {
          id: 'step-1',
          data: { label: 'ステップ1: 問題の分析 / Bước 1: Phân tích bài toán' },
          position: { x: 10, y: 30 },
          style: {
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            padding: '8px',
            fontSize: '11px',
            textAlign: 'center',
            background: '#ffffff',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            width: 160,
          },
        },
        {
          id: 'step-2',
          data: { label: 'ステップ2: 解法の選択 / Bước 2: Chọn phương pháp giải' },
          position: { x: 130, y: 130 },
          style: {
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            padding: '8px',
            fontSize: '11px',
            textAlign: 'center',
            background: '#ffffff',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            width: 160,
          },
        }
      );

      generatedEdges.push({
        id: 'e1-2',
        source: 'step-1',
        target: 'step-2',
        animated: true,
        style: { stroke: '#3b82f6', strokeDasharray: '4', strokeWidth: 1.5 },
      });
    } else {
      userMsgs.forEach((msg: any, idx: number) => {
        const text = msg.message_text || msg.content || '';
        const stepNum = idx + 1;
        const nodeId = msg.id || `node-${stepNum}`;

        generatedNodes.push({
          id: nodeId,
          data: {
            label: `ステップ${stepNum}: ${text.length > 20 ? text.substring(0, 20) + '...' : text} / Bước ${stepNum}`,
          },
          position: { x: 10 + (idx % 2) * 100, y: 30 + idx * 90 },
          style: {
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            padding: '8px',
            fontSize: '11px',
            textAlign: 'center',
            background: '#ffffff',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            width: 160,
          },
        });

        if (idx > 0) {
          const prevNodeId = userMsgs[idx - 1].id || `node-${idx}`;
          generatedEdges.push({
            id: `edge-${idx}`,
            source: prevNodeId,
            target: nodeId,
            animated: true,
            style: { stroke: '#3b82f6', strokeDasharray: '4', strokeWidth: 1.5 },
          });
        }
      });
    }

    return { nodes: generatedNodes, edges: generatedEdges };
  }, [messages]);

  // JA: メッセージ送信ミューテーション / VI: Mutation gửi tin nhắn
  const sendMessageMutation = useMutation({
    mutationFn: ({
      sessionId,
      payload,
    }: {
      sessionId: string;
      payload: { message_text: string; action_type: 'ANSWER' | 'CHANGE_METHOD' };
    }) => chatApi.sendMessage(sessionId, payload),
    onSuccess: (data: any) => {
      // JA: キャッシュを直接更新して即座に画面へ反映 / VI: Cập nhật trực tiếp cache để UI phản hồi tức thì
      queryClient.setQueryData(['chatMessages', currentSessionId], (oldData: ChatMessage[] | undefined) => {
        const newData = oldData ? [...oldData] : [];
        if (data.user_message) newData.push(data.user_message);
        if (data.ai_message) newData.push(data.ai_message);
        return newData;
      });
      queryClient.invalidateQueries({ queryKey: ['chatMessages', currentSessionId] });
    },
  });

  // JA: メッセージ送信ハンドラー / VI: Hàm xử lý gửi tin nhắn
  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    let targetSessionId = currentSessionId;

    // JA: セッションが存在しない場合、自動的に新規作成 / VI: Tự động khởi tạo session nếu chưa có
    if (!targetSessionId) {
      try {
        const newSession: any = await createSessionMutation.mutateAsync('Hint Chat Session');
        targetSessionId = newSession.id;
        setCurrentSessionId(targetSessionId);
        if (onSessionCreated && targetSessionId) {
          onSessionCreated(targetSessionId);
        }
      } catch (err) {
        return;
      }
    }

    if (targetSessionId) {
      sendMessageMutation.mutate({
        sessionId: targetSessionId,
        payload: {
          message_text: text,
          action_type: 'ANSWER',
        },
      });
    }

    setInputText('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(inputText);
  };

  return (
    <div style={{ width: '100%', fontFamily: 'sans-serif', color: '#333', boxSizing: 'border-box' }}>
      
      {/* JA: 思考ツリー表示切り替えボタン / VI: Nút Toggle Ẩn/Hiện Sơ đồ tư duy */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ fontSize: '14px', color: '#666', fontStyle: 'italic' }}>
          Hint Chat Session / Phiên gợi ý
        </div>
        <button
          onClick={() => setShowTree(!showTree)}
          style={{
            padding: '6px 12px',
            fontSize: '12px',
            backgroundColor: '#f3f4f6',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          🌿 思考ツリーを隠す / {showTree ? 'Ẩn cây tư duy' : 'Hiện cây tư duy'}
        </button>
      </div>

      {/* JA: チャット領域と思考ツリー領域のコンテナ / VI: Container chứa Cột Chat & Cột Sơ đồ tư duy */}
      <div style={{ display: 'flex', gap: '16px', width: '100%', marginBottom: '16px' }}>
        
        {/* JA: 左カラム：チャット表示エリア / VI: CỘT TRÁI: Khung hiển thị chat */}
        <div
          style={{
            flex: 1.2,
            height: '460px',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            backgroundColor: '#ffffff',
            padding: '16px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            boxSizing: 'border-box',
          }}
        >
          {isLoadingMessages && <p style={{ fontSize: '12px', color: '#9ca3af' }}>Đang tải...</p>}

          {!isLoadingMessages && messages.length === 0 && (
            <div style={{ fontSize: '13px', color: '#9ca3af', marginTop: '8px' }}>
              質問を送るとヒントが返ってきます /<br />
              Gửi câu hỏi để nhận gợi ý
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {messages.map((msg, index) => {
              const senderRole = (msg as any).sender || (msg as any).node_type || (msg as any).sender_type;
              const isUser = (senderRole || '').toUpperCase() === 'USER';
              const textContent = msg.message_text || (msg as any).content || '';

              return (
                <div
                  key={msg.id || index}
                  style={{
                    display: 'flex',
                    justifyContent: isUser ? 'flex-end' : 'flex-start',
                  }}
                >
                  <div
                    style={{
                      maxWidth: '85%',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      fontSize: '13px',
                      lineHeight: '1.5',
                      backgroundColor: isUser ? '#2563eb' : '#f3f4f6',
                      color: isUser ? '#ffffff' : '#1f2937',
                      border: isUser ? 'none' : '1px solid #e5e7eb',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {textContent}
                  </div>
                </div>
              );
            })}

            {sendMessageMutation.isPending && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div
                  style={{
                    padding: '8px 12px',
                    borderRadius: '8px',
                    fontSize: '13px',
                    backgroundColor: '#f3f4f6',
                    color: '#9ca3af',
                    fontStyle: 'italic',
                  }}
                >
                  Thinking...
                </div>
              </div>
            )}
          </div>
        </div>

        {/* JA: 右カラム：思考プロセスツリー（React Flow） / VI: CỘT PHẢI: Sơ đồ tư duy (React Flow) */}
        {showTree && (
          <div
            style={{
              flex: 1,
              height: '460px',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              backgroundColor: '#ffffff',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              boxSizing: 'border-box',
            }}
          >
            <h3 style={{ fontSize: '15px', fontWeight: 'bold', margin: '0 0 12px 0', color: '#111827' }}>
              🌿 思考プロセス / Tiến trình tư duy
            </h3>

            <div style={{ flex: 1, width: '100%', border: '1px solid #f3f4f6', borderRadius: '6px' }}>
              <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}>
                <Background variant={BackgroundVariant.Dots} gap={12} size={1} color="#d1d5db" />
                <Controls position="bottom-left" showInteractive={false} />
              </ReactFlow>
            </div>
          </div>
        )}
      </div>

      {/* JA: メッセージ入力フォーム / VI: Form nhập liệu tin nhắn */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px', width: '100%', boxSizing: 'border-box' }}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="質問を入力 / Nhập câu hỏi"
          style={{
            flex: 1,
            padding: '10px 14px',
            fontSize: '13px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            outline: 'none',
          }}
          disabled={sendMessageMutation.isPending || createSessionMutation.isPending}
        />
        <button
          type="submit"
          disabled={
            sendMessageMutation.isPending ||
            createSessionMutation.isPending ||
            !inputText.trim()
          }
          style={{
            padding: '10px 24px',
            fontSize: '13px',
            backgroundColor: '#f3f4f6',
            color: '#4b5563',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: '500',
          }}
        >
          {sendMessageMutation.isPending ? '送信中...' : '送信 / Gửi'}
        </button>
      </form>

    </div>
  );
};