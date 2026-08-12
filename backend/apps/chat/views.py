# JA: 認可・検証・services呼び出し・シリアライズのみ / VI: Chỉ phân quyền, kiểm tra, gọi services, tuần tự hóa
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsOwner

from . import services
from .models import ChatSession
from .serializers import ChatMessageSerializer, ChatSessionSerializer, SendMessageInputSerializer


class ChatSessionViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        # JA: ★所有者絞り込み（必須） / VI: ★Lọc theo chủ sở hữu (bắt buộc)
        return ChatSession.objects.filter(user=self.request.user).prefetch_related("messages")

    def perform_create(self, serializer):
        # JA: 作成は services へ委譲。所有者は request.user / VI: Tạo ủy thác cho services; chủ sở hữu = request.user
        serializer.instance = services.create_chat_session(
            user=self.request.user,
            title=serializer.validated_data.get("title", "New Chat Session"),
        )

    @action(detail=True, methods=["post"], url_path="send-message")
    def send_message(self, request, pk=None):
        """JA: メッセージ送信エンドポイント / VI: Endpoint gửi tin nhắn"""
        session = self.get_object()  # JA: 所有権チェック自動適用 / VI: Tự động lọc qua get_queryset
        input_serializer = SendMessageInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        result = services.send_message_and_get_ai_response(
            session=session,
            user_message_text=input_serializer.validated_data["message_text"],
            parent_message_id=input_serializer.validated_data.get("parent_message_id"),
            action_type=input_serializer.validated_data["action_type"],
        )

        return Response(
            {
                "user_message": ChatMessageSerializer(result["user_message"]).data,
                "ai_message": ChatMessageSerializer(result["ai_message"]).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        """JA: 過去メッセージ一覧取得エンドポイント / VI: Endpoint lấy danh sách tin nhắn cũ"""
        session = self.get_object()
        chat_messages = session.messages.all().order_by("created_at")
        serializer = ChatMessageSerializer(chat_messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="graph")
    def graph(self, request, pk=None):
        """JA: ツリー構造データ取得エンドポイント / VI: Endpoint lấy dữ liệu cấu trúc cây"""
        session = self.get_object()
        graph_data = services.get_session_graph_data(session=session)
        return Response(graph_data, status=status.HTTP_200_OK)