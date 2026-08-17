/**
 * features/hintChat/components/HintChatView.tsx
 *
 * JA: ヒントチャットと思考ツリーのメイン表示コンポーネント。分岐推定の確認機能、ドラッグ＆ドロップ、コピー制限対応。
 * VI: Component hiển thị chính của Hint Chat và Sơ đồ tư duy. Hỗ trợ xác nhận rẽ nhánh, kéo thả Node và chặn copy tin nhắn AI.
 */
import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { chatApi } from '../api/chatApi';
import { useChatSessions } from '../api/useChat';
import { TopicFolderPicker } from './TopicFolderPicker';
import { StepLeafNode } from './StepLeafNode';
import { layoutStepTree } from '../utils/stepTreeLayout';
import { queryKeys } from '@/shared/api/queryKeys';
import { useI18n } from '@/shared/i18n';
import { Button, Notice, ErrorText } from '@/shared/ui';
import type { ChatMessage, GraphData, SendMessagePayload } from '@/shared/types';

// JA: ★コンポーネント外で定義(毎レンダーで新オブジェクトを作るとReact Flowが
//     警告を出すため)。葉の見た目はStepLeafNode側に集約する。
// VI: ★Định nghĩa ngoài component (nếu tạo object mới mỗi lần render, React
//     Flow sẽ cảnh báo). Hình lá gom hết vào StepLeafNode.
const NODE_TYPES = { stepLeaf: StepLeafNode };

interface HintChatViewProps {
  activeSessionId?: string;
  onSessionCreated?: (newSessionId: string) => void;
}

export const HintChatView: React.FC<HintChatViewProps> = ({
  activeSessionId: propSessionId,
  onSessionCreated,
}) => {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(propSessionId);
  const [inputText, setInputText] = useState('');
  const [showTree, setShowTree] = useState(true);

  // JA: ★完了ボタンの二重送信対策(実データの真の防御)。sendMessageMutation.isPending
  //     はTanStack Query内部の非同期な状態更新を経るため、同じJS実行タイミングで
  //     連続して(例: 高速な連打で)クリックされると、2回目の呼び出し時点でもまだ
  //     falseのままで、disabled属性の再描画も間に合わないことを実機検証で確認した
  //     (isPendingやdisabled属性だけを見る対策では、Attempt/知識ノードの二重作成を
  //     防ぎきれなかった)。useRefは同期的にすぐ読み書きできるため、この隙間を作らない。
  // VI: ★Chống gửi 2 lần cho nút hoàn thành (lớp phòng vệ thực sự). sendMessageMutation.isPending
  //     đi qua cập nhật state bất đồng bộ nội bộ của TanStack Query, nên nếu bấm liên
  //     tiếp trong cùng một nhịp JS (vd bấm rất nhanh), lúc gọi lần 2 giá trị vẫn là
  //     false và thuộc tính disabled cũng chưa kịp render lại (đã xác nhận bằng kiểm
  //     thử thực tế — chỉ dựa vào isPending/disabled không chặn được việc tạo trùng
  //     Attempt/knowledge node). useRef đọc/ghi đồng bộ ngay lập tức nên không để lại khe hở này.
  const isSubmittingCompleteRef = useRef(false);

  // React Flow States（思考ツリーのドラッグ操作用）
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // JA: ★knowledge_node未設定のセッションをCOMPLETEする時に、保存先Topicを
  //     選ぶための状態。既にnodeがあるセッションではこのUIは出さない。
  // VI: ★State cho việc chọn Topic để lưu, khi COMPLETE một session chưa gắn
  //     knowledge_node. Session đã có sẵn node thì không hiện UI này.
  const [showSaveAsNode, setShowSaveAsNode] = useState(false);
  const [savedNodeTitle, setSavedNodeTitle] = useState<string | null>(null);

  const { data: sessions } = useChatSessions();
  const currentSession = sessions?.find((s) => String(s.id) === String(currentSessionId));
  const hasKnowledgeNode = Boolean(currentSession?.knowledge_node);

  // JA: 親コンポーネントからのアクティブセッションID変更を監視 / VI: Đồng bộ session ID khi props thay đổi
  useEffect(() => {
    if (propSessionId) {
      setCurrentSessionId(propSessionId);
    }
  }, [propSessionId]);

  // JA: 新しいチャットセッションを作成するミューテーション。
  //     ★titleはここでも固定文字列を埋めない(chatApi.createSessionのコメント参照)。
  // VI: Mutation tạo phiên chat mới.
  //     ★Cũng không điền chuỗi cố định cho title ở đây (xem comment ở chatApi.createSession).
  const createSessionMutation = useMutation({
    mutationFn: (title?: string) => chatApi.createSession(title),
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
    staleTime: 1000 * 60 * 5, // JA: キャッシュを5分間保持し、自動再取得による状態リセットを防止 / VI: Tránh auto refetch ngầm đè state
  });

  // JA: 2. 分岐確定ミューテーション / VI: Mutation xác nhận node cha (rẽ nhánh)
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
      // JA: ★キャッシュキーは必ずvariables.sessionId(この呼び出しに実際に使われたID)を
      //     使う。currentSessionIdはstateのクロージャで、setStateの非同期性により
      //     「セッション新規作成直後の初回送信」では古い値(undefined)を指したままに
      //     なり得る(sendMessageMutationのonSuccessで実際に起きていた不具合と同種の
      //     ため、同じ直し方で揃える)。
      // VI: ★Khóa cache luôn dùng variables.sessionId (ID thực sự dùng cho lần gọi này).
      //     currentSessionId là closure của state, do setState bất đồng bộ nên ở lần gửi
      //     đầu tiên ngay sau khi tạo session mới có thể vẫn trỏ về giá trị cũ (undefined)
      //     (cùng loại lỗi đã xảy ra ở onSuccess của sendMessageMutation, sửa đồng bộ theo).
      queryClient.setQueryData(['chatMessages', variables.sessionId], (oldData: ChatMessage[] | undefined) => {
        if (!oldData) return [];
        return oldData.map((m) => {
          if (String(m.id).toLowerCase() === String(variables.messageId).toLowerCase()) {
            return {
              ...m,
              parent_message_id: variables.parentMessageId,
              parent_confirmed: true,
            };
          }
          return m;
        });
      });
      // JA: 親が変わると木の形と採番も変わるので、サーバーから取り直す。
      // VI: Đổi node cha thì hình dạng cây và cách đánh số cũng đổi, nên lấy lại từ server.
      queryClient.invalidateQueries({
        queryKey: queryKeys.chat.tree(variables.sessionId),
      });
    },
  });

  // JA: 3. 思考ツリーの描画データはサーバーから取得する。
  //     ★以前はここでフロントが「USER発言の時系列の通し番号」を振っていたため、
  //     枝に分かれても番号が連番のままで、番号とノードの位置が食い違っていた。
  //     採番はサーバーが木を辿って行うので、step_label をそのまま表示する。
  // VI: 3. Lấy dữ liệu vẽ cây tư duy từ server.
  //     ★Trước đây frontend tự đánh số tuần tự theo thời gian của phát ngôn USER nên khi
  //     rẽ nhánh, số vẫn chạy liên tiếp và lệch với vị trí node. Việc đánh số do server
  //     duyệt cây đảm nhiệm, nên chỉ cần hiển thị đúng step_label.
  const { data: graph } = useQuery<GraphData>({
    queryKey: queryKeys.chat.tree(currentSessionId ?? ''),
    queryFn: () => chatApi.getGraph(currentSessionId as string),
    enabled: !!currentSessionId,
  });

  useEffect(() => {
    if (!graph) {
      setNodes([]);
      setEdges([]);
      return;
    }

    // JA: ★木は下から上へ育つ(rankdir: 'BT')。配置計算はdagreに任せる
    //     (詳細は utils/stepTreeLayout.ts)。
    // VI: ★Cây mọc từ dưới lên (rankdir: 'BT'). Việc tính vị trí giao cho dagre
    //     (chi tiết ở utils/stepTreeLayout.ts).
    const { nodes: laidOutNodes, edges: laidOutEdges } = layoutStepTree(graph.nodes, graph.edges);
    setNodes(laidOutNodes);
    setEdges(laidOutEdges);
  }, [graph, setNodes, setEdges]);


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
    onSuccess: (data: any, variables) => {
      // JA: ★キャッシュキーはcurrentSessionId(stateのクロージャ)ではなく、必ず
      //     variables.sessionId(このmutate呼び出しに実際に渡されたID)を使う。
      //     新規セッションの1通目送信では、handleSendMessageがsetCurrentSessionId()
      //     の直後に同期的にmutate()を呼ぶため、この時点のsendMessageMutationは
      //     まだ古いレンダー(currentSessionId=undefined)のクロージャを持っている。
      //     以前はここでcurrentSessionIdを直接参照していたため、1通目の返信が
      //     ['chatMessages', undefined]という誰も読まないキーに書き込まれて画面に
      //     反映されず、2通目を送った時のinvalidateQueriesによる再取得で初めて
      //     1通目・2通目がまとめて表示される不具合になっていた。
      // VI: ★Khóa cache luôn dùng variables.sessionId (ID thực sự truyền vào lần gọi
      //     mutate này), không dùng currentSessionId (closure của state). Ở lần gửi
      //     đầu tiên của session mới, handleSendMessage gọi mutate() ngay sau
      //     setCurrentSessionId() một cách đồng bộ, nên sendMessageMutation lúc đó vẫn
      //     giữ closure của lần render cũ (currentSessionId=undefined). Trước đây dùng
      //     trực tiếp currentSessionId ở đây khiến phản hồi của tin đầu tiên bị ghi vào
      //     khóa ['chatMessages', undefined] mà không ai đọc, không hiện lên màn hình;
      //     mãi tới khi gửi tin thứ 2, invalidateQueries mới lấy lại và hiện cả 2 tin cùng lúc.
      const sessionId = variables.sessionId;
      queryClient.setQueryData(['chatMessages', sessionId], (oldData: ChatMessage[] | undefined) => {
        const newData = oldData ? [...oldData] : [];
        if (data.user_message) newData.push(data.user_message);
        if (data.ai_message) newData.push(data.ai_message);
        return newData;
      });
      queryClient.invalidateQueries({ queryKey: ['chatMessages', sessionId] });
      // JA: 新しいステップが増えた可能性があるので思考ツリーを取り直す。
      //     幹/枝の判定と採番はサーバー側で行われるため、ここで再取得しないと反映されない。
      // VI: Có thể vừa thêm bước mới nên lấy lại cây tư duy.
      //     Việc phán đoán thân/nhánh và đánh số nằm ở server nên không lấy lại thì không cập nhật.
      queryClient.invalidateQueries({
        queryKey: queryKeys.chat.tree(sessionId),
      });
      // JA: ★COMPLETEで新しい知識ノードが作られた場合、セッション一覧を
      //     再取得してhasKnowledgeNodeを更新し、完了メッセージを表示する。
      // VI: ★Nếu COMPLETE vừa tạo knowledge node mới, tải lại danh sách
      //     session để cập nhật hasKnowledgeNode và hiện thông báo hoàn tất.
      if (data.knowledge_node_title) {
        setSavedNodeTitle(data.knowledge_node_title);
        setShowSaveAsNode(false);
        queryClient.invalidateQueries({ queryKey: queryKeys.chat.all });
      }
    },
  });

  // JA: 「完了」ボタンのハンドラ。既にノードがあるセッションはそのままCOMPLETE、
  //     ノード未設定ならTopicフォルダ選択パネルを開く。
  // VI: Hàm xử lý nút "Hoàn thành". Session đã có node thì COMPLETE luôn,
  //     chưa có node thì mở panel chọn thư mục Topic.
  const handleCompleteClick = () => {
    // JA: ★二重押下対策(フロント側の真の防御はuseRef、isPendingは補助)。
    if (!currentSessionId || isSubmittingCompleteRef.current) return;
    if (hasKnowledgeNode) {
      // JA: バックエンドは message_text 省略/空文字を許容する(COMPLETEは本文不要)ため、
      //     以前のようにダミー文字列を送って会話履歴を汚す必要はない。
      // VI: Backend chấp nhận message_text bỏ trống (COMPLETE không cần nội dung), nên
      //     không cần gửi chuỗi giả làm bẩn lịch sử hội thoại như trước.
      isSubmittingCompleteRef.current = true;
      sendMessageMutation.mutate(
        {
          sessionId: currentSessionId,
          payload: { message_text: '', action_type: 'COMPLETE', understood: true },
        },
        { onSettled: () => { isSubmittingCompleteRef.current = false; } }
      );
      return;
    }
    setSavedNodeTitle(null);
    setShowSaveAsNode(true);
  };

  // JA: フォルダピッカーで保存先Topicが確定した時のハンドラ。
  //     ★isSubmittingCompleteRef.currentの同期チェック+即時setが唯一の確実な防御。
  //     sendMessageMutation.isPendingはTanStack Query内部の非同期な状態更新を経るため、
  //     同じJS実行タイミングで連打されると2回目の判定時点でもfalseのままになり得る
  //     ことを実機検証(3連続クリック→2つのCOMPLETEリクエストが実際に飛び、
  //     Attemptが2件・SM-2が2回適用される)で確認した。バックエンド側にも
  //     知識ノードの重複を防ぐ条件付きUPDATEはあるが、Attemptは「完了すると
  //     再び新規作成可能になる」設計(複数回の復習を許すため)のため、DB制約
  //     だけでは二重送信そのものを完全には防げない。よって送信自体をここで
  //     確実に1回に絞る。
  // VI: Hàm xử lý khi đã chốt Topic để lưu qua bộ chọn thư mục.
  //     ★Kiểm tra đồng bộ + set ngay isSubmittingCompleteRef.current là lớp phòng vệ
  //     chắc chắn duy nhất. sendMessageMutation.isPending đi qua cập nhật state bất
  //     đồng bộ nội bộ của TanStack Query nên nếu bấm liên tiếp trong cùng nhịp JS,
  //     lúc xét lần 2 vẫn có thể là false (đã xác nhận bằng kiểm thử thực tế: bấm 3
  //     lần liên tiếp → thực sự gửi 2 request COMPLETE, tạo 2 Attempt và áp dụng SM-2
  //     2 lần). Backend có UPDATE điều kiện chống trùng knowledge node, nhưng Attempt
  //     được thiết kế "hoàn thành xong thì có thể tạo mới" (để cho phép ôn tập nhiều
  //     lần), nên riêng ràng buộc DB không chặn được triệt để việc gửi trùng. Vì vậy
  //     phải chặn chắc ngay tại đây, đảm bảo chỉ gửi đúng 1 lần.
  const handleSaveToTopic = (topicId: string) => {
    if (!currentSessionId || isSubmittingCompleteRef.current) return;
    isSubmittingCompleteRef.current = true;
    sendMessageMutation.mutate(
      {
        sessionId: currentSessionId,
        payload: {
          message_text: '',
          action_type: 'COMPLETE',
          understood: true,
          topic_id: topicId,
        },
      },
      { onSettled: () => { isSubmittingCompleteRef.current = false; } }
    );
  };

  // JA: メッセージ送信ハンドラー / VI: Hàm xử lý gửi tin nhắn
  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    let targetSessionId = currentSessionId;

    if (!targetSessionId) {
      try {
        const newSession: any = await createSessionMutation.mutateAsync(undefined);
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

  // JA: ★入力欄をtextarea化したことに伴うキー操作。Enter単体で送信、Shift+Enterは
  //     改行(textareaの既定動作に任せる=preventDefaultしない)。
  //     e.nativeEvent.isComposing のチェックが無いと、日本語などIME変換中に
  //     変換確定のためだけに押したEnterまで送信として拾ってしまい、変換途中の
  //     文章が意図せず送られてしまう。
  // VI: ★Xử lý phím sau khi đổi ô nhập thành textarea. Enter đơn gửi tin nhắn,
  //     Shift+Enter xuống dòng (để mặc định của textarea xử lý, không preventDefault).
  //     Nếu thiếu kiểm tra e.nativeEvent.isComposing, Enter dùng để chốt cụm từ khi
  //     gõ IME (tiếng Nhật...) sẽ bị hiểu nhầm thành gửi, khiến câu đang gõ dở bị
  //     gửi đi ngoài ý muốn.
  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSendMessage(inputText);
    }
  };

  return (
    <div style={{ width: '100%', fontFamily: 'sans-serif', color: '#333', boxSizing: 'border-box' }}>
      
      {/* Nút Toggle Ẩn/Hiện Sơ đồ tư duy */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ fontSize: '14px', color: '#666', fontStyle: 'italic' }}>
          {t('hintChat.session.label')}
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
          🌿 {showTree ? t('hintChat.tree.hide') : t('hintChat.tree.show')}
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
                ? t('hintChat.complete.review')
                : t('hintChat.complete.saveAsNode')}
            </Button>
          )}

          {showSaveAsNode && (
            <div
              style={{
                marginTop: '8px',
                padding: '12px 14px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            >
              <Notice>{t('hintChat.complete.folderPrompt')}</Notice>
              <div style={{ marginTop: '8px' }}>
                <TopicFolderPicker
                  onSelect={handleSaveToTopic}
                  onCancel={() => setShowSaveAsNode(false)}
                  disabled={sendMessageMutation.isPending}
                />
              </div>
              {sendMessageMutation.isError && (
                <ErrorText>{(sendMessageMutation.error as Error).message}</ErrorText>
              )}
            </div>
          )}

          {savedNodeTitle && (
            <Notice>{t('hintChat.complete.saved', { title: savedNodeTitle })}</Notice>
          )}
        </div>
      )}

      {/* JA: チャット領域と思考ツリー領域のコンテナ / VI: Container chứa Cột Chat & Cột Sơ đồ tư duy */}
      <div style={{ display: 'flex', gap: '16px', width: '100%', marginBottom: '16px' }}>
        
        {/* CỘT TRÁI: Khung hiển thị chat */}
        <div
          style={{
            flex: 1.2,
            height: '480px',
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
          {isLoadingMessages && <p style={{ fontSize: '12px', color: '#9ca3af' }}>{t('common.loading')}</p>}

          {!isLoadingMessages && messages.length === 0 && (
            <div style={{ fontSize: '13px', color: '#9ca3af', marginTop: '8px' }}>
              {t('hintChat.emptyHint')}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {messages.map((msg, index) => {
              const senderRole = msg.sender || (msg as any).node_type || (msg as any).sender_type;
              const isUser = (senderRole || '').toUpperCase() === 'USER';
              const textContent = msg.message_text || (msg as any).content || '';

              // JA: 確認UIを出すかどうかはバックエンドが parent_confirmed で決める。
              //     直近ステップへの自然な派生なら確定済み(True)で返るのでバナーは出ず、
              //     過去のステップへ繋ぎ直した場合だけ False で返って確認を促す。
              //     ★以前はフロント側でも「直前のUSER発言か」を判定していたが、相槌は
              //     ステップではないため基準がずれる。判定はサーバーに一本化する。
              // VI: Việc hiện UI xác nhận do backend quyết định qua parent_confirmed.
              //     Phái sinh tự nhiên từ bước gần nhất trả về True nên không hiện banner;
              //     chỉ khi nối về bước cũ hơn mới trả False để hỏi lại.
              //     ★Trước đây frontend cũng tự xét "có phải phát ngôn USER liền trước không",
              //     nhưng câu đệm không phải là bước nên tiêu chí bị lệch. Gom về server.
              const suggestedParentIdStr = String(msg.suggested_parent_id || '').toLowerCase();

              const needsBranchConfirm =
                isUser && !msg.parent_confirmed && Boolean(suggestedParentIdStr);

              const suggestedParentMsg = needsBranchConfirm
                ? messages.find(m => String(m.id).toLowerCase() === suggestedParentIdStr)
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

                        // JA: AIのヒントメッセージはコピー不可、ユーザーメッセージはコピー可能
                        // VI: Chặn copy tin nhắn AI, cho phép copy tin nhắn USER
                        userSelect: isUser ? 'text' : 'none',
                        WebkitUserSelect: isUser ? 'text' : 'none',
                        msUserSelect: isUser ? 'text' : 'none',
                      }}
                      onCopy={(e) => {
                        if (!isUser) {
                          e.preventDefault();
                          alert(t('hintChat.copyBlocked'));
                        }
                      }}
                    >
                      {textContent}
                    </div>
                  </div>

                  {/* Thanh gợi ý rẽ nhánh cho User bấm Confirm */}
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
                        💡{' '}
                        {t('hintChat.branch.suggestion', {
                          quote: suggestedParentMsg
                            ? suggestedParentMsg.message_text.substring(0, 30) + '...'
                            : t('hintChat.branch.oldMessageFallback'),
                        })}
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
                          🌿 {t('hintChat.branch.confirm')}
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            // JA: 「今のままにする」= 現在の親を維持したまま確認済みにする。
                            // VI: "Giữ nguyên" = giữ node cha hiện tại và đánh dấu đã xác nhận.
                            const currentParentId = msg.parent_message_id ?? null;

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
                          {t('hintChat.branch.keep')}
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
                  {t('hintChat.thinking')}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* CỘT PHẢI: Sơ đồ tư duy (React Flow) */}
        {showTree && (
          <div
            style={{
              flex: 1,
              height: '480px',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              backgroundColor: '#ffffff',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              boxSizing: 'border-box',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 'bold', margin: 0, color: '#111827' }}>
                🌿 {t('hintChat.tree.title')}
              </h3>
              <span style={{ fontSize: '11px', color: '#6b7280' }}>✋ {t('hintChat.tree.dragHint')}</span>
            </div>

            <div
              style={{
                flex: 1,
                width: '100%',
                border: '1px solid #f3f4f6',
                borderRadius: '6px',
                // JA: 下端をうっすら土色に。木が根元(下)から生えている雰囲気を出す。
                // VI: Tô nhẹ màu đất ở mép dưới, gợi cảm giác cây mọc từ gốc (phía dưới).
                background: 'linear-gradient(to top, #efe6d8 0%, #f6f2ea 6%, #ffffff 22%)',
              }}
            >
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={NODE_TYPES}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
                nodesDraggable={true}
                proOptions={{ hideAttribution: true }}
              >
                <Background variant={BackgroundVariant.Dots} gap={12} size={1} color="#c9e0b8" />
                <Controls position="bottom-left" showInteractive={true} />
              </ReactFlow>
            </div>
          </div>
        )}
      </div>

      {/* Form nhập liệu tin nhắn */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px', width: '100%', boxSizing: 'border-box' }}>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleInputKeyDown}
          placeholder={t('hintChat.input.placeholder')}
          rows={2}
          style={{
            flex: 1,
            padding: '10px 14px',
            fontSize: '13px',
            fontFamily: 'inherit',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            outline: 'none',
            resize: 'none',
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
          {sendMessageMutation.isPending ? t('hintChat.sending') : t('hintChat.send')}
        </button>
      </form>

    </div>
  );
};