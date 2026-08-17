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
from django.db import IntegrityError
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
# JA: ★数式の書き方に関する共通ルール。チャット画面はプレーンテキスト表示
#     (LaTeX/Markdownのレンダラーを持たない)なので、AIが $$ax^2+bx+c=0$$ や
#     \neq のようなLaTeX記法をそのまま返すと、画面には未レンダリングの記号列が
#     並んで表示され、ユーザーには「文字化け」に見えてしまう(実際に日本語の
#     数式トピックで報告された不具合)。加えて、STEP_ANALYSIS_SYSTEM_PROMPT の
#     ようにJSON形式での応答を要求している場面では、\neq や \frac のバックスラッシュが
#     有効なJSONエスケープ(\n, \t 等)ではないため、AIの応答をjson.loadsする際に
#     パース失敗を誘発することもある。3つのシステムプロンプト全てに共通で
#     差し込むことで、両方の問題を根元で防ぐ。
# VI: ★Quy tắc chung về cách viết công thức toán. Màn hình chat hiển thị dạng
#     plain text (không có renderer LaTeX/Markdown), nên nếu AI trả nguyên văn
#     ký hiệu LaTeX như $$ax^2+bx+c=0$$ hay \neq, màn hình sẽ hiện chuỗi ký hiệu
#     chưa render, người dùng nhìn như "lỗi phông chữ" (đã bị báo cáo với chủ đề
#     công thức tiếng Nhật). Ngoài ra, ở nơi yêu cầu trả lời dạng JSON như
#     STEP_ANALYSIS_SYSTEM_PROMPT, dấu backslash trong \neq hay \frac không phải
#     escape hợp lệ của JSON (\n, \t...) nên có thể khiến json.loads parse lỗi.
#     Chèn chung vào cả 3 system prompt để chặn cả 2 vấn đề từ gốc.
MATH_NOTATION_RULE = """
MATH NOTATION RULE — this is a FORMATTING rule only. It applies whenever you happen to write a
formula, in any language. It does NOT define your subject: you are not a math-only tutor, and you
help with every topic the student brings (cooking, sports, history, daily life, anything).
- NEVER use LaTeX or Markdown math syntax: no $...$, no $$...$$, no \\( \\) or \\[ \\], no backslash
  commands like \\frac, \\sqrt, \\neq, \\leq, \\geq, \\times, \\cdot, \\pi, and no code blocks for formulas.
- Write formulas as plain, readable text using normal Unicode characters instead:
  x², √2, π, ×, ÷, ≠, ≤, ≥, °, a₁, ½, etc.
- Example: write "ax² + bx + c = 0" (not "$$ax^2 + bx + c = 0$$"), and "a ≠ 0" (not "$a \\neq 0$").
"""

SYSTEM_PROMPT = f"""
You are an AI Tutor helping a student learn step by step, on ANY topic they bring to you.

STRICT RULES:
1. NEVER give the complete/final answer directly, even if the user asks for it directly or insists.
2. Instead, guide with a hint, a leading question, or reveal only a small piece of the concept at a time.
3. If the user's attempt is close to correct, confirm what's right and encourage them to continue, without revealing the rest.
4. If the user seems stuck, break the problem into a smaller, easier sub-question rather than solving it for them.
5. You have access to the full conversation history below (previous questions and your previous replies).
   Use it to stay consistent and to correctly recall anything the user or you mentioned earlier.
6. Keep responses concise (a few sentences), conversational, and encouraging.
7. EVERY topic the user raises is a valid learning topic — cooking, sports, games, daily life, anything.
   NEVER refuse a question, NEVER say a topic is outside your purpose or unrelated to studying, and NEVER
   tell the user to look it up elsewhere. There is no such thing as an off-topic question here.
8. Rule 7 does NOT weaken rules 1-4: engage with the topic using exactly the same guiding style.
   For "how do I make sushi?", start guiding them through it with a hint or a leading question —
   just as you would for any other topic. Answer in the same language the user writes in.
{MATH_NOTATION_RULE}"""

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

【数式の書き方 / Quy tắc viết công thức】
- $...$ や $$...$$、\\( \\) \\[ \\]、\\frac, \\sqrt, \\neq, \\leq, \\geq, \\times, \\cdot, \\pi のような
  LaTeX/Markdown記法は絶対に使わないこと(画面はプレーンテキスト表示で、記号がそのまま
  未変換のまま表示されてしまうため)。
- 代わりに、読みやすい通常のUnicode文字で書くこと: x², √2, π, ×, ÷, ≠, ≤, ≥, ° など。
  例)「$$ax^2+bx+c=0$$」ではなく「ax² + bx + c = 0」、「$a \\neq 0$」ではなく「a ≠ 0」。
- Không được dùng ký hiệu LaTeX/Markdown như $...$, $$...$$, \\( \\) \\[ \\], \\frac, \\sqrt,
  \\neq, \\leq, \\geq, \\times, \\cdot, \\pi (vì màn hình hiển thị dạng plain text, ký hiệu
  sẽ hiện nguyên văn chưa được render).
- Thay vào đó hãy viết bằng ký tự Unicode thông thường, dễ đọc: x², √2, π, ×, ÷, ≠, ≤, ≥, °...

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
NODE_SUMMARY_SYSTEM_PROMPT = (
    """
You are summarizing a tutoring conversation into a permanent study note for the student.

Based on the conversation so far, write a concise study note capturing what the student learned.

OUTPUT FORMAT (STRICT):
- Line 1: a short title (a few words, no trailing punctuation)
- From line 2 onward: a concise explanation of the concept, written for the student's own future review

Do not include any preamble, meta-commentary, or markdown formatting.
"""
    + MATH_NOTATION_RULE
)

NEEDS_AI_ANSWER = {"ANSWER", "REQUEST_CHANGE_METHOD"}
SESSION_NODE_TITLE_MAX_LEN = 255
# JA: セッション名が未指定かつノードにも紐づかない(フリーチャット)場合の既定名。
#     ChatSession.title のモデル既定値と揃えること。
# VI: Tên mặc định khi không chỉ định tên và cũng không gắn node (chat tự do).
#     Phải khớp với giá trị mặc định của model ChatSession.title.
DEFAULT_SESSION_TITLE = "New Chat Session"
# JA: フリーチャットの最初のメッセージからセッション名を作る時の最大文字数。
# VI: Độ dài tối đa khi tạo tên session từ tin nhắn đầu tiên của chat tự do.
FIRST_MESSAGE_TITLE_MAX_LEN = 30
# JA: 分岐推定でAIに見せる過去質問1件あたりの最大文字数 / VI: Độ dài tối đa mỗi câu hỏi cũ đưa cho AI
NODE_TOPIC_MAX_LEN = 100
# JA: AIに渡す会話履歴の最大件数と1件あたりの最大文字数（トークン節約）
# VI: Số lượng và độ dài tối đa của lịch sử hội thoại đưa cho AI (tiết kiệm token)
MAX_HISTORY_MESSAGES = 20
HISTORY_MESSAGE_MAX_LEN = 600


def _session_title_for_node(node) -> str:
    """
    JA: セッション名をノード名から組み立てる。「木から復習を始めた時」
        (create_chat_session_for_node)と「フリーチャットが完了してノードが
        生まれた時」(create_knowledge_node_from_session)の両方で使う
        唯一の命名規則にする。ここが2箇所でズレると、タイムログ上で
        同じノードのセッションなのに名前が違う、という状態が起きる。
    VI: Ghép tên session từ tên node. Dùng làm quy tắc đặt tên duy nhất cho cả
        2 trường hợp: "bắt đầu ôn tập từ cây" (create_chat_session_for_node)
        và "chat tự do hoàn thành, sinh ra node" (create_knowledge_node_from_session).
        Nếu 2 nơi này lệch nhau thì trên nhật ký thời gian sẽ có tình trạng
        cùng 1 node nhưng tên session khác nhau.
    """
    return f"学習: {node.title}"


def _title_from_first_message(text: str) -> str:
    """
    JA: フリーチャットの最初のメッセージからセッション名を作る。完了(知識ノード化)を
        待たずに、送った瞬間からタイムログ上で見分けが付くようにするため
        (完了しないまま終わったセッションはずっと既定名のままになっていた不具合の修正)。
        AI要約は使わない(応答を待たせたくない・要約コストをかけたくない)ので、
        本文の先頭を短く切り詰めるだけの単純な規則にする。完了時は
        _session_title_for_node による「学習: <ノード名>」が上書きするので、
        ここでの名前は「完了するまでの仮の名前」という位置づけ。
    VI: Tạo tên session từ tin nhắn đầu tiên của chat tự do. Để nhận ra được trên
        nhật ký thời gian ngay từ lúc gửi, không cần đợi hoàn thành (thành knowledge node)
        (sửa lỗi session bị bỏ dở giữa chừng thì mãi mãi giữ tên mặc định).
        Không dùng AI tóm tắt (không muốn làm chậm phản hồi / tốn chi phí), nên chỉ cắt
        ngắn phần đầu nội dung theo quy tắc đơn giản. Khi hoàn thành thì tên "学習: <tên node>"
        từ _session_title_for_node sẽ ghi đè, nên tên ở đây chỉ là "tên tạm cho tới khi hoàn thành".
    """
    stripped = text.strip()
    if len(stripped) <= FIRST_MESSAGE_TITLE_MAX_LEN:
        return stripped
    return stripped[:FIRST_MESSAGE_TITLE_MAX_LEN].rstrip() + "…"


def create_chat_session_for_node(*, user, node_id=None, title: str | None = None) -> ChatSession:
    # JA: 他アプリ所有のKnowledgeNodeは、所有権チェック込みの窓口経由で取得する
    #     (CONVENTIONS.md §10)。直接 objects.filter(id=...) で引くと、他人のノードに
    #     自分のセッションを紐付けられてしまう。
    # VI: KnowledgeNode thuộc app khác nên phải lấy qua cửa ngõ có kiểm tra quyền sở hữu
    #     (CONVENTIONS.md §10). Nếu tự query objects.filter(id=...) thì user có thể gắn
    #     session của mình vào node của người khác.
    #
    # JA: 【設計変更 2026-08-16】title の既定値を None にした。以前は "New Session" を
    #     番兵にして「未指定ならノード名から命名する」判定をしていたが、views 側が
    #     未指定時に "New Chat Session" を渡していたため番兵と一致せず、ノード由来の
    #     命名が一度も発火していなかった。結果、学習木から復習を始めたセッションが
    #     すべて "New Chat Session" になり、タイムログ上で見分けが付かなくなっていた。
    #     「未指定」は None で表し、既定値の決定はこの services に一本化する。
    # VI: 【Thay đổi thiết kế 2026-08-16】Đổi mặc định của title thành None. Trước đây dùng
    #     "New Session" làm sentinel để xét "chưa chỉ định thì đặt tên theo node", nhưng
    #     views lại truyền "New Chat Session" khi không chỉ định nên không khớp sentinel,
    #     khiến việc đặt tên theo node chưa từng chạy. Hệ quả: mọi phiên mở từ cây học tập
    #     đều tên "New Chat Session", không phân biệt được trên nhật ký thời gian.
    #     "Chưa chỉ định" biểu thị bằng None, và việc quyết định giá trị mặc định gom về services.
    from apps.topics import services as topics_services

    title = (title or "").strip()

    node = None
    if node_id:
        node = topics_services.get_owned_knowledge_node(user=user, node_id=node_id)

        existing = ChatSession.objects.filter(knowledge_node=node, user=user).first()
        if existing:
            return existing

        if not title:
            title = _session_title_for_node(node)

    return ChatSession.objects.create(
        user=user, knowledge_node=node, title=title or DEFAULT_SESSION_TITLE
    )


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
        ★【設計変更 2026-08-16】session.title もここでノード名から更新する。
        以前は knowledge_node の紐付けだけ行い title を放置していたため、
        フリーチャットから完了させたセッションはタイムログ上でずっと
        "New Chat Session"(フロントの既定名)のままだった。命名規則は
        _session_title_for_node に一本化してあるので、木から復習を始めた
        セッションと同じ "学習: <ノード名>" になる。
    VI: Được gọi khi một phiên chat tự do (chưa gắn knowledge_node) "hoàn
        thành". Nhờ AI tóm tắt hội thoại thành title/content, lưu thành một
        KnowledgeNode mới dưới Topic được chỉ định, và gắn 1:1 (OneToOne)
        với session này. Việc tạo KnowledgeNode được ủy thác qua services
        của app sở hữu (apps.topics), không gọi thẳng
        KnowledgeNode.objects.create từ app này.
        ★【Thay đổi thiết kế 2026-08-16】Cũng cập nhật session.title theo tên
        node ở đây. Trước đây chỉ gắn knowledge_node mà bỏ mặc title, nên
        session hoàn thành từ chat tự do mãi mãi giữ tên "New Chat Session"
        (tên mặc định của frontend) trên nhật ký thời gian. Quy tắc đặt tên
        đã gom về _session_title_for_node nên sẽ ra cùng dạng "学習: <tên node>"
        như session bắt đầu ôn tập từ cây.
        ★【設計変更 2026-08-17】完了ボタンの二重押下で2つのリクエストがほぼ同時に
        ここへ来ると、どちらも「session.knowledge_node_id はまだNone」という
        古い状態を見て、それぞれ別々にAIへ要約させ、別々のKnowledgeNodeを作って
        いた(呼び出し元のガードは呼び出し時点のsessionを見るだけで、実際に
        書き込む瞬間の状態は見ていないため)。結果、同じ会話から生まれた
        タイトルが同じノードが2つでき、片方だけがsessionに紐付いて、もう片方は
        どこからも辿れない「空っぽに見えるノード」として残ってしまっていた。
        ここを「knowledge_nodeがまだNoneの行にだけ書き込む」条件付きUPDATEに
        することで、後から来たリクエストは自分が作ったノードを破棄して、
        先に勝った方のノードをそのまま返すようにする。
    VI: Được gọi khi một phiên chat tự do (chưa gắn knowledge_node) "hoàn
        ★【Thay đổi thiết kế 2026-08-17】Khi bấm nút hoàn thành 2 lần liên tiếp,
        2 request gần như đồng thời tới đây đều thấy "session.knowledge_node_id
        vẫn còn None" (trạng thái cũ, vì điều kiện chặn ở nơi gọi chỉ xét session
        tại thời điểm gọi, không xét trạng thái thật lúc ghi), nên mỗi request tự
        nhờ AI tóm tắt riêng và tạo ra 2 KnowledgeNode khác nhau. Kết quả: 2 node
        cùng tên (từ cùng 1 hội thoại), chỉ 1 node được gắn vào session, node còn
        lại "trông như rỗng" vì không ai trỏ tới nó nữa. Đổi sang UPDATE có điều
        kiện (chỉ ghi vào dòng mà knowledge_node vẫn đang None) để request tới sau
        tự hủy node mình vừa tạo và trả về node của request đã thắng trước đó.
    """
    from apps.topics import services as topics_services

    topic = topics_services.get_owned_topic(user=user, topic_id=topic_id)
    title, content = _summarize_session_as_node(session)
    node = topics_services.create_knowledge_node(
        user=user, topic=topic, title=title, content=content
    )

    # JA: 「knowledge_nodeがまだNoneの行にだけ」書き込む条件付きUPDATE。
    #     このUPDATE文自体はDBが1回で処理するため、二重押下で2リクエストが
    #     同時に来ても、書き込みに成功するのはどちらか一方だけになる。
    # VI: UPDATE có điều kiện "chỉ ghi vào dòng mà knowledge_node vẫn còn None".
    #     Bản thân câu UPDATE được DB xử lý trong 1 lần, nên dù 2 request tới
    #     cùng lúc do bấm 2 lần, chỉ 1 trong 2 ghi thành công.
    claimed = ChatSession.objects.filter(id=session.id, knowledge_node__isnull=True).update(
        knowledge_node=node, title=_session_title_for_node(node)
    )
    if claimed == 0:
        # JA: 先に別のリクエストが確定させていた。自分が作ったノードは孤立するので
        #     削除し、既に確定している方のノードを返す(=見かけ上は何も起きない)。
        # VI: Request khác đã chốt trước rồi. Node mình vừa tạo sẽ mồ côi nên xóa đi,
        #     trả về node đã được chốt trước đó (nhìn bên ngoài như không có gì xảy ra).
        logger.warning(
            "[complete] knowledge_node重複作成を検出、孤立ノードを破棄: session=%s discarded_node=%s",
            session.id,
            node.id,
        )
        node.delete()
        session.refresh_from_db(fields=["knowledge_node", "title"])
        return session.knowledge_node

    session.knowledge_node = node
    session.title = _session_title_for_node(node)
    return node


def get_or_create_active_attempt(*, session: ChatSession) -> Attempt:
    """
    JA: ★【設計変更 2026-08-17】完了/ヒントボタンの二重押下で2リクエストがほぼ同時に
        来ると、どちらも「未完了のAttemptが無い」と判定して別々にAttemptを
        作ってしまっていた。Attemptモデルに追加した部分ユニーク制約
        (1セッションにつき未完了Attemptは1件まで)がDBレベルでこれを弾くので、
        後から来た方はIntegrityErrorを拾って、先に作られた1件に合流する。
        ★【設計変更 2026-08-17 その2】当初は「まずSELECTで探し、無ければCREATE」
        という順序だったが、これだと2リクエストが両方ともSELECTで「無い」と
        見た直後にCREATEし、片方がIntegrityErrorになるまでの間に矛盾した状態が
        生まれ得た(実機のPromise.all検証で、SQLiteは1文ごとにロックを取って
        すぐ解放するため、SELECTとCREATEの間に相手の書き込みが割り込めることを
        確認した)。SELECTを飛ばし、常にまずCREATEを試みてIntegrityErrorだけを
        「既にある」の判定に使う形にすることで、判定と作成が1つのSQL文(INSERT)に
        まとまり、割り込む隙が無くなる。
    VI: ★【Thay đổi thiết kế 2026-08-17】Khi bấm nút hoàn thành/gợi ý 2 lần liên
        tiếp, 2 request gần như đồng thời đều thấy "không có Attempt đang mở"
        nên mỗi bên tự tạo 1 Attempt riêng. Ràng buộc unique một phần vừa thêm
        vào model Attempt (mỗi session tối đa 1 Attempt chưa hoàn thành) chặn
        điều này ở mức DB; request tới sau bắt IntegrityError rồi dùng chung
        Attempt đã được tạo trước đó.
        ★【Thay đổi thiết kế 2026-08-17, phần 2】Ban đầu thứ tự là "SELECT tìm trước,
        không có thì CREATE", nhưng cách này để lại khe hở: cả 2 request đều SELECT
        thấy "không có" rồi mới CREATE, và trong khoảng giữa đó bên kia có thể chen
        vào (đã xác nhận bằng Promise.all trên server thật: SQLite khóa theo từng
        câu lệnh rồi nhả ngay, nên giữa SELECT và CREATE có kẽ hở cho request kia ghi
        vào). Bỏ SELECT, luôn thử CREATE trước và chỉ dùng IntegrityError để biết "đã
        có rồi", gộp việc kiểm tra + tạo thành 1 câu SQL (INSERT) duy nhất, không còn
        khe hở để chen vào.
    """
    try:
        return Attempt.objects.create(chat_session=session)
    except IntegrityError:
        return session.attempts.get(completed_at__isnull=True)


def claim_attempt_for_action(*, session: ChatSession, action_type: str) -> tuple[Attempt, bool]:
    """
    JA: ★【設計変更 2026-08-17】Attemptの確保と、COMPLETE時の「完了権」の確定だけを
        行う。SM-2の適用(apps.reviews.services.record_review_result)はここでは
        呼ばず、戻り値のwon_completionを見て呼び出し元が判断する。
        なぜ分離したか: 当初はこの処理を「知識ノード作成(AI要約、数秒かかる)」の
        後に呼んでいたが、二重押下で2リクエストがほぼ同時に来た場合、後続の
        リクエストがここへ来る頃には先行リクエストが既にAttemptの作成・完了・
        SM-2適用まで全部終えてしまっていることがあり(実際のrunserver上で
        Promise.allを使った同時送信で再現・確認済み)、「未完了のAttemptが無い」
        と正しく(しかし意図に反して)判断されて別のAttemptが新規作成され、
        SM-2が二重に適用されていた。AI呼び出しより前に、かつ軽量なDB操作だけで
        完結するこの部分を独立させることで、2リクエストの到達タイミングが近い
        うちに競合を検出できる時間窓を最大化する。
    VI: ★【Thay đổi thiết kế 2026-08-17】Chỉ đảm bảo có Attempt và chốt "quyền hoàn
        thành" khi COMPLETE. KHÔNG gọi SM-2 (apps.reviews.services.record_review_result)
        ở đây — bên gọi tự quyết định dựa vào won_completion trả về.
        Vì sao tách ra: trước đây gọi bước này SAU khi tạo knowledge node (tóm tắt
        bằng AI, mất vài giây); khi bấm 2 lần gần như đồng thời, tới lúc request
        sau chạy tới đây thì request trước có thể đã tạo, hoàn thành Attempt và áp
        dụng SM-2 xong xuôi rồi (đã tái hiện và xác nhận trên runserver thật bằng
        Promise.all gửi đồng thời) — khiến request sau thấy đúng (nhưng sai ý định)
        "không có Attempt đang mở" nên tạo Attempt mới và áp dụng SM-2 lần nữa.
        Tách phần thao tác DB nhẹ, không gọi AI, ra trước sẽ tối đa hóa khung thời
        gian để phát hiện xung đột khi 2 request tới gần nhau về thời điểm.
    """
    attempt = get_or_create_active_attempt(session=session)

    if action_type == "HINT":
        attempt.hint_count += 1
        attempt.save(update_fields=["hint_count"])
        return attempt, False

    if action_type == "COMPLETE":
        # JA: 「未完了の行にだけ」書き込む条件付きUPDATE。影響行数(updated)が0なら
        #     自分より先に誰かが完了させていたということなので、この呼び出しは
        #     「完了権」を得られなかった(won_completion=False)。
        # VI: UPDATE có điều kiện "chỉ ghi vào dòng chưa hoàn thành". Số dòng ảnh
        #     hưởng (updated) là 0 nghĩa là có ai đó đã hoàn thành trước, nên lần
        #     gọi này KHÔNG giành được "quyền hoàn thành" (won_completion=False).
        updated = Attempt.objects.filter(id=attempt.id, completed_at__isnull=True).update(
            completed_at=timezone.now()
        )
        if updated == 0:
            logger.warning(
                "[complete] Attempt二重完了を検出、SM-2の再適用をスキップ: attempt=%s", attempt.id
            )
            return attempt, False
        attempt.refresh_from_db(fields=["completed_at"])
        return attempt, True

    return attempt, False


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

    # JA: ★このメッセージがセッションの最初の1件かどうかを、他の書き込みが起きる前に
    #     判定しておく(下でuser_msg/ai_msgを作った後だと必ずFalseになってしまう)。
    # VI: ★Xét xem tin nhắn này có phải tin đầu tiên của session không, trước khi có
    #     ghi nào khác xảy ra (nếu xét sau khi đã tạo user_msg/ai_msg thì luôn ra False).
    is_first_message = not session.messages.exists()

    # JA: ★Attemptの確保と「完了権」の確定は、AI呼び出し(要約・ヒント生成)より
    #     必ず先に行う。理由は claim_attempt_for_action のdocstring参照
    #     (二重押下対策として、競合を検出できる時間窓を最大化するため)。
    # VI: ★Đảm bảo có Attempt và chốt "quyền hoàn thành" LUÔN thực hiện trước khi
    #     gọi AI (tóm tắt/sinh gợi ý). Lý do xem docstring của claim_attempt_for_action
    #     (chống bấm 2 lần bằng cách tối đa hóa khung thời gian phát hiện xung đột).
    attempt = None
    won_completion = False
    if action_type in ("HINT", "COMPLETE"):
        attempt, won_completion = claim_attempt_for_action(session=session, action_type=action_type)

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

    # JA: ★「完了権」を得たリクエストだけがSM-2を適用する(二重押下対策)。
    # VI: ★Chỉ request giành được "quyền hoàn thành" mới áp dụng SM-2 (chống bấm 2 lần).
    if action_type == "COMPLETE" and won_completion:
        from apps.reviews.services import record_review_result

        record_review_result(attempt, bool(understood))

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

        # JA: ★フリーチャット(knowledge_node未設定)の最初のメッセージなら、
        #     完了(知識ノード化)を待たずに本文からセッション名を付ける。
        #     node紐付き(復習チャット)や、既に命名済みのセッションは対象外。
        # VI: ★Nếu là tin nhắn đầu tiên của chat tự do (chưa gắn knowledge_node),
        #     đặt tên session từ nội dung mà không cần đợi hoàn thành (thành node).
        #     Không áp dụng cho session đã gắn node (chat ôn tập) hay đã có tên riêng.
        if (
            is_first_message
            and session.knowledge_node_id is None
            and session.title == DEFAULT_SESSION_TITLE
        ):
            session.title = _title_from_first_message(text)
            session.save(update_fields=["title"])

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
