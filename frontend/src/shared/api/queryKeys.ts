/**
 * shared/api/queryKeys.ts
 *
 * JA: ★TanStack Query のクエリキーを一元管理する。キーを文字列で散らすと
 *     無効化(invalidate)の対象がズレてバグる。ここで定義したものだけを使うこと。
 *     新しい feature はここにキーを1グループ追加してから使う。
 * VI: ★Quản lý tập trung query key của TanStack Query. Nếu rải key dạng chuỗi khắp nơi,
 *     đối tượng invalidate sẽ lệch và gây bug. Chỉ dùng key định nghĩa ở đây.
 *     Feature mới thêm 1 nhóm key vào đây trước khi dùng.
 */
export const queryKeys = {
  // JA: 現在ユーザー。VI: User hiện tại.
  me: ['me'] as const,

  // JA: 各機能のキーはここにグループを追加する。例（CONVENTIONS.md §5 参照）:
  //     items: { all: ['items'] as const, list: () => [...queryKeys.items.all, 'list'] as const },
  // VI: Thêm nhóm key của từng tính năng ở đây. Ví dụ (xem CONVENTIONS.md §5):
  //     items: { all: ['items'] as const, list: () => [...queryKeys.items.all, 'list'] as const },
  // JA: チャット機能のクエリキー。 VI: Key cho tính năng Chat và Cây tư duy.
  chat: {
    all: ['chat'] as const,
    session: (attemptId: string) => [...queryKeys.chat.all, 'session', attemptId] as const,
    messages: (sessionId: string) => [...queryKeys.chat.all, 'messages', sessionId] as const,
    tree: (sessionId: string) => [...queryKeys.chat.all, 'tree', sessionId] as const,
  },
  // JA: 学習内容ツリーのクエリキー。 VI: Key cho tính năng Cây nội dung đã học.
  learningTree: {
    all: ['learningTree'] as const,
    list: () => [...queryKeys.learningTree.all, 'list'] as const,
    node: (nodeId: string) => [...queryKeys.learningTree.all, 'node', nodeId] as const,
  },
  // JA: 復習スケジュール(学習木の葉を塗るための定着度・復習タイミング)のクエリキー。
  // VI: Key cho lịch ôn tập (độ ghi nhớ, thời điểm ôn tập để tô lá của cây học tập).
  reviews: {
    all: ['reviews'] as const,
    schedules: () => [...queryKeys.reviews.all, 'schedules'] as const,
    // JA: 復習予定日を過ぎた葉だけの一覧(「今日の復習」用)。 VI: Danh sách lá đã quá hạn ôn (dùng cho "Ôn tập hôm nay").
    due: () => [...queryKeys.reviews.all, 'due'] as const,
  },
  // JA: Topic(学習木のカテゴリ)のクエリキー。list()はルート直下、children(id)は
  //     指定Topic直下(フォルダのドリルダウン)。
  // VI: Key cho Topic (danh mục của cây học tập). list() là gốc, children(id) là
  //     trực thuộc Topic chỉ định (duyệt sâu dần theo thư mục).
  topics: {
    all: ['topics'] as const,
    list: () => [...queryKeys.topics.all, 'list'] as const,
    children: (topicId: string) => [...queryKeys.topics.all, 'children', topicId] as const,
  },
}
