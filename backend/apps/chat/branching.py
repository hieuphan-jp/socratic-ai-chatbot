"""
apps/chat/branching.py

JA: 「この新しい質問は、過去のどのステップから派生したのか」を、AIを呼ばずに推定する。
    文字bigram(2文字の並び)のコサイン類似度で測る。日本語・ベトナム語ともに
    形態素解析器なしで動き、外部ライブラリも不要、実行は数ミリ秒でAPIコストは0。

    ★なぜ文字bigramか: 日本語は英語と違い単語が空白で区切られていないため、
      単語単位の一致を取るには形態素解析器(MeCab等)が要る。文字を2文字ずつ
      ずらして数える方式なら解析器なしで「語彙の重なり」を近似できる。
      例) 「三平方の定理」→ 三平/平方/方の/の定/定理

    ★IDF重み付け: 「です」「ます」「して」のような助詞・語尾のbigramはどの文にも
      出るため、そのまま数えるとノイズになる。候補全体での出現率が高いbigramの
      重みを下げる(IDF)ことで、その話題に固有の語だけが効くようにする。

    ★判定ルール: 単に類似度が最大の候補を選ぶのではなく、「直前のステップよりも
      明確に古いステップの方が似ている」場合だけ分岐とみなす。そうしないと自然な
      会話の続き(直前の話題の深掘り)まで分岐扱いになってしまう。
VI: Đoán "câu hỏi mới này rẽ nhánh từ bước cũ nào" mà KHÔNG gọi AI.
    Đo bằng cosine similarity của bigram ký tự (2 ký tự liền nhau). Chạy được cho cả
    tiếng Nhật lẫn tiếng Việt mà không cần bộ tách từ, không cần thư viện ngoài,
    chạy trong vài mili giây và tốn 0 chi phí API.

    ★Vì sao dùng bigram ký tự: tiếng Nhật không tách từ bằng khoảng trắng nên muốn so
      khớp theo từ thì phải có bộ phân tích hình thái (MeCab...). Đếm theo cặp 2 ký tự
      trượt dần thì xấp xỉ được "độ trùng từ vựng" mà không cần bộ phân tích.

    ★Trọng số IDF: các bigram của trợ từ/đuôi câu ("です", "ます"...) xuất hiện ở mọi câu
      nên nếu đếm thẳng sẽ thành nhiễu. Giảm trọng số các bigram xuất hiện ở nhiều câu
      (IDF) để chỉ còn từ đặc trưng của chủ đề có tác dụng.

    ★Quy tắc phán đoán: không chỉ chọn ứng viên có similarity cao nhất, mà chỉ coi là rẽ
      nhánh khi "bước CŨ giống rõ rệt hơn bước LIỀN TRƯỚC". Nếu không, việc đào sâu tự
      nhiên chủ đề ngay trước đó cũng sẽ bị coi nhầm là rẽ nhánh.
"""

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

# JA: 分岐とみなす最低類似度。これ未満なら「どの過去ステップとも似ていない」と判断する。
# VI: Ngưỡng similarity tối thiểu để coi là rẽ nhánh. Dưới mức này coi như không giống bước cũ nào.
MIN_SCORE = 0.15

# JA: 直前ステップとの類似度に対して、どれだけ上回れば「出戻り」とみなすか。
#     この差が小さいと、単なる話題の継続を分岐と誤判定してしまう。
# VI: Cần vượt similarity của bước liền trước bao nhiêu thì coi là "quay lại bước cũ".
#     Nếu chênh lệch nhỏ thì sẽ nhầm việc tiếp nối chủ đề thành rẽ nhánh.
MIN_MARGIN = 0.05

# JA: 確信度をhighにする差。分岐確認UIを出すかどうかの分かれ目になる。
# VI: Mức chênh để đặt confidence = high, quyết định có hiện UI xác nhận rẽ nhánh hay không.
HIGH_CONFIDENCE_MARGIN = 0.15

# JA: 記号・空白はノイズなので落とす(日本語/ベトナム語の文字と英数字だけ残す)。
# VI: Bỏ ký hiệu và khoảng trắng (chỉ giữ chữ cái tiếng Nhật/Việt và chữ số).
_NON_WORD = re.compile(r"[^0-9a-zà-ỹ぀-ヿ一-鿿]+", re.IGNORECASE)

# JA: ★話題と無関係な定型表現(依頼・丁寧語・つなぎ)を先に落とす。
#     これを消さないと「〜てください」同士が一致するだけで分岐と誤判定してしまう
#     (実測: 話題が全く違う2文が語尾だけで score 0.15 に達した)。
#     IDFでも下げられるが、候補が数件だと統計が効かないため明示的に除去する。
# VI: ★Loại trước các cụm cố định không liên quan chủ đề (nhờ vả, kính ngữ, từ nối).
#     Không bỏ thì hai câu chỉ vì cùng đuôi "〜てください" đã bị coi là rẽ nhánh
#     (đo thực tế: 2 câu khác hẳn chủ đề vẫn đạt score 0.15 chỉ nhờ đuôi câu).
#     IDF cũng hạ được trọng số nhưng khi chỉ có vài ứng viên thì thống kê không đủ,
#     nên loại bỏ tường minh.
_FILLER = re.compile(
    r"(について|につきまして|に関して|を教えて|教えて|知りたい|ください|下さい|お願いします|"
    r"おねがいします|でしょうか|ですか|ますか|したいです|たいです|なりますか|でしょう|"
    r"もう一度|もういちど|について詳しく|詳しく|説明して|"
    r"cho tôi|cho mình|giúp tôi|giúp mình|hãy|như thế nào|làm sao|là gì|"
    r"mình muốn|tôi muốn|giải thích|một lần nữa)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BranchSuggestion:
    """JA: 分岐推定の結果 / VI: Kết quả đoán rẽ nhánh"""

    parent_id: str
    score: float
    # JA: 直前ステップとの類似度の差。大きいほど「明確な出戻り」。
    # VI: Chênh lệch so với bước liền trước. Càng lớn thì càng rõ là quay lại bước cũ.
    margin: float
    confidence: str  # "high" | "low"


def normalize(text: str) -> str:
    """
    JA: 全角/半角・大文字小文字の揺れを吸収し、定型表現・記号・空白を落とす。
        残るのは実質的に内容語だけになる。
    VI: Chuẩn hóa full-width/half-width, hoa/thường; bỏ cụm cố định, ký hiệu và khoảng trắng.
        Phần còn lại về cơ bản chỉ là từ mang nội dung.
    """
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = _FILLER.sub("", text)
    return _NON_WORD.sub("", text)


def bigrams(text: str) -> Counter:
    """
    JA: 正規化済みテキストから文字bigramを数える。1文字しかない場合はその文字自身を返す
        (短い入力でも空にならないようにするため)。
    VI: Đếm bigram ký tự từ text đã chuẩn hóa. Nếu chỉ có 1 ký tự thì trả về chính ký tự đó
        (để đầu vào ngắn không bị rỗng).
    """
    normalized = normalize(text)
    if len(normalized) < 2:
        return Counter([normalized] if normalized else [])
    return Counter(normalized[i : i + 2] for i in range(len(normalized) - 1))


def _idf(documents: list[Counter]) -> dict[str, float]:
    """
    JA: 候補群の中での「珍しさ」を計算する。多くの候補に出るbigramほど重みが下がる。
    VI: Tính "độ hiếm" trong tập ứng viên. Bigram xuất hiện ở càng nhiều ứng viên thì trọng số càng thấp.
    """
    total = len(documents)
    if total == 0:
        return {}
    document_frequency: Counter = Counter()
    for document in documents:
        document_frequency.update(document.keys())
    return {
        gram: math.log((total + 1) / (freq + 1)) + 1.0 for gram, freq in document_frequency.items()
    }


def _cosine(a: Counter, b: Counter, idf: dict[str, float]) -> float:
    """JA: IDF重み付きコサイン類似度 / VI: Cosine similarity có trọng số IDF"""
    if not a or not b:
        return 0.0

    shared = set(a) & set(b)
    dot = sum(a[gram] * b[gram] * (idf.get(gram, 1.0) ** 2) for gram in shared)
    if dot == 0.0:
        return 0.0

    norm_a = math.sqrt(sum((count * idf.get(gram, 1.0)) ** 2 for gram, count in a.items()))
    norm_b = math.sqrt(sum((count * idf.get(gram, 1.0)) ** 2 for gram, count in b.items()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def should_adopt(suggestion: BranchSuggestion | None) -> bool:
    """
    JA: 推定結果を実際に親ノードとして採用してよいかを判断する。
        確信度が high のものだけ採用し、low は「候補ではあるが採用しない」とする。
        low を採用すると、誤検知(共通語だけで似ていると判定されたケース)が
        そのまま思考ツリーの形を壊してしまうため。
    VI: Quyết định có thực sự dùng kết quả đoán làm node cha hay không.
        Chỉ nhận khi confidence là high; mức low coi như "có ứng viên nhưng không dùng".
        Nếu nhận cả mức low thì các ca nhận nhầm (chỉ giống nhau ở từ chung)
        sẽ làm hỏng hình dạng của cây tư duy.
    """
    return suggestion is not None and suggestion.confidence == "high"


def suggest_parent(*, new_text: str, candidates: list[tuple[str, str]]) -> BranchSuggestion | None:
    """
    JA: 新しい質問が、過去のどのステップから派生したかを推定する。
        candidates は (id, text) を古い順に並べたもの。末尾が「直前のステップ」。
        分岐と判断できない場合は None を返す(=直前の続きとして扱ってよい)。
    VI: Đoán câu hỏi mới rẽ nhánh từ bước cũ nào.
        candidates là danh sách (id, text) từ cũ đến mới; phần tử cuối là "bước liền trước".
        Nếu không đủ căn cứ để coi là rẽ nhánh thì trả None (coi như tiếp nối bước liền trước).
    """
    # JA: 直前1件しかないなら「出戻り先」が存在しない。
    # VI: Nếu chỉ có 1 ứng viên thì không tồn tại "bước cũ để quay lại".
    if len(candidates) < 2:
        return None

    new_vector = bigrams(new_text)
    if not new_vector:
        return None

    candidate_vectors = [bigrams(text) for _, text in candidates]
    idf = _idf([new_vector, *candidate_vectors])

    # JA: 末尾(直前)は「自然な続き」の基準線として使い、出戻り候補からは外す。
    # VI: Phần tử cuối (liền trước) dùng làm đường cơ sở "tiếp nối tự nhiên", không tính là ứng viên quay lại.
    previous_score = _cosine(new_vector, candidate_vectors[-1], idf)

    best_id: str | None = None
    best_score = 0.0
    for (candidate_id, _), vector in zip(candidates[:-1], candidate_vectors[:-1], strict=True):
        score = _cosine(new_vector, vector, idf)
        if score > best_score:
            best_score = score
            best_id = candidate_id

    if best_id is None or best_score < MIN_SCORE:
        return None

    margin = best_score - previous_score
    if margin < MIN_MARGIN:
        return None

    return BranchSuggestion(
        parent_id=best_id,
        score=round(best_score, 4),
        margin=round(margin, 4),
        confidence="high" if margin >= HIGH_CONFIDENCE_MARGIN else "low",
    )
