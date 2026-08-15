# JA: 認可・検証・services呼び出し・シリアライズのみ
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
        return ChatSession.objects.filter(user=self.request.user).prefetch_related(
            "messages", "attempts"
        )

    def perform_create(self, serializer):
        serializer.instance = services.create_chat_session_for_node(
            user=self.request.user,
            node_id=serializer.validated_data.get("node_id"),
            title=serializer.validated_data.get("title", "New Chat Session"),
        )

    @action(detail=True, methods=["post"], url_path="send-message")
    def send_message(self, request, pk=None):
        session = self.get_object()
        input_serializer = SendMessageInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        result = services.send_message_and_get_ai_response(
            session=session,
            user_message_text=input_serializer.validated_data["message_text"],
            parent_message_id=input_serializer.validated_data.get("parent_message_id"),
            action_type=input_serializer.validated_data["action_type"],
            understood=input_serializer.validated_data.get("understood", False),
            topic_id=input_serializer.validated_data.get("topic_id"),
        )

        return Response(
            {
                "user_message": ChatMessageSerializer(result["user_message"]).data
                if result.get("user_message")
                else None,
                "ai_message": ChatMessageSerializer(result["ai_message"]).data
                if result.get("ai_message")
                else None,
                # JA: ★このリクエストで知識ノードが新規作成された場合、フロントが
                #     「知識ノードとして保存しました」と表示するために返す。
                # VI: ★Trả về để frontend hiển thị "đã lưu thành knowledge node"
                #     khi node vừa được tạo mới trong request này.
                "knowledge_node": str(session.knowledge_node_id)
                if session.knowledge_node_id
                else None,
                "knowledge_node_title": session.knowledge_node.title
                if session.knowledge_node_id
                else None,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="confirm-parent")
    def confirm_parent(self, request, pk=None):
        """
        JA: 分岐確認UIからの「この過去ノードに繋げる／今のままにする」を確定する。
        VI: Chốt lựa chọn "nối vào node cũ này / giữ nguyên" từ UI xác nhận rẽ nhánh.
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
        session = self.get_object()
        chat_messages = session.messages.all().order_by("created_at")
        serializer = ChatMessageSerializer(chat_messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="graph")
    def graph(self, request, pk=None):
        session = self.get_object()
        graph_data = services.get_session_graph_data(session=session)
        return Response(graph_data, status=status.HTTP_200_OK)
