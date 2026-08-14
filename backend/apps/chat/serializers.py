# JA: JSONシリアライズと入力検証（KNOWLEDGE_NODE・ReviewLog 連携 + 分岐推定確認 対応）
# VI: Tuần tự hóa JSON và kiểm tra đầu vào (Tích hợp KNOWLEDGE_NODE, ReviewLog + xác nhận đoán nhánh)

from rest_framework import serializers
from .models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    # JA: ★親ノードのUUIDを bóc tách して返却するフィールド（read_only=True で安全化）
    # VI: ★Trường bóc tách lấy UUID của parent_message trả về cho Frontend gọn nhẹ
    parent_message_id = serializers.UUIDField(
        source="parent_message.id", allow_null=True, read_only=True
    )
    
    # JA: ★フロントの確認UI用フィールド（分岐推定機能）
    # VI: ★Các field phục vụ UI xác nhận (tính năng đoán nhánh)
    suggested_parent_id = serializers.UUIDField(
        source="suggested_parent.id", allow_null=True, read_only=True
    )
    parent_confidence = serializers.CharField(read_only=True)
    parent_confirmed = serializers.BooleanField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "session",
            "parent_message_id",
            "suggested_parent_id",
            "parent_confidence",
            "parent_confirmed",
            "sender",
            "message_text",
            "is_hint",
            "node_type",
            "created_at",
        ]
        read_only_fields = ["id", "session", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    # JA: リクエスト時に Cây kiến thức の node_id を受け取るためのフィールド
    # VI: Trường nhận node_id từ Cây kiến thức khi Frontend tạo Session
    node_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "user",
            "title",
            "knowledge_node",
            "node_id",
            "hint_count",
            "completed_at",
            "messages",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "knowledge_node",
            "hint_count",
            "completed_at",
            "created_at",
        ]


class SendMessageInputSerializer(serializers.Serializer):
    """
    JA: メッセージ送信リクエストの検証 (HINT / COMPLETE アクションに対応)
        ★parent_message_id は「ユーザーが明示的にこのノードに返信する」場合のみ指定する。
    VI: Validation request gửi tin nhắn (Hỗ trợ các action HINT và COMPLETE)
        ★parent_message_id CHỈ truyền khi user chủ động chọn "trả lời tiếp node này".
    """

    parent_message_id = serializers.UUIDField(required=False, allow_null=True)
    message_text = serializers.CharField(required=False, allow_blank=True, default="")
    action_type = serializers.ChoiceField(
        choices=["ANSWER", "REQUEST_CHANGE_METHOD", "HINT", "COMPLETE"],
        default="ANSWER",
    )


class ConfirmParentInputSerializer(serializers.Serializer):
    """JA: 親ノード確認/変更リクエストの検証 / VI: Validation request xác nhận/đổi node cha"""

    message_id = serializers.UUIDField(required=True)
    parent_message_id = serializers.UUIDField(required=False, allow_null=True)