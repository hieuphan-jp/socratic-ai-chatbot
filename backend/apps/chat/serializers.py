# JA: JSONシリアライズと入力検証
#     【設計変更2026-08-13】hint_count/completed_atはChatSessionから
#     Attemptへ移動したため、ChatSessionSerializerは現在進行中(または
#     最新)のAttempt情報をcurrent_attemptとして返す。作成時はnode_idを
#     受け取れるようにした(create_chat_session_for_node経由)。
#     【統合2026-08-15】チャット機能ブランチの分岐推定(AIが親ノードを推定し、
#     ユーザーが確認する)のフィールドをChatMessageSerializerに統合した。
# VI: Tuần tự hóa JSON và kiểm tra đầu vào.
#     【Thay đổi thiết kế 2026-08-13】hint_count/completed_at đã chuyển từ
#     ChatSession sang Attempt, nên ChatSessionSerializer trả về thông
#     tin Attempt hiện tại (hoặc mới nhất) dưới dạng current_attempt. Lúc
#     tạo có thể nhận node_id (qua create_chat_session_for_node).
#     【Tích hợp 2026-08-15】Đã gộp các field của tính năng đoán nhánh (AI đoán
#     node cha, user xác nhận) từ nhánh tính năng Chat vào ChatMessageSerializer.
from rest_framework import serializers

from .models import Attempt, ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    parent_message_id = serializers.UUIDField(
        source="parent_message.id", allow_null=True, read_only=True
    )

    # JA: ★分岐確認UI用。AIが推定した親ノードとその確信度、確認済みかどうか。
    #     parent_confirmed=False かつ suggested_parent_id がある時だけ、
    #     フロントは「この質問は過去のどのノードの続きか」の確認UIを出す。
    # VI: ★Dùng cho UI xác nhận rẽ nhánh. Node cha do AI đoán, độ tin cậy, và đã xác nhận chưa.
    #     Frontend chỉ hiện UI xác nhận "câu hỏi này nối tiếp node cũ nào" khi
    #     parent_confirmed=False và có suggested_parent_id.
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
    """
    JA: メッセージ送信リクエストの検証。
        ★parent_message_id は「ユーザーが明示的にこのノードに返信する」場合のみ指定する。
          指定しない場合、バックエンドがAIに分岐先(親ノード)を推定させる。
        【統合2026-08-15】完了ボタン(COMPLETE)は本文を伴わずに押せるため、
        message_text は必須にしない。必須のままだと本文なしのCOMPLETEが400で
        弾かれ、ダミー文字列を送る羽目になり会話履歴が汚れる。
    VI: Validation request gửi tin nhắn.
        ★parent_message_id CHỈ truyền khi user chủ động chọn "trả lời tiếp node này".
          Nếu không truyền, backend sẽ để AI tự đoán node cha.
        【Tích hợp 2026-08-15】Nút hoàn thành (COMPLETE) có thể bấm mà không kèm nội dung,
        nên message_text không bắt buộc. Nếu bắt buộc thì COMPLETE không nội dung sẽ bị
        chặn 400, buộc phải gửi chuỗi giả và làm bẩn lịch sử hội thoại.
    """

    parent_message_id = serializers.UUIDField(required=False, allow_null=True)
    message_text = serializers.CharField(required=False, allow_blank=True, default="")
    action_type = serializers.ChoiceField(
        choices=["ANSWER", "REQUEST_CHANGE_METHOD", "HINT", "COMPLETE"], default="ANSWER"
    )
    understood = serializers.BooleanField(required=False, default=False)
    # JA: ★knowledge_node未設定のセッションをCOMPLETEして知識ノードを新規
    #     作成する場合のみ必須。保存先のTopicを指定する。
    # VI: ★Chỉ bắt buộc khi COMPLETE một phiên chat tự do (chưa gắn
    #     knowledge_node) để tạo knowledge node mới. Chỉ định Topic để lưu vào.
    topic_id = serializers.UUIDField(required=False, allow_null=True)


class ConfirmParentInputSerializer(serializers.Serializer):
    """JA: 親ノード確認/変更リクエストの検証 / VI: Validation request xác nhận/đổi node cha"""

    message_id = serializers.UUIDField(required=True)
    parent_message_id = serializers.UUIDField(required=False, allow_null=True)
