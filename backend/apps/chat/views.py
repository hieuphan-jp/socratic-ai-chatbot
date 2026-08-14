# JA: 認可・検証・services呼び出し・シリアライズのみ
#     【設計変更2026-08-13】perform_create が存在しない
#     services.create_chat_session を呼んでいたバグを修正し、
#     services.create_chat_session_for_node(node_id対応) を呼ぶように
#     変更した。send_message には understood(ユーザーの自己申告)を
#     追加で渡す。
# VI: Chỉ phân quyền, kiểm tra, gọi services, tuần tự hóa.
#     【Thay đổi thiết kế 2026-08-13】Sửa lỗi perform_create gọi
#     services.create_chat_session (không tồn tại), đổi sang gọi
#     services.create_chat_session_for_node (hỗ trợ node_id). send_message
#     truyền thêm understood (tự báo của người dùng).
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
        # JA: ★所有者絞り込み(必須) / VI: ★Lọc theo chủ sở hữu (bắt buộc)
        return ChatSession.objects.filter(user=self.request.user).prefetch_related(
            "messages", "attempts"
        )

    def perform_create(self, serializer):
        # JA: 作成はservicesへ委譲。所有者はrequest.user。node_idが渡されて
        #     いれば、そのノード向けの既存セッションを再利用するか新規作成
        #     する(create_chat_session_for_node側の責務)。
        # VI: Tạo ủy thác cho services; chủ sở hữu = request.user. Nếu có
        #     node_id thì tái sử dụng session hiện có cho node đó hoặc tạo
        #     mới (trách nhiệm của create_chat_session_for_node).
        serializer.instance = services.create_chat_session_for_node(
            user=self.request.user,
            node_id=serializer.validated_data.get("node_id"),
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
            understood=input_serializer.validated_data.get("understood", False),
        )

        return Response(
            {
                "user_message": ChatMessageSerializer(result["user_message"]).data
                if result.get("user_message")
                else None,
                "ai_message": ChatMessageSerializer(result["ai_message"]).data
                if result.get("ai_message")
                else None,
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
