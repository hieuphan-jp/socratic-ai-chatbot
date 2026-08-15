# JA: Chat機能の純粋な業務ロジック（HTTP非依存）
#     【統合2026-08-15】チャット機能ブランチの「分岐推定」(AIが親ノードを推定し
#     ユーザーが確認する)を取り込んだ。復習の記録(Attempt/ReviewLog)は develop の
#     設計に合わせてある: このモジュールは ReviewLog を直接作らず、Attempt を
#     完了させて apps.reviews.services.record_review_result に委譲する。
# VI: Logic nghiệp vụ thuần của tính năng Chat (không phụ thuộc HTTP).
#     【Tích hợp 2026-08-15】Đã lấy tính năng "đoán nhánh" (AI đoán node cha, user xác nhận)
#     từ nhánh tính năng Chat. Phần ghi nhận ôn tập (Attempt/ReviewLog) tuân theo thiết kế
#     của develop: module này KHÔNG tự tạo ReviewLog, mà đóng Attempt rồi ủy thác cho
#     apps.reviews.services.record_review_result.
import json
import logging
import re

from django.utils import timezone

from apps.ai.base import ChatMessage as AIChatMessage
from apps.ai.base import ChatResult
from apps.ai.client import get_llm
from apps.common.exceptions import ValidationError

from .models import Attempt, ChatMessage, ChatSession

logger = logging.getLogger(__name__)

# JA: ★家庭教師としての役割をより明確に指示。ヒントを段階的に導き、直接の答えは出さない。
# VI: ★Chỉ thị rõ ràng hơn vai trò gia sư. Dẫn dắt bằng gợi ý từng bước, không đưa thẳng đáp án.
SYSTEM_PROMPT = """
You are an AI Tutor helping a student learn step by step.

STRICT RULES:
1. NEVER give the complete/final answer directly, even if the user asks for it directly or insists.
2. Instead, guide with a hint, a leading question, or reveal only a small piece of the concept at a time.
3. If the user's attempt is close to correct, confirm what's right and encourage them to continue, without revealing the rest.
4. If the user seems stuck, break the problem into a smaller, easier sub-question rather than solving it for them.
5. You have access to the full conversation history below (previous questions and your previous replies).
   Use it to stay consistent and to correctly recall anything the user or you mentioned earlier.
6. Keep responses concise (a few sentences), conversational, and encouraging.
"""

# JA: 分岐推定用のシステムプロンプト。ユーザーの新しい質問が「直前の会話の続き」なのか
#     「過去の古い質問への出戻り(分岐)」なのかをAIに判定させ、JSONで返させる。
# VI: System prompt cho việc đoán nhánh. Cho AI phán đoán câu hỏi mới là "nối tiếp câu liền trước"
#     hay "quay lại rẽ nhánh từ câu hỏi cũ", và trả về dạng JSON.
BRANCHING_SYSTEM_PROMPT = """
あなたは学習者を指導する AI Tutor です。
ユーザーの質問に対してヒントを提供すると同時に、思考ツリーの分岐先（親ノード）を正確に推定してください。

【重要：分岐判定ガイドライン / Quy tắc phát hiện rẽ nhánh】
ユーザーの最新の質問について、以下の条件をチェックしてください：
1. **話題の切り替え・復帰**: ユーザーが直前の会話（N-1）を連続して深掘りせず、過去の質問（N-2, N-3...）の話題に戻っているか？
2. **参照単語の検知**: 「さっきの〜」「最初の〜」「〜についてだけど」「chủ đề trước...」「câu đầu tiên...」「nãy bạn nói...」などの過去を参照するキーワードが含まれているか？
3. **文脈の断絶**: 直前の会話と最新の質問のトピックが完全に切れているか？

【出力フォーマット / Format đầu ra】
必ず以下の JSON フォーマットのみで返答してください。余計なテキストや Markdown コードブロックを含めないでください。

{
  "answer": "ユーザーへのヒント回答 / Lời thoại trả lời cho User",
  "suggested_parent_id": "最も関連性の高い過去の USER メッセージの UUID (分岐がない場合は null) / UUID của câu hỏi USER tương ứng trong quá khứ nếu rẽ nhánh, ngược lại là null",
  "confidence": "high | medium | low"
}
"""

# JA: ★フリーチャット(knowledge_node未設定)が「完了」した際、会話内容から
#     知識ノードのtitle/contentをAIに要約させるための指示。
# VI: ★Chỉ thị để AI tóm tắt nội dung hội thoại thành title/content của
#     knowledge node, khi một phiên chat tự do (chưa gắn knowledge_node) "hoàn thành".
NODE_SUMMARY_SYSTEM_PROMPT = """
You are summarizing a tutoring conversation into a permanent study note for the student.

Based on the conversation so far, write a concise study note capturing what the student learned.

OUTPUT FORMAT (STRICT):
- Line 1: a short title (a few words, no trailing punctuation)
- From line 2 onward: a concise explanation of the concept, written for the student's own future review

Do not include any preamble, meta-commentary, or markdown formatting.
"""

NEEDS_AI_ANSWER = {"ANSWER", "REQUEST_CHANGE_METHOD"}
SESSION_NODE_TITLE_MAX_LEN = 255
# JA: 分岐推定でAIに見せる過去質問1件あたりの最大文字数 / VI: Độ dài tối đa mỗi câu hỏi cũ đưa cho AI
NODE_TOPIC_MAX_LEN = 100
# JA: AIに渡す会話履歴の最大件数と1件あたりの最大文字数（トークン節約）
# VI: Số lượng và độ dài tối đa của lịch sử hội thoại đưa cho AI (tiết kiệm token)
MAX_HISTORY_MESSAGES = 20
HISTORY_MESSAGE_MAX_LEN = 600


def create_chat_session_for_node(*, user, node_id=None, title: str = "New Session") -> ChatSession:
    # JA: 他アプリ所有のKnowledgeNodeは、所有権チェック込みの窓口経由で取得する
    #     (CONVENTIONS.md §10)。直接 objects.filter(id=...) で引くと、他人のノードに
    #     自分のセッションを紐付けられてしまう。
    # VI: KnowledgeNode thuộc app khác nên phải lấy qua cửa ngõ có kiểm tra quyền sở hữu
    #     (CONVENTIONS.md §10). Nếu tự query objects.filter(id=...) thì user có thể gắn
    #     session của mình vào node của người khác.
    from apps.topics import services as topics_services

    node = None
    if node_id:
        node = topics_services.get_owned_knowledge_node(user=user, node_id=node_id)

        existing = ChatSession.objects.filter(knowledge_node=node, user=user).first()
        if existing:
            return existing

        if title == "New Session":
            title = f"学習: {node.title}"

    return ChatSession.objects.create(user=user, knowledge_node=node, title=title)


def _extract_text(raw_response) -> str:
    """JA: LLMの戻り値からテキストを取り出す / VI: Lấy text từ giá trị trả về của LLM"""
    if isinstance(raw_response, ChatResult):
        return raw_response.text
    if hasattr(raw_response, "text"):
        return raw_response.text
    return str(raw_response)


def _extract_json(raw_text: str) -> dict | None:
    """
    JA: AIの応答からJSONを取り出す。JSON以外の前置きが混ざることがあるため、
        素直にパースできなければ最初の { ... } を正規表現で拾って再挑戦する。
    VI: Lấy JSON từ phản hồi của AI. Vì đôi khi AI thêm lời dẫn, nếu parse thẳng
        không được thì dùng regex bắt cụm { ... } đầu tiên rồi thử lại.
    """
    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        pass

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _build_history_messages(session: ChatSession) -> list[AIChatMessage]:
    """
    JA: これまでの会話履歴を AIChatMessage のリストに変換し、AI に渡す。
    VI: Chuyển lịch sử hội thoại đã có thành danh sách AIChatMessage để đưa cho AI.
    """
    past_messages = session.messages.order_by("-created_at")[:MAX_HISTORY_MESSAGES]
    history = []
    for msg in reversed(list(past_messages)):
        role = "user" if msg.sender == ChatMessage.Sender.USER else "assistant"
        history.append(AIChatMessage(role=role, content=msg.message_text[:HISTORY_MESSAGE_MAX_LEN]))
    return history


def _build_branching_instructions(user_nodes: list, text: str) -> str:
    """
    JA: 過去のUSER質問をノードIDつきの一覧に整形し、分岐推定の指示文を組み立てる。
        直前のノードではなく、より古いノードへの分岐だけを検出させるのが狙い。
    VI: Format các câu hỏi USER cũ thành danh sách kèm Node ID và dựng chỉ thị đoán nhánh.
        Mục tiêu: chỉ phát hiện rẽ nhánh về node cũ hơn, không phải node liền trước.
    """
    history_formatted = [
        f"- [Node ID: {msg.id}] (Bước {idx}): {msg.message_text[:NODE_TOPIC_MAX_LEN]}"
        for idx, msg in enumerate(user_nodes, start=1)
    ]
    history_str = "\n".join(history_formatted) if history_formatted else "Không có câu hỏi cũ nào."

    return f"""
{BRANCHING_SYSTEM_PROMPT}

=== LỊCH SỬ CÁC CÂU HỎI TRƯỚC ĐÂY CỦA USER (TỪ CŨ ĐẾN MỚI) ===
{history_str}

=== CÂU HỎI MỚI NHẤT CỦA USER ===
"{text}"

=== YÊU CẦU / INSTRUCTIONS ===
1. So sánh CÂU HỎI MỚI NHẤT với LỊCH SỬ CÁC CÂU HỎI TRƯỚC ĐÂY.
2. Nếu CÂU HỎI MỚI NHẤT đang muốn hỏi nối tiếp hoặc rẽ nhánh từ một [Node ID] cũ hơn (từ Bước 1 đến Bước N-2) thay vì câu liền trước (Bước N-1), hãy gán chuỗi UUID của [Node ID] đó vào `suggested_parent_id` và đặt `confidence` thành "high".
3. Nếu chỉ là câu hỏi tiếp nối tự nhiên của câu liền trước (Bước N-1), hãy gán `suggested_parent_id` là null và `confidence` là "low".
4. Trả về đúng định dạng JSON yêu cầu.
"""


def _generate_ai_answer(*, session: ChatSession, explicit_parent, action_type: str, text: str):
    """
    JA: AIの回答本文と、分岐推定の結果(推定親ノード・確信度・確定フラグ)を返す。
        ユーザーが明示的に親を指定した場合、または質問がまだ1件以下の場合は
        推定不要なので通常の回答だけを生成する(初回から確認UIが出るのを防ぐ)。
    VI: Trả về nội dung trả lời của AI kèm kết quả đoán nhánh (node cha đoán được,
        độ tin cậy, cờ đã chốt). Nếu user đã tự chỉ định node cha, hoặc mới có <= 1 câu hỏi,
        thì không cần đoán (tránh hiện UI xác nhận ngay từ câu đầu).
    """
    llm = get_llm()
    history = _build_history_messages(session)
    user_nodes = list(
        session.messages.filter(sender=ChatMessage.Sender.USER).order_by("created_at")
    )

    if explicit_parent is not None or len(user_nodes) <= 1:
        messages_payload = [
            AIChatMessage(role="system", content=SYSTEM_PROMPT),
            *history,
            AIChatMessage(role="user", content=f"Action: {action_type}\nMessage: {text}"),
        ]
        try:
            return _extract_text(llm.chat(messages_payload)), None, "", True
        except Exception as e:
            logger.error("JA: AI応答生成エラー: %s / VI: Lỗi tạo phản hồi AI: %s", e, e)
            return f"[AI Tutor] Lỗi tạo phản hồi từ AI: {e}", None, "", True

    messages_payload = [
        AIChatMessage(role="system", content=SYSTEM_PROMPT),
        *history,
        AIChatMessage(role="user", content=_build_branching_instructions(user_nodes, text)),
    ]

    try:
        raw_text = _extract_text(llm.chat(messages_payload))
        parsed = _extract_json(raw_text)

        if parsed and isinstance(parsed, dict) and "answer" in parsed:
            parent_confidence = parsed.get("confidence", "low") or "low"
            suggested_parent = None
            suggested_id = parsed.get("suggested_parent_id")

            # JA: AIが挙げたIDが実在する場合だけ採用する / VI: Chỉ nhận ID nếu thực sự tồn tại trong DB
            if suggested_id and str(suggested_id).lower() != "null":
                suggested_parent = ChatMessage.objects.filter(
                    session=session, id=suggested_id
                ).first()

            # JA: 確信度が high の時だけ未確定にして、フロントに確認UIを出させる。
            # VI: Chỉ để chưa chốt khi độ tin cậy là high, để frontend hiện UI xác nhận.
            parent_confirmed = not (parent_confidence == "high" and suggested_parent)
            return parsed["answer"], suggested_parent, parent_confidence, parent_confirmed

        # JA: JSONでなく普通の文章が返ってきた場合はそのまま回答として扱う。
        # VI: Nếu AI trả về văn bản thường thay vì JSON thì dùng luôn làm câu trả lời.
        return raw_text, None, "", True
    except Exception as e:
        logger.error("JA: AI応答生成エラー: %s / VI: Lỗi tạo phản hồi AI: %s", e, e)
        return f"[AI Tutor] Lỗi tạo phản hồi từ AI: {e}", None, "", True


def _summarize_session_as_node(session: ChatSession) -> tuple[str, str]:
    """
    JA: セッションの会話履歴全体をAIに渡し、知識ノードのtitle/contentを要約
        させる。1行目をtitle、2行目以降をcontentとして解釈する規約。
    VI: Đưa toàn bộ lịch sử hội thoại của session cho AI, nhờ tóm tắt thành
        title/content của knowledge node. Quy ước: dòng 1 là title, từ dòng
        2 trở đi là content.
    """
    llm = get_llm()
    history = [
        AIChatMessage(
            role="user" if msg.sender == ChatMessage.Sender.USER else "assistant",
            content=msg.message_text[:600],
        )
        for msg in session.messages.order_by("created_at")
    ]
    messages_payload = [
        AIChatMessage(role="system", content=NODE_SUMMARY_SYSTEM_PROMPT),
        *history,
        AIChatMessage(
            role="user",
            content="Summarize this conversation into a study note title and content now.",
        ),
    ]
    raw_response = llm.chat(messages_payload)
    if isinstance(raw_response, ChatResult):
        text = raw_response.text
    elif hasattr(raw_response, "text"):
        text = raw_response.text
    else:
        text = str(raw_response)
    text = text.strip()

    lines = text.splitlines()
    title = (lines[0].strip() if lines else "")[:SESSION_NODE_TITLE_MAX_LEN]
    content = "\n".join(lines[1:]).strip() or text
    return title or session.title, content


def create_knowledge_node_from_session(*, session: ChatSession, user, topic_id):
    """
    JA: フリーチャット(knowledge_node未設定)が「完了」した時に呼ばれる。
        会話内容からAIにtitle/contentを要約させ、指定Topic配下に新しい
        KnowledgeNodeとして保存し、このセッションと1:1(OneToOne)で紐付ける。
        KnowledgeNodeの作成自体は所有アプリ(apps.topics)のservices経由で行う
        (このアプリからKnowledgeNode.objects.createを直接呼ばない)。
    VI: Được gọi khi một phiên chat tự do (chưa gắn knowledge_node) "hoàn
        thành". Nhờ AI tóm tắt hội thoại thành title/content, lưu thành một
        KnowledgeNode mới dưới Topic được chỉ định, và gắn 1:1 (OneToOne)
        với session này. Việc tạo KnowledgeNode được ủy thác qua services
        của app sở hữu (apps.topics), không gọi thẳng
        KnowledgeNode.objects.create từ app này.
    """
    from apps.topics import services as topics_services

    topic = topics_services.get_owned_topic(user=user, topic_id=topic_id)
    title, content = _summarize_session_as_node(session)
    node = topics_services.create_knowledge_node(
        user=user, topic=topic, title=title, content=content
    )

    session.knowledge_node = node
    session.save(update_fields=["knowledge_node"])
    return node


def get_or_create_active_attempt(*, session: ChatSession) -> Attempt:
    attempt = session.attempts.filter(completed_at__isnull=True).order_by("-created_at").first()
    if attempt is None:
        attempt = Attempt.objects.create(chat_session=session)
    return attempt


def record_hint_or_completion(
    *, session: ChatSession, action_type: str, understood: bool | None = None
):
    attempt = get_or_create_active_attempt(session=session)

    if action_type == "HINT":
        attempt.hint_count += 1
        attempt.save(update_fields=["hint_count"])

    if action_type == "COMPLETE":
        attempt.completed_at = timezone.now()
        attempt.save(update_fields=["completed_at"])

        from apps.reviews.services import record_review_result

        record_review_result(attempt, bool(understood))

    return attempt


def get_session_graph_data(*, session: ChatSession) -> dict:
    messages = session.messages.all().order_by("created_at")

    nodes = []
    edges = []

    for msg in messages:
        nodes.append(
            {
                "id": str(msg.id),
                "type": "stepNode" if msg.node_type == "STEP" else "answerNode",
                "data": {
                    "label": msg.sender,
                    "text": msg.message_text,
                    "node_type": msg.node_type,
                },
            }
        )

        if msg.parent_message_id:
            edges.append(
                {
                    "id": f"e-{msg.parent_message_id}-{msg.id}",
                    "source": str(msg.parent_message_id),
                    "target": str(msg.id),
                }
            )

    return {"nodes": nodes, "edges": edges}


def send_message_and_get_ai_response(
    *,
    session: ChatSession,
    user_message_text: str,
    parent_message_id=None,
    action_type: str = "ANSWER",
    understood: bool | None = None,
    topic_id=None,
) -> dict:
    text = (user_message_text or "").strip()
    if action_type in NEEDS_AI_ANSWER and not text:
        raise ValidationError("メッセージ内容は必須です / Nội dung tin nhắn là bắt buộc")

    # JA: ★フリーチャット(knowledge_node未設定)がCOMPLETEした瞬間に、初めて
    #     知識ノードを作成しこのセッションと1:1で紐付ける。既にノードがある
    #     セッション(復習チャット)ではここは通らない。record_review_result は
    #     knowledge_node必須のため、この処理を先に済ませておく必要がある。
    # VI: ★Khi một phiên chat tự do (chưa gắn knowledge_node) COMPLETE lần
    #     đầu, tạo mới knowledge node và gắn 1:1 với session này. Session đã
    #     có sẵn node (chat ôn tập) sẽ không đi qua nhánh này. Vì
    #     record_review_result bắt buộc phải có knowledge_node, bước này cần
    #     làm trước.
    if action_type == "COMPLETE" and session.knowledge_node_id is None:
        if not topic_id:
            raise ValidationError(
                "知識ノードとして保存するTopicを選択してください / Vui lòng chọn Topic để lưu"
            )
        create_knowledge_node_from_session(session=session, user=session.user, topic_id=topic_id)

    if action_type in ("HINT", "COMPLETE"):
        record_hint_or_completion(session=session, action_type=action_type, understood=understood)

    # JA: ユーザーが「このノードへの返信」を明示した場合の親。未指定ならAIに推定させる。
    # VI: Node cha khi user chủ động chọn "trả lời node này". Không chỉ định thì để AI đoán.
    explicit_parent = None
    if parent_message_id:
        explicit_parent = ChatMessage.objects.filter(session=session, id=parent_message_id).first()

    suggested_parent = None
    parent_confidence = ""
    parent_confirmed = True

    if action_type == "HINT":
        ai_text = "続けてみましょう。分からない部分をもう少し詳しく教えてください。"
    elif action_type == "COMPLETE":
        ai_text = "お疲れ様でした！学習の記録を保存しました。"
    else:
        ai_text, suggested_parent, parent_confidence, parent_confirmed = _generate_ai_answer(
            session=session, explicit_parent=explicit_parent, action_type=action_type, text=text
        )

    user_node_type = (
        ChatMessage.NodeType.ANSWER
        if action_type == "ANSWER"
        else ChatMessage.NodeType.CHANGE_METHOD
    )
    user_msg = None
    if text:
        # JA: 親は「明示指定 > AI推定 > 直前のメッセージ」の優先順で決める。
        # VI: Node cha ưu tiên: user chỉ định > AI đoán > tin nhắn ngay trước đó.
        final_parent = (
            explicit_parent or suggested_parent or session.messages.order_by("-created_at").first()
        )
        user_msg = ChatMessage.objects.create(
            session=session,
            parent_message=final_parent,
            suggested_parent=suggested_parent,
            parent_confidence=parent_confidence,
            parent_confirmed=parent_confirmed,
            sender=ChatMessage.Sender.USER,
            message_text=text,
            node_type=user_node_type,
        )

    ai_msg = ChatMessage.objects.create(
        session=session,
        parent_message=user_msg,
        sender=ChatMessage.Sender.AI,
        message_text=str(ai_text),
        node_type=ChatMessage.NodeType.STEP,
        is_hint=(action_type == "HINT"),
    )

    return {"user_message": user_msg, "ai_message": ai_msg}


def confirm_message_parent(*, session: ChatSession, message_id, parent_message_id) -> ChatMessage:
    """
    JA: 分岐確認UIでユーザーが親ノードを確定/変更したときの処理。
        AI推定(suggested_parent)を採用する場合も、元の親のままにする場合も、
        どちらも「ユーザーが確認済み」として parent_confirmed=True にする。
    VI: Xử lý khi user chốt/đổi node cha ở UI xác nhận rẽ nhánh.
        Dù chấp nhận đề xuất của AI (suggested_parent) hay giữ nguyên node cha cũ,
        đều đánh dấu parent_confirmed=True vì user đã xác nhận.
    """
    message = ChatMessage.objects.filter(
        session=session, id=message_id, sender=ChatMessage.Sender.USER
    ).first()
    if message is None:
        raise ValidationError("メッセージが見つかりません / Không tìm thấy tin nhắn")

    parent = None
    if parent_message_id:
        parent = ChatMessage.objects.filter(session=session, id=parent_message_id).first()
        if parent is None:
            raise ValidationError("親メッセージが見つかりません / Không tìm thấy tin nhắn cha")

    message.parent_message = parent
    message.parent_confirmed = True
    message.save(update_fields=["parent_message", "parent_confirmed"])
    return message
