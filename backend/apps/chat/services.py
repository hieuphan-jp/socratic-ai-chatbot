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
from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from apps.ai.base import ChatMessage as AIChatMessage
from apps.ai.base import ChatResult
from apps.ai.client import get_llm
from apps.common.exceptions import ValidationError

from . import branching, steps
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

# JA: ★ステップ判定用のシステムプロンプト。
#     【設計変更 2026-08-16】以前は「直前(N-1)の続きか、N-2以前への出戻りか」だけを判定させ、
#     直前ステップからの分岐を明示的に禁止していた。そのため「HTMLとは何か」の直後に
#     「HTMLの役割は」と聞いても、仕様通りnullが返り、木がまっすぐ伸びるだけだった。
#     本来ほしいのは「幹(大きなステップ)か、枝(既出ステップを掘り下げる小さな質問)か」の
#     判定なので、軸を作り替えた。枝の親は直前ステップでも構わない。
#     あわせて、ノードに出すタイトルも同じ応答で返させる(AI呼び出し回数は増えない)。
# VI: ★System prompt để phán đoán bước.
#     【Thay đổi thiết kế 2026-08-16】Trước đây chỉ phán đoán "tiếp nối câu liền trước (N-1)"
#     hay "quay lại bước từ N-2 trở về trước", và CẤM rẽ nhánh từ bước liền trước. Vì vậy hỏi
#     "vai trò của HTML" ngay sau "HTML là gì" vẫn trả null đúng như đặc tả, cây chỉ đi thẳng.
#     Cái thực sự cần là phán đoán "thân (bước lớn)" hay "nhánh (câu hỏi nhỏ đào sâu bước đã có)",
#     nên đã đổi trục phán đoán. Cha của nhánh có thể chính là bước liền trước.
#     Đồng thời trả luôn tiêu đề hiển thị trên node trong cùng phản hồi (không tăng số lần gọi AI).
STEP_ANALYSIS_SYSTEM_PROMPT = """
あなたは学習者を指導する AI Tutor です。
ユーザーの質問にヒントで答えると同時に、その質問を「学習の思考ツリー」のどこに置くべきかを判定してください。

【判定ルール / Quy tắc phán đoán】
- is_new_step = true（幹：新しい大きなステップ）
  学習の目的に向かって前進する、新しいテーマに入ったとき。
  例）「Webアプリを作りたい」→「HTMLとは何か」→「CSSとは何か」はそれぞれ幹。

- is_new_step = false（枝：既出ステップから派生した小さな質問）
  すでに出たステップの内容を掘り下げる、補足を求める、具体例を尋ねる質問。
  **直前のステップに対する掘り下げでも必ず枝にすること。**
  例）「HTMLとは何か」の直後の「HTMLの役割は？」「タグの書き方は？」は枝。
  この場合 parent_step_id に、最も関連する既出ステップの UUID を必ず入れること。

【step_title のルール / Quy tắc step_title】
- ユーザーの発言をそのまま写さず、内容を要約した10〜20文字程度の短い見出しにすること。
- 体言止め（名詞で終える）。例）「HTMLの役割」「二次方程式の判別式」

【出力フォーマット / Format đầu ra】
必ず以下の JSON のみで返答してください。前置きや Markdown のコードブロックを含めないでください。

{
  "answer": "ユーザーへのヒント回答 / Lời thoại trả lời cho User",
  "is_new_step": true または false,
  "parent_step_id": "枝の場合は関連する既出ステップの UUID。幹の場合は null",
  "step_title": "ノードに表示する短い要約タイトル",
  "confidence": "high | low"
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


def _build_step_analysis_instructions(
    *, goal: str, step_nodes: list, labels: dict, text: str
) -> str:
    """
    JA: 既出ステップを「番号つきの一覧」に整形し、幹/枝の判定指示を組み立てる。
        ★判定の軸に「当初の目的」を渡すのが要点。目的が分からないと、AIは
        「その質問が目的に向かって前進しているか(幹)、寄り道か(枝)」を判断できない。
        送るのは発言全文ではなく要約タイトル(あれば)なので、会話が伸びてもトークンが膨らみにくい。
    VI: Format các bước đã có thành danh sách kèm số thứ tự và dựng chỉ thị phán đoán thân/nhánh.
        ★Điểm mấu chốt là đưa "mục tiêu ban đầu" vào làm trục phán đoán. Không biết mục tiêu thì
        AI không thể xác định câu hỏi đang tiến tới mục tiêu (thân) hay chỉ là rẽ ngang (nhánh).
        Gửi tiêu đề tóm tắt (nếu có) thay vì nguyên văn nên hội thoại dài cũng ít phình token.
    """
    formatted = [
        f"- [ステップ {labels.get(node.id, '?')}] "
        f"[UUID: {node.id}] {(node.step_title or node.message_text)[:NODE_TOPIC_MAX_LEN]}"
        for node in step_nodes
    ]
    steps_str = "\n".join(formatted) if formatted else "(まだステップはありません)"

    return f"""
{STEP_ANALYSIS_SYSTEM_PROMPT}

=== 学習の当初の目的 / Mục tiêu học tập ban đầu ===
{goal[:NODE_TOPIC_MAX_LEN]}

=== これまでのステップ（古い順）/ Các bước đã có (từ cũ đến mới) ===
{steps_str}

=== ユーザーの新しい質問 / Câu hỏi mới của user ===
"{text}"

=== 手順 / Các bước thực hiện ===
1. 新しい質問が「目的に向かう新しいテーマ」なら is_new_step = true、
   「既出ステップの掘り下げ・補足」なら is_new_step = false とする。
2. is_new_step = false のときは、最も関連する既出ステップの UUID を parent_step_id に入れる。
   直前のステップでも構わない。
3. step_title に、その質問を要約した短い見出しを入れる。
4. 指定の JSON 形式だけで返す。
"""


def get_branching_strategy() -> str:
    """
    JA: 分岐推定の方式を返す。CHAT_BRANCHING_STRATEGY で切り替える。
        - "ai"     … AIにJSONで判定させる(精度は高いがプロンプトが重い)
        - "bigram" … 文字bigram類似度で判定する(AI呼び出しは通常の回答1回だけ、判定は無料)
        - "off"    … 分岐推定をしない(常に直前の続き扱い)
    VI: Trả về phương thức đoán nhánh, đổi bằng CHAT_BRANCHING_STRATEGY.
        - "ai"     … để AI phán đoán bằng JSON (chính xác hơn nhưng prompt nặng)
        - "bigram" … dùng similarity bigram ký tự (AI chỉ gọi 1 lần cho câu trả lời, phần đoán miễn phí)
        - "off"    … không đoán nhánh (luôn coi là tiếp nối bước liền trước)
    """
    return str(getattr(settings, "CHAT_BRANCHING_STRATEGY", "ai")).strip().lower()


def _plain_answer(*, llm, history, action_type: str, text: str) -> str:
    """
    JA: 分岐推定を伴わない、素の回答生成。プロンプトが軽いぶん安く速い。
    VI: Sinh câu trả lời thuần, không kèm đoán nhánh. Prompt nhẹ nên rẻ và nhanh hơn.
    """
    messages_payload = [
        AIChatMessage(role="system", content=SYSTEM_PROMPT),
        *history,
        AIChatMessage(role="user", content=f"Action: {action_type}\nMessage: {text}"),
    ]
    return _extract_text(llm.chat(messages_payload))


@dataclass
class StepAnalysis:
    """
    JA: 1回のユーザー発言に対する「回答」と「思考ツリー上の置き場所」の判定結果。
    VI: Kết quả cho một phát ngôn của user: "câu trả lời" và "vị trí trên cây tư duy".
    """

    answer: str
    step_kind: str
    parent: ChatMessage | None
    step_title: str
    confidence: str
    parent_confirmed: bool


def _get_step_nodes(session: ChatSession) -> list[ChatMessage]:
    """JA: 木に載っているステップだけを古い順に返す / VI: Trả về các bước trên cây theo thứ tự cũ→mới"""
    return list(
        session.messages.exclude(step_kind=ChatMessage.StepKind.NONE).order_by("created_at")
    )


def _session_goal(session: ChatSession) -> str:
    """
    JA: そのセッションの「当初の目的」= 最初のユーザー発言。幹/枝の判定の軸になる。
    VI: "Mục tiêu ban đầu" của session = phát ngôn đầu tiên của user; là trục phán đoán thân/nhánh.
    """
    first = session.messages.filter(sender=ChatMessage.Sender.USER).order_by("created_at").first()
    return first.message_text if first else session.title


def _resolve_branch_parent(
    *, session: ChatSession, step_nodes: list[ChatMessage], parent_id, text: str
) -> ChatMessage | None:
    """
    JA: AIが指した親ステップを解決する。IDが無効な場合は、文字bigramの類似度で
        代替候補を探し、それも無ければ直近のステップに繋ぐ(木から外れないように)。
    VI: Giải quyết bước cha do AI chỉ định. Nếu ID không hợp lệ thì tìm ứng viên thay thế bằng
        similarity bigram, không có nữa thì nối vào bước gần nhất (để không rơi khỏi cây).
    """
    if parent_id and str(parent_id).lower() != "null":
        found = next((node for node in step_nodes if str(node.id) == str(parent_id)), None)
        if found:
            return found
        logger.warning("[step] AIが実在しない親ステップIDを返した: %s", parent_id)

    suggestion = branching.suggest_parent(
        new_text=text,
        candidates=[(str(node.id), node.step_title or node.message_text) for node in step_nodes],
    )
    if branching.should_adopt(suggestion):
        return next((node for node in step_nodes if str(node.id) == suggestion.parent_id), None)

    return step_nodes[-1] if step_nodes else None


def _analyze_and_answer(
    *, session: ChatSession, explicit_parent, action_type: str, text: str
) -> StepAnalysis:
    """
    JA: AIに「回答」「幹か枝か」「枝ならどのステップの下か」「ノードのタイトル」を
        1回のJSON応答でまとめて返させる。判定のためだけの追加API呼び出しは行わない。
        ユーザーが親を明示した場合と、まだステップが1つも無い場合はAIに判定させない。
    VI: Cho AI trả về trong MỘT phản hồi JSON: "câu trả lời", "thân hay nhánh",
        "nếu là nhánh thì dưới bước nào", "tiêu đề node". Không gọi thêm API chỉ để phán đoán.
        Không hỏi AI khi user đã tự chỉ định cha, hoặc khi chưa có bước nào.
    """
    llm = get_llm()
    history = _build_history_messages(session)
    step_nodes = _get_step_nodes(session)
    strategy = get_branching_strategy()

    def plain(step_kind: str, parent: ChatMessage | None) -> StepAnalysis:
        try:
            answer = _plain_answer(llm=llm, history=history, action_type=action_type, text=text)
        except Exception as e:
            logger.error("JA: AI応答生成エラー: %s / VI: Lỗi tạo phản hồi AI: %s", e, e)
            answer = f"[AI Tutor] Lỗi tạo phản hồi từ AI: {e}"
        return StepAnalysis(
            answer=answer,
            step_kind=step_kind,
            parent=parent,
            step_title=steps.fallback_title(text),
            confidence="",
            parent_confirmed=True,
        )

    # JA: ユーザーが「このステップへの返信」を明示した場合は、その意思をそのまま採用する。
    # VI: Nếu user đã chủ động chọn "trả lời bước này" thì tôn trọng đúng ý đó.
    if explicit_parent is not None:
        return plain(ChatMessage.StepKind.BRANCH, explicit_parent)

    # JA: 最初の発言は必ず幹。判定する相手がいないのでAIにも聞かない。
    # VI: Phát ngôn đầu tiên luôn là thân. Không có gì để so nên cũng không hỏi AI.
    if not step_nodes or strategy == "off":
        return plain(ChatMessage.StepKind.TRUNK, None)

    labels = steps.build_step_labels(step_nodes)
    messages_payload = [
        AIChatMessage(role="system", content=SYSTEM_PROMPT),
        *history,
        AIChatMessage(
            role="user",
            content=_build_step_analysis_instructions(
                goal=_session_goal(session), step_nodes=step_nodes, labels=labels, text=text
            ),
        ),
    ]

    try:
        raw_text = _extract_text(llm.chat(messages_payload))
    except Exception as e:
        logger.error("JA: AI応答生成エラー: %s / VI: Lỗi tạo phản hồi AI: %s", e, e)
        return StepAnalysis(
            answer=f"[AI Tutor] Lỗi tạo phản hồi từ AI: {e}",
            step_kind=ChatMessage.StepKind.TRUNK,
            parent=None,
            step_title=steps.fallback_title(text),
            confidence="",
            parent_confirmed=True,
        )

    parsed = _extract_json(raw_text)
    if not (parsed and isinstance(parsed, dict) and "answer" in parsed):
        # JA: ★JSONで返らなかった場合。以前はここが完全に無言だったため、
        #     ステップ判定が黙って無効化されていることに誰も気づけなかった。
        # VI: ★Trường hợp không trả về JSON. Trước đây chỗ này hoàn toàn im lặng nên
        #     không ai nhận ra việc phán đoán bước đã bị vô hiệu hóa ngầm.
        logger.warning(
            "[step] AIがJSONを返さなかったため幹として扱う。先頭200文字: %r", raw_text[:200]
        )
        return StepAnalysis(
            answer=raw_text,
            step_kind=ChatMessage.StepKind.TRUNK,
            parent=None,
            step_title=steps.fallback_title(text),
            confidence="",
            parent_confirmed=True,
        )

    is_new_step = bool(parsed.get("is_new_step", True))
    title = steps.clean_title(parsed.get("step_title", "")) or steps.fallback_title(text)
    confidence = str(parsed.get("confidence", "low") or "low")

    if is_new_step:
        logger.info("[step] 幹として追加: %s", title)
        return StepAnalysis(
            answer=parsed["answer"],
            step_kind=ChatMessage.StepKind.TRUNK,
            parent=None,
            step_title=title,
            confidence=confidence,
            parent_confirmed=True,
        )

    parent = _resolve_branch_parent(
        session=session, step_nodes=step_nodes, parent_id=parsed.get("parent_step_id"), text=text
    )
    # JA: 直近のステップにぶら下がるのは自然な流れなので確認を求めない。
    #     それ以外(過去のステップへの出戻り)のときだけ確認UIを出す。
    # VI: Nối vào bước gần nhất là diễn tiến tự nhiên nên không cần hỏi lại.
    #     Chỉ hiện UI xác nhận khi nối về bước cũ hơn.
    is_natural = parent is not None and step_nodes and parent.id == step_nodes[-1].id
    logger.info("[step] 枝として追加: %s → 親=%s", title, parent.step_title if parent else None)
    return StepAnalysis(
        answer=parsed["answer"],
        step_kind=ChatMessage.StepKind.BRANCH,
        parent=parent,
        step_title=title,
        confidence=confidence,
        parent_confirmed=bool(is_natural or parent is None),
    )


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
    """
    JA: 思考ツリーの描画データ。★ステップ(幹/枝)だけを返し、相槌やAIの返答は含めない。
        【設計変更 2026-08-16】ステップ番号の採番をここ(サーバー側)に移した。
        以前はフロントが「USER発言の時系列の通し番号」を振っていたため、枝に分かれても
        番号が連番のままで、番号とノードの位置が食い違っていた。木を辿って採番すれば
        構造と番号が必ず一致する(幹=1,2,3 / 3の枝=3-1,3-2)。
    VI: Dữ liệu vẽ cây tư duy. ★Chỉ trả về các bước (thân/nhánh), không gồm câu đệm và câu trả lời AI.
        【Thay đổi thiết kế 2026-08-16】Chuyển việc đánh số bước về đây (phía server).
        Trước đây frontend đánh số tuần tự theo thời gian của phát ngôn USER nên khi rẽ nhánh,
        số vẫn chạy liên tiếp và lệch với vị trí node. Duyệt cây để đánh số thì cấu trúc và số
        luôn khớp (thân = 1,2,3 / nhánh của 3 = 3-1, 3-2).
    """
    step_nodes = _get_step_nodes(session)
    labels = steps.build_step_labels(step_nodes)
    step_ids = {node.id for node in step_nodes}

    nodes = []
    edges = []
    for node in step_nodes:
        label = labels.get(node.id, "")
        nodes.append(
            {
                "id": str(node.id),
                "type": "stepNode",
                "data": {
                    "step_label": label,
                    "title": node.step_title or node.message_text[:24],
                    "text": node.message_text,
                    "step_kind": node.step_kind,
                    "parent_confirmed": node.parent_confirmed,
                },
            }
        )

        # JA: 幹どうしは時系列で繋ぎ、枝は親ステップへ繋ぐ。
        # VI: Các bước thân nối theo thứ tự thời gian; nhánh nối vào bước cha.
        if node.step_kind == ChatMessage.StepKind.BRANCH and node.parent_message_id in step_ids:
            source = node.parent_message_id
        else:
            trunk_before = [
                n
                for n in step_nodes
                if n.step_kind == ChatMessage.StepKind.TRUNK and n.created_at < node.created_at
            ]
            source = trunk_before[-1].id if trunk_before else None

        if source:
            edges.append(
                {
                    "id": f"e-{source}-{node.id}",
                    "source": str(source),
                    "target": str(node.id),
                    "is_branch": node.step_kind == ChatMessage.StepKind.BRANCH,
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

    analysis = None
    if action_type == "HINT":
        ai_text = "続けてみましょう。分からない部分をもう少し詳しく教えてください。"
    elif action_type == "COMPLETE":
        ai_text = "お疲れ様でした！学習の記録を保存しました。"
    elif steps.is_trivial_message(text):
        # JA: ★相槌や極端に短い発言は、AIに判定させる前にここで足切りする。
        #     以前は全てのユーザー発言が無条件にステップ化されていたため、
        #     「そうですね」だけでノードが生えていた。
        #     ステップにはしないが会話としては成立させたいので、回答は普通に生成する。
        # VI: ★Câu đệm hoặc phát ngôn cực ngắn thì lọc ngay tại đây, trước khi hỏi AI.
        #     Trước đây mọi phát ngôn user đều thành bước vô điều kiện nên chỉ "そうですね"
        #     cũng mọc ra node. Không tạo bước nhưng vẫn phải trả lời bình thường.
        logger.info("[step] 相槌としてステップ化しない: %r", text[:30])
        ai_text = _plain_answer(
            llm=get_llm(),
            history=_build_history_messages(session),
            action_type=action_type,
            text=text,
        )
    else:
        analysis = _analyze_and_answer(
            session=session, explicit_parent=explicit_parent, action_type=action_type, text=text
        )
        ai_text = analysis.answer

    user_node_type = (
        ChatMessage.NodeType.ANSWER
        if action_type == "ANSWER"
        else ChatMessage.NodeType.CHANGE_METHOD
    )
    user_msg = None
    if text:
        user_msg = ChatMessage.objects.create(
            session=session,
            # JA: 枝なら親ステップに繋ぐ。幹・相槌は親を持たない(木の採番側で最上位扱い)。
            # VI: Nhánh thì nối vào bước cha. Thân và câu đệm không có cha (được coi là cấp cao nhất khi đánh số).
            parent_message=analysis.parent if analysis else None,
            suggested_parent=analysis.parent
            if analysis and analysis.step_kind == ChatMessage.StepKind.BRANCH
            else None,
            parent_confidence=analysis.confidence if analysis else "",
            parent_confirmed=analysis.parent_confirmed if analysis else True,
            step_kind=analysis.step_kind if analysis else ChatMessage.StepKind.NONE,
            step_title=analysis.step_title if analysis else "",
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
