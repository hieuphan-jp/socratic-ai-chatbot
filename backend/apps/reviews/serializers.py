"""
JA: ReviewSchedule のJSON表現。保存処理や業務判断はここに書かない
    (services.py の責務)。
    【設計変更 2026-08-15】学習木の葉の色分けは、フロントが
    GET /api/learning-tree/ と GET /api/review-schedules/ を node_id で
    突き合わせて行う。そのためこのシリアライザは「葉1枚を塗るのに必要な
    材料」を過不足なく返す係になる:
      ・mastery_level  … 緑の濃さ(0〜MASTERY_MAX_LEVEL)
      ・is_due         … 復習タイミングを示す別UI用のフラグ
      ・chat_session_id… その葉から過去のチャットに戻るための行き先
    ※ 一覧に出てこないノード(=ReviewScheduleが無い手動作成ノード)は
      「未学習」として扱ってよい。
    ※ 木全体の定着率(%)は「is_due が false の葉 ÷ 木の葉の総数」で、
      フロント側で算出できるため専用APIは設けない。
VI: Biểu diễn JSON của ReviewSchedule. Không viết xử lý lưu hay phán đoán
    nghiệp vụ ở đây (đó là trách nhiệm của services.py).
    【Thay đổi thiết kế 2026-08-15】Việc tô màu lá của cây học tập do frontend
    thực hiện, bằng cách ghép GET /api/learning-tree/ với
    GET /api/review-schedules/ theo node_id. Vì vậy serializer này chịu trách
    nhiệm trả đủ "nguyên liệu để tô 1 chiếc lá":
      ・mastery_level  … độ đậm màu xanh (0 đến MASTERY_MAX_LEVEL)
      ・is_due         … cờ cho UI riêng báo đã tới lượt ôn tập
      ・chat_session_id… đích để quay lại cuộc trò chuyện cũ từ chiếc lá đó
    ※ Node không xuất hiện trong danh sách (= node tạo tay, chưa có
      ReviewSchedule) thì coi như "chưa học".
    ※ Tỉ lệ ghi nhớ của cả cây (%) = "số lá có is_due = false ÷ tổng số lá",
      frontend tự tính được nên không thêm API riêng.
"""

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from .models import ReviewSchedule


class ReviewScheduleSerializer(serializers.ModelSerializer):
    node_id = serializers.UUIDField(source="node.id", read_only=True)
    node_title = serializers.CharField(source="node.title", read_only=True)
    topic_id = serializers.UUIDField(source="node.topic_id", read_only=True)
    mastery_level = serializers.IntegerField(read_only=True)
    mastery_max_level = serializers.IntegerField(source="MASTERY_MAX_LEVEL", read_only=True)
    is_due = serializers.BooleanField(read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    chat_session_id = serializers.SerializerMethodField()

    class Meta:
        model = ReviewSchedule
        fields = [
            "id",
            "node_id",
            "node_title",
            "topic_id",
            "interval_days",
            "next_review_at",
            "learned_count",
            "mastery_level",
            "mastery_max_level",
            "is_due",
            "days_overdue",
            "chat_session_id",
        ]
        read_only_fields = fields

    def get_chat_session_id(self, obj):
        try:
            return obj.node.chat_session.id
        except ObjectDoesNotExist:
            return None
