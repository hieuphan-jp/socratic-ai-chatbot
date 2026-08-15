/**
 * features/hintChat/api/useChat.ts
 *
 * JA: メッセージ送信フック (楽観的更新・日英コメント対応)
 * VI: Hook gửi tin nhắn (Cập nhật lạc quan Optimistic Update & Comment Việt - Nhật)
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from './chatApi'
import type { ChatMessage } from '@/shared/types'

export const useSendMessage = (defaultSessionId?: string) => {
  const queryClient = useQueryClient()

  return useMutation({
    // JA: メッセージ送信API呼出 / VI: Gọi API gửi tin nhắn
    mutationFn: ({
      sessionId,
      payload,
    }: {
      sessionId: string
      payload: { message_text: string; action_type?: string }
    }) => chatApi.sendMessage(sessionId, payload),

    // ⚡ ON MUTATE: 送信ボタン押下直後に実行 (UIを即時更新)
    // ⚡ ON MUTATE: Chạy NGAY LẬP TỨC khi bấm gửi (Cập nhật UI ngay lập tức)
    onMutate: async ({ sessionId, payload }) => {
      // JA: 使用するセッションID（引数またはデフォルト値）
      // VI: Session ID được sử dụng (Tham số truyền vào hoặc giá trị mặc định)
      const targetSessionId = sessionId || defaultSessionId
      if (!targetSessionId) return

      const queryKey = ['chatMessages', targetSessionId]

      // JA: 進行中のリクエストをキャンセルしてキャッシュの競合を防ぐ
      // VI: Hủy các request đang chạy dở để tránh xung đột cache
      await queryClient.cancelQueries({ queryKey })

      // JA: ロールバック用の以前のメッセージ一覧を保存
      // VI: Lưu lại danh sách tin nhắn cũ phòng trường hợp cần rollback
      const previousMessages = queryClient.getQueryData<ChatMessage[]>(queryKey) || []

      // JA: 即時表示用の仮ユーザーメッセージを作成
      // VI: Tạo tin nhắn người dùng tạm thời để hiển thị ngay lập tức
      const optimisticUserMsg: ChatMessage = {
        id: `temp-${Date.now()}`,
        message_text: payload.message_text,
        sender: 'USER',
        node_type: 'USER',
        created_at: new Date().toISOString(),
      }

      // JA: キャッシュを更新して画面に即座に反映
      // VI: Cập nhật cache để hiển thị lên màn hình ngay lập tức
      queryClient.setQueryData<ChatMessage[]>(queryKey, (old = []) => [
        ...old,
        optimisticUserMsg,
      ])

      return { previousMessages, queryKey }
    },

    // ❌ ON ERROR: 送信失敗時の処理 (以前の状態に復元)
    // ❌ ON ERROR: Xử lý khi gửi thất bại (Rollback về trạng thái cũ)
    onError: (_err, _variables, context) => {
      if (context?.queryKey && context?.previousMessages) {
        queryClient.setQueryData(context.queryKey, context.previousMessages)
      }
      alert('JA: 送信に失敗しました。 / VI: Gửi tin nhắn thất bại.')
    },

    // 🔄 ON SETTLED: 通信完了後にサーバーから最新データを再取得
    // 🔄 ON SETTLED: Sau khi hoàn tất, refetch lại để lấy ID thật từ server
    onSettled: (_data, _error, variables) => {
      const targetSessionId = variables.sessionId || defaultSessionId
      if (targetSessionId) {
        queryClient.invalidateQueries({
          queryKey: ['chatMessages', targetSessionId],
        })
      }
    },
  })
}