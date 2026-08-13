# JA: 認可・検証・services呼び出し・シリアライズのみ (KNOWLEDGE_NODE・ReviewLog連携 + 分岐推定確認 対応)
# VI: Chỉ phân quyền, kiểm tra, gọi services, tuần tự hóa (Tích hợp KNOWLEDGE_NODE, ReviewLog + xác nhận đoán nhánh)

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsOwner

from . import services
from .models import ChatSession
from .serializers import (
    ChatMessageSerializer,
    ChatSessionSerializer,
    ConfirmParentInputSerializer,
    SendMessageInputSerializer,
)


class ChatSessionViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        # JA: ★所有者絞り込み（必須）および KnowledgeNode の最適化取得
        # VI: ★Lọc theo chủ sở hữu (bắt buộc) và tối ưu truy vấn lấy kèm KnowledgeNode
        return (
            ChatSession.objects.filter(user=self.request.user)
            .select_related("knowledge_node")
            .prefetch_related("messages")
        )

    def perform_create(self, serializer):
        # JA: 作成は services へ委譲。node_id を渡して KNOWLEDGE_NODE と紐付け
        # VI: Tạo ủy thác cho services; truyền node_id để liên kết với KNOWLEDGE_NODE
        node_id = serializer.validated_data.get("node_id")
        title = serializer.validated_data.get("title", "New Chat Session")

        serializer.instance = services.create_chat_session_for_node(
            user=self.request.user,
            node_id=node_id,
            title=title,
        )

    @action(detail=True, methods=["post"], url_path="send-message")
    def send_message(self, request, pk=None):
        """
        JA: メッセージ送信エンドポイント (HINT / COMPLETE / 分岐推定 対応)
        VI: Endpoint gửi tin nhắn (Xử lý các action HINT / COMPLETE / đoán nhánh)
        """
        session = self.get_object()  # JA: 所有権チェック自動適用 / VI: Tự động lọc qua get_queryset
        input_serializer = SendMessageInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        action_type = input_serializer.validated_data.get("action_type", "ANSWER")
        user_message_text = input_serializer.validated_data.get("message_text", "")
        parent_message_id = input_serializer.validated_data.get("parent_message_id")

        result = services.send_message_and_get_ai_response(
            session=session,
            user_message_text=user_message_text,
            parent_message_id=parent_message_id,
            action_type=action_type,
        )

        return Response(
            {
                "user_message": ChatMessageSerializer(result["user_message"]).data
                if result.get("user_message")
                else None,
                "ai_message": ChatMessageSerializer(result["ai_message"]).data
                if result.get("ai_message")
                else None,
                "session_info": {
                    "hint_count": session.hint_count,
                    "completed_at": session.completed_at,
                },
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="confirm-parent")
    def confirm_parent(self, request, pk=None):
        """
        JA: ★AIが推定した親ノードをユーザーが確認、または別ノードに変更するエンドポイント。
            Gemini を呼ばないためクォータを消費しない。
        VI: ★Endpoint để user xác nhận node cha do AI đề xuất, hoặc chọn lại node khác.
            Không gọi Gemini nên không tốn quota.
        """
        session = self.get_object()
        input_serializer = ConfirmParentInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        message = services.confirm_message_parent(
            session=session,
            message_id=input_serializer.validated_data["message_id"],
            parent_message_id=input_serializer.validated_data.get("parent_message_id"),
        )

        return Response(ChatMessageSerializer(message).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        """JA: 過去メッセージ一覧取得エンドポイント / VI: Endpoint lấy danh sách tin nhắn cũ"""
        session = self.get_object()
        chat_messages = session.messages.all().order_by("created_at")
        serializer = ChatMessageSerializer(chat_messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="graph")
    def graph(self, request, pk=None):
        """JA: ツリー構造データ取得エンドポイント / VI: Endpoint lấy dữ liệu構造 cây"""
        session = self.get_object()
        graph_data = services.get_session_graph_data(session=session)
        return Response(graph_data, status=status.HTTP_200_OK)