import type { ChatMessage, StepNode } from '../types';

export const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 'm1',
    sender: 'ai',
    text: 'Xin chào! Tôi có thể giúp gì cho bài học hôm nay của bạn?\nこんにちは！今日の me の学習をお手伝いします。',
    timestamp: '10:00 AM',
  },
  {
    id: 'm2',
    sender: 'user',
    text: 'Hãy giải thích thuật toán QuickSort và các bước thực hiện.',
    timestamp: '10:01 AM',
  },
  {
    id: 'm3',
    sender: 'ai',
    text: 'QuickSort là thuật toán chia để trị. Tôi đã chia nhỏ quy trình thành cây các bước xử lý (Tree Overview). Bạn có thể mở chế độ xem cây sơ đồ bằng nút ở góc trên bên phải nhé!',
    timestamp: '10:01 AM',
  },
];

export const MOCK_STEP_NODES: StepNode[] = [
  { id: '1', label: 'Bắt đầu: Mảng đầu vào', labelJp: '入力配列', status: 'completed' },
  { id: '2', label: 'Chọn phần tử chốt (Pivot)', labelJp: 'ピボット選択', status: 'completed' },
  { id: '3', label: 'Phân hoạch mảng (Partitioning)', labelJp: '配列の分割', status: 'in_progress' },
  { id: '4', label: 'Đệ quy sắp xếp nửa trái', labelJp: '左部分の再帰ソート', status: 'pending' },
  { id: '5', label: 'Đệ quy sắp xếp nửa phải', labelJp: '右部分の再帰ソート', status: 'pending' },
  { id: '6', label: 'Hoàn thành: Mảng đã sắp xếp', labelJp: 'ソート完了', status: 'pending' },
];