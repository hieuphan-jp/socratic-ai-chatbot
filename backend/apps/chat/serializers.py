# JA: JSONシリアライズと入力検証
#     【設計変更2026-08-13】hint_count/completed_atはChatSessionから
#     Attemptへ移動したため、ChatSessionSerializerは現在進行中(または
#     最新)のAttempt情報をcurrent_attemptとして返す。作成時はnode_idを
#     受け取れるようにした(create_chat_session_for_node経由)。
# VI: Tuần tự hóa JSON và kiểm tra đầu vào.
#     【Thay đổi thiết kế 2026-08-13】hint_count/completed_at đã chuyển từ
#     ChatSession sang Attempt, nên ChatSessionSerializer trả về thông
#     tin Attempt hiện tại (hoặc mới nhất) dưới dạng current_attempt. Lúc
#     tạo có thể nhận node_id (qua create_chat_session_for_node).
from rest_framework import serializers

from .models import Attempt, ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    parent_message_id = serializers.UUIDField(
        source="parent_message.id", allow_null=True, required=False
    )

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "session",
            "parent_message_id",
            "sender",
            "message_text",
            "is_hint",
            "node_type",
            "created_at",
        ]
        read_only_fields = ["id", "session", "created_at"]


class AttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attempt
        fields = ["id", "hint_count", "completed_at", "created_at"]
        read_only_fields = fields


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    knowledge_node = serializers.UUIDField(
        source="knowledge_node_id", read_only=True, allow_null=True
    )
    node_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    current_attempt = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "user",
            "title",
            "knowledge_node",
            "node_id",
            "current_attempt",
            "messages",
            "created_at",
        ]
        read_only_fields = ["id", "user", "knowledge_node", "current_attempt", "created_at"]

    def get_current_attempt(self, obj):
        attempt = (
            obj.attempts.filter(completed_at__isnull=True).order_by("-created_at").first()
            or obj.attempts.order_by("-created_at").first()
        )
        return AttemptSerializer(attempt).data if attempt else None


class SendMessageInputSerializer(serializers.Serializer):
    """JA: メッセージ送信リクエストの検証 / VI: Validation request gửi tin nhắn"""

    parent_message_id = serializers.UUIDField(required=False, allow_null=True)
    message_text = serializers.CharField(required=True)
    action_type = serializers.ChoiceField(
        choices=["ANSWER", "REQUEST_CHANGE_METHOD", "HINT", "COMPLETE"], default="ANSWER"
    )
    understood = serializers.BooleanField(required=False, default=False)
    # JA: ★knowledge_node未設定のセッションをCOMPLETEして知識ノードを新規
    #     作成する場合のみ必須。保存先のTopicを指定する。
    # VI: ★Chỉ bắt buộc khi COMPLETE một phiên chat tự do (chưa gắn
    #     knowledge_node) để tạo knowledge node mới. Chỉ định Topic để lưu vào.
    topic_id = serializers.UUIDField(required=False, allow_null=True)
