"""
apps/chat/steps.py

JA: 思考ツリーの「ステップ」に関する純ロジック(AI呼び出しなし)。
    1) is_trivial_message … 相槌や極端に短い発言を、AIに問い合わせる前に足切りする。
       「そうですね」のような発言までノード化されていた問題への直接の対策であり、
       同時にAI呼び出しの中身を軽くする(判定用の重いプロンプトを積まずに済む)。
    2) build_step_labels … 幹/枝の木構造から 1, 2, 3, 3-1, 3-2 という番号を採番する。
       以前はフロントが「USER発言の時系列の通し番号」を振っていたため、
       枝に分かれても番号が連番のままで、番号とノードの位置が食い違っていた。
       木を辿って採番すれば構造と番号が必ず一致する。
VI: Logic thuần về "bước" của cây tư duy (không gọi AI).
    1) is_trivial_message … lọc bỏ câu đệm/phát ngôn quá ngắn TRƯỚC khi hỏi AI.
       Đây là cách xử lý trực tiếp việc "そうですね" cũng bị thành node, đồng thời
       làm nhẹ lần gọi AI (không phải nhồi prompt phán đoán nặng).
    2) build_step_labels … đánh số 1, 2, 3, 3-1, 3-2 từ cấu trúc cây thân/nhánh.
       Trước đây frontend đánh số tuần tự theo thời gian của phát ngôn USER nên khi rẽ
       nhánh, số vẫn chạy liên tiếp, khiến số và vị trí node không khớp.
       Duyệt cây để đánh số thì cấu trúc và số luôn khớp nhau.
"""

import re
import unicodedata
from collections import defaultdict

# JA: これ未満の文字数は、それだけで内容のある質問とはみなさない。
# VI: Ngắn hơn số ký tự này thì tự nó không được coi là câu hỏi có nội dung.
MIN_STEP_TEXT_LENGTH = 8

# JA: 相槌・同意・お礼など、それ自体は学習の前進を表さない定型表現。
#     完全一致(正規化後)で判定するため、「なるほど、では次に〜」のような
#     内容を伴う発言は足切りされない。
# VI: Các cụm cố định như đệm lời, đồng ý, cảm ơn — tự chúng không thể hiện tiến triển học tập.
#     So khớp bằng cách khớp toàn bộ (sau chuẩn hóa) nên câu có nội dung như
#     "なるほど、では次に〜" sẽ không bị lọc.
AIZUCHI = {
    # 日本語 / Tiếng Nhật
    "はい",
    "いいえ",
    "うん",
    "ええ",
    "そうです",
    "そうですね",
    "そうなんですね",
    "なるほど",
    "なるほどです",
    "わかりました",
    "わかった",
    "りょうかい",
    "了解",
    "了解です",
    "ありがとう",
    "ありがとうございます",
    "おねがいします",
    "おっけー",
    "ok",
    "okです",
    "はいそうです",
    "つづけて",
    "続けて",
    "もっと",
    # ベトナム語 / Tiếng Việt
    "vâng",
    "dạ",
    "ừ",
    "đúng rồi",
    "hiểu rồi",
    "cảm ơn",
    "cám ơn",
    "được",
    "tiếp tục",
    "okie",
}

_NON_WORD = re.compile(r"[^0-9a-zà-ỹ぀-ヿ一-鿿]+", re.IGNORECASE)


def _normalize(text: str) -> str:
    return _NON_WORD.sub("", unicodedata.normalize("NFKC", text or "").lower())


def is_trivial_message(text: str) -> bool:
    """
    JA: 「ステップとして記録するに値しない発言」かどうかを、AIを使わず判定する。
        判定を誤ってステップを作らないよりは、作ってしまう方が害が小さいので、
        明確な相槌と極端に短い発言だけを落とす(保守的な足切り)。
    VI: Phán đoán "phát ngôn không đáng ghi thành bước" mà không dùng AI.
        Bỏ sót (vẫn tạo bước) ít hại hơn là loại nhầm, nên chỉ lọc các câu đệm rõ ràng
        và phát ngôn cực ngắn (lọc theo hướng thận trọng).
    """
    normalized = _normalize(text)
    if not normalized:
        return True
    if normalized in AIZUCHI:
        return True
    # JA: 疑問符があれば、短くても質問として扱う(「なぜ?」など)。
    # VI: Nếu có dấu hỏi thì dù ngắn vẫn coi là câu hỏi (vd "なぜ?").
    if "?" in text or "？" in text:
        return False
    return len(normalized) < MIN_STEP_TEXT_LENGTH


# JA: ノードに出すタイトルの最大長。長いと木が読みづらくなる。
# VI: Độ dài tối đa của tiêu đề trên node. Dài quá thì cây khó đọc.
MAX_TITLE_LENGTH = 24

# JA: 文末の助詞・敬語だけを落として体言止めに寄せる(ルールベースの簡易整形)。
# VI: Bỏ trợ từ/kính ngữ ở cuối câu để đưa về dạng danh từ (chỉnh sửa đơn giản theo luật).
_TITLE_TAIL = re.compile(
    r"(について(教えて)?(ください)?|を教えて(ください)?|とは(何ですか|なんですか)?|"
    r"を知りたい(です)?|はどう(なりますか|やって|すれば)?|"
    r"ですか|でしょうか|ますか|してください|お願いします|教えて)\s*[?？。．.]*$"
)


def clean_title(title: str) -> str:
    """
    JA: AIが返したタイトルを表示用に整える(前後の記号除去・長さ制限)。
    VI: Chỉnh tiêu đề AI trả về cho phù hợp hiển thị (bỏ ký hiệu thừa, giới hạn độ dài).
    """
    cleaned = (title or "").strip().strip("「」\"'`　 ")
    return cleaned[:MAX_TITLE_LENGTH]


def fallback_title(text: str) -> str:
    """
    JA: AIがタイトルを返さなかった/返せなかったときの代替。AI呼び出しを増やさずに、
        1文目を取り出して文末表現を削るだけの簡易整形で見出しらしくする。
    VI: Phương án thay thế khi AI không trả (hoặc không trả được) tiêu đề. Không gọi thêm AI,
        chỉ lấy câu đầu và cắt phần đuôi câu để trông giống một tiêu đề.
    """
    first_sentence = re.split(r"[。．.\n?？!！]", (text or "").strip())[0].strip()
    if not first_sentence:
        return clean_title(text)
    return clean_title(_TITLE_TAIL.sub("", first_sentence) or first_sentence)


def build_step_labels(step_messages: list) -> dict:
    """
    JA: 幹(TRUNK)と枝(BRANCH)の木から、表示用の番号を採番して {id: "3-1"} を返す。
        - TRUNK は常に最上位。時系列順に 1, 2, 3...
        - BRANCH は親の番号に連ねる。3の下に付けば 3-1, 3-2...
        - 枝の下の枝も同様に 3-1-1 と伸ばす。
        - 親が見つからない BRANCH は、木から外れないよう最上位として扱う。
        step_messages には step_kind が NONE でないメッセージを時系列順で渡すこと。
    VI: Từ cây thân (TRUNK) và nhánh (BRANCH), đánh số hiển thị và trả về {id: "3-1"}.
        - TRUNK luôn ở cấp cao nhất, đánh 1, 2, 3... theo thứ tự thời gian.
        - BRANCH nối theo số của cha: nằm dưới 3 thì thành 3-1, 3-2...
        - Nhánh của nhánh cũng kéo dài tương tự: 3-1-1.
        - BRANCH không tìm được cha thì coi như cấp cao nhất để không rơi khỏi cây.
        Truyền vào step_messages các tin nhắn có step_kind khác NONE, theo thứ tự thời gian.
    """
    step_ids = {message.id for message in step_messages}

    roots = []
    children = defaultdict(list)
    for message in step_messages:
        parent_id = message.parent_message_id
        is_branch = message.step_kind == "BRANCH" and parent_id in step_ids
        if is_branch:
            children[parent_id].append(message)
        else:
            roots.append(message)

    labels: dict = {}

    def walk(nodes: list, prefix: str) -> None:
        for index, node in enumerate(nodes, start=1):
            label = f"{prefix}-{index}" if prefix else str(index)
            labels[node.id] = label
            walk(children.get(node.id, []), label)

    walk(roots, "")
    return labels
