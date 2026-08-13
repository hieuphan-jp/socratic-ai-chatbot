# JA: チャット機能と復習機能のデータモデル定義
# VI: Định nghĩa Data Model cho tính năng Chat và Spaced Repetition (Reviews)

from django.db import models
from django.conf import settings
from django.utils import timezone


class ChatSession(models.Model):
    """
    JA: チャットセッション（ERDの ATTEMPT テーブルに相当）
        ユーザーの学習試行データを保持し、KNOWLEDGE_NODE と紐付けられる。
    VI: Phiên chat (Tương đương với bảng ATTEMPT trong ERD)
        Lưu trữ dữ liệu thử sức/học tập của người dùng và liên kết với KNOWLEDGE_NODE.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        help_text="JA: ユーザーID / VI: ID người dùng"
    )
    title = models.CharField(
        max_length=255, 
        default="New Session",
        help_text="JA: セッションタイト / VI: Tiêu đề phiên chat"
    )
    
    # JA: KNOWLEDGE_NODE への外部キー（1:N の関係）
    # VI: Khoá ngoại nối tới KNOWLEDGE_NODE (Mối quan hệ 1:N)
    knowledge_node = models.ForeignKey(
        'reviews.KnowledgeNode', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='attempts',
        help_text="JA: 関連する知識ノード / VI: Node kiến thức liên quan"
    )
    
    # JA: 間隔復習 (Spaced Repetition) 用のフィールド (ATTEMPT 由来)
    # VI: Các trường phục vụ tính năng lặp lại ngắt quãng (Bảng ATTEMPT)
    hint_count = models.IntegerField(
        default=0,
        help_text="JA: ヒント要求回数 / VI: Số lần xin gợi ý"
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="JA: 学習完了日時 / VI: Thời gian hoàn thành phiên học"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="JA: 作成日時 / VI: Thời gian tạo"
    )

    class Meta:
        db_table = 'chat_sessions'
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'

    def mark_completed(self):
        """
        JA: セッションを完了状態としてマークする
        VI: Đánh dấu phiên học đã hoàn thành
        """
        self.completed_at = timezone.now()
        self.save(update_fields=['completed_at'])