# JA: JSONシリアライズと入力検証 / VI: Tuần tự hóa JSON và kiểm tra đầu vào
from rest_framework import serializers

from .models import ChatMessage, ChatSession


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


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "user", "title", "messages", "created_at"]
        read_only_fields = ["id", "user", "created_at"]


class SendMessageInputSerializer(serializers.Serializer):
    """JA: メッセージ送信リクエストの検証 / VI: Validation request gửi tin nhắn"""

    parent_message_id = serializers.UUIDField(required=False, allow_null=True)
    message_text = serializers.CharField(required=True)
    action_type = serializers.ChoiceField(
        choices=["ANSWER", "REQUEST_CHANGE_METHOD"], default="ANSWER"
    )
