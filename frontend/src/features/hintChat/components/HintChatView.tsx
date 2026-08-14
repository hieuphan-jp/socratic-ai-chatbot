/**
 * features/hintChat/components/HintChatView.tsx
 *
 * JA: ヒントチャットと思考ツリーのメイン表示コンポーネント。分岐推定の確認機能対応。
 * VI: Component hiển thị chính của Hint Chat và Sơ đồ tư duy. Hỗ trợ xác nhận rẽ nhánh chính xác.
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
import { useChatSessions, useTopics, useCreateTopic } from '../api/useChat';
import { queryKeys } from '@/shared/api/queryKeys';
import { Button, Input, Notice, ErrorText } from '@/shared/ui';
import type { ChatMessage, SendMessagePayload } from '@/shared/types';

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

  // JA: ★knowledge_node未設定のセッションをCOMPLETEする時に、保存先Topicを
  //     選ぶための状態。既にnodeがあるセッションではこのUIは出さない。
  // VI: ★State cho việc chọn Topic để lưu, khi COMPLETE một session chưa gắn
  //     knowledge_node. Session đã có sẵn node thì không hiện UI này.
  const [showSaveAsNode, setShowSaveAsNode] = useState(false);
  const [selectedTopicId, setSelectedTopicId] = useState('');
  const [newTopicName, setNewTopicName] = useState('');
  const [savedNodeTitle, setSavedNodeTitle] = useState<string | null>(null);

  const { data: sessions } = useChatSessions();
  const currentSession = sessions?.find((s) => String(s.id) === String(currentSessionId));
  const hasKnowledgeNode = Boolean(currentSession?.knowledge_node);

  const { data: topics = [], isPending: isLoadingTopics } = useTopics();
  const createTopicMutation = useCreateTopic();

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

  // JA: 2. 分岐確定ミューテーション (invalidateQueries を除去し、State/Cache を固定)
  // VI: Mutation xác nhận node cha - Giữ nguyên Cache vừa cập nhật, tránh bị API GET fetch đè lại dữ liệu cũ
  const confirmParentMutation = useMutation({
    mutationFn: ({
      sessionId,
      messageId,
      parentMessageId,
    }: {
      sessionId: string;
      messageId: string;
      parentMessageId: string | null;
    }) => chatApi.confirmParent(sessionId, { message_id: messageId, parent_message_id: parentMessageId }),
    onSuccess: (_updatedMsg: any, variables) => {
      // Cập nhật trực tiếp cache local để cố định cấu trúc nhánh mới mà không bị fetch lại làm giật
      queryClient.setQueryData(['chatMessages', currentSessionId], (oldData: ChatMessage[] | undefined) => {
        if (!oldData) return [];
        return oldData.map((m) => {
          if (String(m.id) === String(variables.messageId)) {
            return {
              ...m,
              parent_message: variables.parentMessageId as any,
              parent_confirmed: true,
            };
          }
          return m;
        });
      });
    },
  });

  // JA: 3. React Flow用のノードとエッジを生成（思考ツリー・分岐構造対応）
  // VI: 3. Tạo Node & Edge cho Sơ đồ tư duy (React Flow) - Xử lý bóc tách ID parent_message chính xác
  const { nodes, edges } = useMemo(() => {
    const generatedNodes: Node[] = [];
    const generatedEdges: Edge[] = [];

    // JA: ユーザーの質問メッセージを抽出 / VI: Lọc tin nhắn USER
    const userMsgs = messages.filter((msg: ChatMessage) => {
      const sender = (msg.sender || msg.node_type || (msg as any).sender_type || '').toUpperCase();
      return sender === 'USER' || sender === 'HUMAN';
    });

    if (userMsgs.length === 0) {
      // Demo node khi chưa có tin nhắn
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
      // Map lưu vị trí index của các node USER để tra cứu vị trí
      const nodeIndexMap: Record<string, number> = {};
      userMsgs.forEach((msg, idx) => {
        if (msg.id) nodeIndexMap[String(msg.id)] = idx;
      });

      userMsgs.forEach((msg: ChatMessage, idx: number) => {
        const text = msg.message_text || '';
        const stepNum = idx + 1;
        const nodeId = String(msg.id || `node-${stepNum}`);

        // Bóc tách parentId chuẩn kể cả khi parent_message là Object hay String
        const rawParent = msg.parent_message;
        let parentId: string | null = null;
        if (typeof rawParent === 'object' && rawParent !== null) {
          parentId = String((rawParent as any).id);
        } else if (rawParent) {
          parentId = String(rawParent);
        }

        // Kiểm tra xem node này có rẽ nhánh từ một node cũ (không phải node ngay liền trước) hay không
        const isBranching = Boolean(
          parentId && 
          nodeIndexMap[parentId] !== undefined && 
          nodeIndexMap[parentId] < idx - 1
        );

        // Tọa độ hiển thị: nếu là nhánh rẽ thì đẩy lệch sang phải (x = 190) để tách nhánh rõ ràng
        const posX = isBranching ? 190 : 10;
        const posY = 30 + idx * 85;

        generatedNodes.push({
          id: nodeId,
          data: {
            label: `ステップ${stepNum}: ${text.length > 18 ? text.substring(0, 18) + '...' : text} / Bước ${stepNum}`,
          },
          position: { x: posX, y: posY },
          style: {
            border: isBranching ? '2px solid #2563eb' : '1px solid #d1d5db',
            borderRadius: '6px',
            padding: '8px',
            fontSize: '11px',
            textAlign: 'center',
            background: isBranching ? '#eff6ff' : '#ffffff',
            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            width: 160,
          },
        });

        // Tạo Edge liên kết
        if (idx > 0) {
          // Nếu parentId hợp lệ và tồn tại trong cây thì nối vào parentId đó, ngược lại mới nối vào câu ngay trước
          const actualParentId = (parentId && nodeIndexMap[parentId] !== undefined)
            ? parentId 
            : String(userMsgs[idx - 1].id);

          if (actualParentId) {
            generatedEdges.push({
              id: `edge-${idx}`,
              source: actualParentId,
              target: nodeId,
              animated: true,
              style: { 
                stroke: isBranching ? '#2563eb' : '#3b82f6', 
                strokeDasharray: isBranching ? '0' : '4', 
                strokeWidth: isBranching ? 2 : 1.5 
              },
            });
          }
        }
      });
    }

    return { nodes: generatedNodes, edges: generatedEdges };
  }, [messages]);

  // JA: メッセージ送信ミューテーション（ANSWER/HINT/COMPLETE 共通）
  // VI: Mutation gửi tin nhắn (dùng chung cho ANSWER/HINT/COMPLETE)
  const sendMessageMutation = useMutation({
    mutationFn: ({
      sessionId,
      payload,
    }: {
      sessionId: string;
      payload: SendMessagePayload;
    }) => chatApi.sendMessage(sessionId, payload),
    onSuccess: (data: any) => {
      queryClient.setQueryData(['chatMessages', currentSessionId], (oldData: ChatMessage[] | undefined) => {
        const newData = oldData ? [...oldData] : [];
        if (data.user_message) newData.push(data.user_message);
        if (data.ai_message) newData.push(data.ai_message);
        return newData;
      });
      queryClient.invalidateQueries({ queryKey: ['chatMessages', currentSessionId] });
      // JA: ★COMPLETEで新しい知識ノードが作られた場合、セッション一覧を
      //     再取得してhasKnowledgeNodeを更新し、完了メッセージを表示する。
      // VI: ★Nếu COMPLETE vừa tạo knowledge node mới, tải lại danh sách
      //     session để cập nhật hasKnowledgeNode và hiện thông báo hoàn tất.
      if (data.knowledge_node_title) {
        setSavedNodeTitle(data.knowledge_node_title);
        setShowSaveAsNode(false);
        setSelectedTopicId('');
        setNewTopicName('');
        queryClient.invalidateQueries({ queryKey: queryKeys.chat.all });
      }
    },
  });

  // JA: 「完了」ボタンのハンドラ。既にノードがあるセッションはそのままCOMPLETE、
  //     ノード未設定ならTopic選択パネルを開く。
  // VI: Hàm xử lý nút "Hoàn thành". Session đã có node thì COMPLETE luôn,
  //     chưa có node thì mở panel chọn Topic.
  const handleCompleteClick = () => {
    if (!currentSessionId) return;
    if (hasKnowledgeNode) {
      sendMessageMutation.mutate({
        sessionId: currentSessionId,
        payload: { message_text: '[COMPLETE]', action_type: 'COMPLETE', understood: true },
      });
      return;
    }
    setSavedNodeTitle(null);
    setShowSaveAsNode(true);
  };

  // JA: Topic選択パネルの確定ハンドラ。新規Topic名が入力されていれば先に作成する。
  // VI: Hàm xử lý xác nhận panel chọn Topic. Nếu có nhập tên Topic mới thì tạo trước.
  const handleConfirmSaveAsNode = async () => {
    if (!currentSessionId) return;
    let topicId = selectedTopicId;
    if (!topicId && newTopicName.trim()) {
      const created = await createTopicMutation.mutateAsync(newTopicName.trim());
      topicId = created.id;
    }
    if (!topicId) return;
    sendMessageMutation.mutate({
      sessionId: currentSessionId,
      payload: {
        message_text: '[COMPLETE]',
        action_type: 'COMPLETE',
        understood: true,
        topic_id: topicId,
      },
    });
  };

  // JA: メッセージ送信ハンドラー / VI: Hàm xử lý gửi tin nhắn
  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    let targetSessionId = currentSessionId;

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

      {/* JA: ★学んだ内容を知識ノードとして保存する導線 / VI: ★Luồng lưu nội dung đã học thành knowledge node */}
      {currentSessionId && (
        <div style={{ marginBottom: '12px' }}>
          {!showSaveAsNode && (
            <Button
              type="button"
              onClick={handleCompleteClick}
              disabled={sendMessageMutation.isPending}
            >
              {hasKnowledgeNode
                ? '復習を完了する / Hoàn thành ôn tập'
                : '学習を完了して知識ノードとして保存 / Hoàn thành và lưu thành knowledge node'}
            </Button>
          )}

          {showSaveAsNode && (
            <div
              style={{
                marginTop: '8px',
                padding: '12px 14px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                display: 'grid',
                gap: '8px',
              }}
            >
              <Notice>
                保存先のTopicを選ぶか、新しいTopic名を入力してください /
                Chọn Topic để lưu, hoặc nhập tên Topic mới
              </Notice>

              {isLoadingTopics ? (
                <Notice>読み込み中… / Đang tải…</Notice>
              ) : topics.length > 0 ? (
                <select
                  value={selectedTopicId}
                  onChange={(e) => {
                    setSelectedTopicId(e.target.value);
                    if (e.target.value) setNewTopicName('');
                  }}
                  style={{ padding: '8px 10px', borderRadius: 6, border: '1px solid #ccc' }}
                >
                  <option value="">既存のTopicから選択 / Chọn Topic có sẵn</option>
                  {topics.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              ) : null}

              <Input
                placeholder="新しいTopic名 / Tên Topic mới"
                value={newTopicName}
                onChange={(e) => {
                  setNewTopicName(e.target.value);
                  if (e.target.value) setSelectedTopicId('');
                }}
              />

              {sendMessageMutation.isError && (
                <ErrorText>{(sendMessageMutation.error as Error).message}</ErrorText>
              )}

              <div style={{ display: 'flex', gap: '8px' }}>
                <Button
                  type="button"
                  onClick={handleConfirmSaveAsNode}
                  disabled={
                    (!selectedTopicId && !newTopicName.trim()) ||
                    sendMessageMutation.isPending ||
                    createTopicMutation.isPending
                  }
                >
                  保存する / Lưu
                </Button>
                <Button type="button" onClick={() => setShowSaveAsNode(false)}>
                  キャンセル / Hủy
                </Button>
              </div>
            </div>
          )}

          {savedNodeTitle && (
            <Notice>
              知識ノード「{savedNodeTitle}」として保存しました / Đã lưu thành knowledge node "
              {savedNodeTitle}"
            </Notice>
          )}
        </div>
      )}

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
              const senderRole = msg.sender || (msg as any).node_type || (msg as any).sender_type;
              const isUser = (senderRole || '').toUpperCase() === 'USER';
              const textContent = msg.message_text || (msg as any).content || '';

              // Lấy câu hỏi USER đứng ngay phía trước
              const userMsgsBefore = messages
                .slice(0, index)
                .filter(m => ((m.sender || (m as any).sender_type || '').toUpperCase() === 'USER'));
              
              const immediatePrevUserMsg = userMsgsBefore.length > 0 ? userMsgsBefore[userMsgsBefore.length - 1] : null;

              // Bóc tách suggested_parent_id chuẩn kiểu dữ liệu
              const rawSuggestedParent = msg.suggested_parent_id;
              const suggestedParentIdStr = typeof rawSuggestedParent === 'object' && rawSuggestedParent !== null
                ? (rawSuggestedParent as any).id
                : rawSuggestedParent;

              // CHỈ HIỂN THỊ BANNER CONFIRM NẾU:
              // 1. Là tin nhắn USER chưa confirm (parent_confirmed === false)
              // 2. Có suggested_parent_id
              // 3. suggested_parent_id KHÁC với câu hỏi USER ngay liền trước (thực sự đang rẽ nhánh về câu cũ)
              const needsBranchConfirm = 
                isUser && 
                !msg.parent_confirmed && 
                Boolean(suggestedParentIdStr) && 
                suggestedParentIdStr !== (immediatePrevUserMsg ? String(immediatePrevUserMsg.id) : null);

              const suggestedParentMsg = needsBranchConfirm 
                ? messages.find(m => String(m.id) === String(suggestedParentIdStr)) 
                : null;

              return (
                <React.Fragment key={msg.id || index}>
                  <div
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

                  {/* JA: 分岐提案の確認バー (Confirm Banner) / VI: Thanh gợi ý rẽ nhánh cho User bấm Confirm */}
                  {needsBranchConfirm && currentSessionId && (
                    <div
                      style={{
                        margin: '4px 0 8px auto',
                        maxWidth: '85%',
                        backgroundColor: '#eff6ff',
                        border: '1px solid #93c5fd',
                        borderRadius: '6px',
                        padding: '8px 12px',
                        fontSize: '12px',
                        color: '#1e40af',
                      }}
                    >
                      <div style={{ marginBottom: '6px', fontWeight: '500' }}>
                        💡 AI Gợi ý: Câu hỏi này có vẻ liên quan đến câu hỏi trước đó:{' '}
                        <i>"{suggestedParentMsg ? suggestedParentMsg.message_text.substring(0, 30) + '...' : 'Câu thoại cũ'}"</i>.
                        Bạn có muốn rẽ nhánh cây tư duy từ câu đó không?
                      </div>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        <button
                          type="button"
                          onClick={() => {
                            confirmParentMutation.mutate({
                              sessionId: currentSessionId,
                              messageId: msg.id,
                              parentMessageId: suggestedParentIdStr || null,
                            });
                          }}
                          disabled={confirmParentMutation.isPending}
                          style={{
                            padding: '4px 10px',
                            fontSize: '11px',
                            backgroundColor: '#2563eb',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontWeight: '500',
                          }}
                        >
                          🌿 Đồng ý rẽ nhánh
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            // Lấy parent_message hiện tại để giữ nguyên
                            const rawMsgParent = msg.parent_message;
                            const currentParentId = typeof rawMsgParent === 'object' && rawMsgParent !== null
                              ? (rawMsgParent as any).id
                              : rawMsgParent;

                            confirmParentMutation.mutate({
                              sessionId: currentSessionId,
                              messageId: msg.id,
                              parentMessageId: currentParentId || null,
                            });
                          }}
                          disabled={confirmParentMutation.isPending}
                          style={{
                            padding: '4px 10px',
                            fontSize: '11px',
                            backgroundColor: '#ffffff',
                            color: '#4b5563',
                            border: '1px solid #d1d5db',
                            borderRadius: '4px',
                            cursor: 'pointer',
                          }}
                        >
                          Giữ nguyên
                        </button>
                      </div>
                    </div>
                  )}
                </React.Fragment>
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