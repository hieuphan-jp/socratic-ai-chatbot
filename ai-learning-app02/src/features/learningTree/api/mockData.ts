import type { ChatSession } from '../types';

export const MOCK_CHAT_SESSIONS: ChatSession[] = [
  {
    id: '1',
    title: 'Giải thuật Sắp xếp Nhanh (QuickSort)',
    titleJp: 'クイックソートアルゴリズム',
    category: 'C++ / Thuật toán',
    updatedAt: '2026-08-14T10:30:00Z',
    previewText: 'Cách phân hoạch Lomuto và tính độ phức tạp O(n log n)...'
  },
  {
    id: '2',
    title: 'Xây dựng Model Phân loại Hình ảnh với PyTorch',
    titleJp: 'PyTorchによる画像分類モデルの構築',
    category: 'AI / Machine Learning',
    updatedAt: '2026-08-13T16:15:00Z',
    previewText: 'Kiến trúc ResNet50 và tinh chỉnh Transfer Learning...'
  },
  {
    id: '3',
    title: 'Kiến trúc Microservices với Docker & K8s',
    titleJp: 'DockerとK8sによるマイクロサービスアーキテクチャ',
    category: 'Cloud & DevOps',
    updatedAt: '2026-08-10T09:00:00Z',
    previewText: 'Cách thiết lập Ingress Controller và Service Mesh...'
  },
  {
    id: '4',
    title: 'Cơ bản về Con trỏ và Bộ nhớ trong C++',
    titleJp: 'C++のポインタとメモリの基礎',
    category: 'C++ / Thuật toán',
    updatedAt: '2026-08-08T14:20:00Z',
    previewText: 'Phân biệt Stack và Heap, hiện tượng Memory Leak...'
  }
];