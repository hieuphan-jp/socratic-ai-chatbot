"""
apps/chat/management/commands/eval_branching.py

JA: 文字bigramによる分岐推定(apps/chat/branching.py)が実際どれくらい当たるかを、
    AIを一切呼ばずに確認するための評価コマンド。
    --demo   … 用意したサンプル会話で挙動を見る(DBもAPIキーも不要)
    (既定)   … DBの実セッションを再生し、各発言に対する推定結果を表示する
    実行例:
      python manage.py eval_branching --demo
      python manage.py eval_branching
      python manage.py eval_branching --session <UUID>
VI: Lệnh đánh giá xem việc đoán nhánh bằng bigram ký tự (apps/chat/branching.py) chính xác
    tới đâu, KHÔNG gọi AI.
    --demo   … xem hành vi trên hội thoại mẫu có sẵn (không cần DB lẫn API key)
    (mặc định) … phát lại các session thật trong DB, hiển thị kết quả đoán cho từng phát ngôn
"""

from django.core.management.base import BaseCommand

from apps.chat import branching
from apps.chat.models import ChatMessage, ChatSession

# JA: サンプル会話。「期待する親」を書いておき、推定が一致するかを見る。
#     None = 分岐なし(直前の続き)が正解。
# VI: Hội thoại mẫu. Ghi sẵn "node cha mong đợi" để xem kết quả đoán có khớp không.
#     None = đáp án đúng là không rẽ nhánh (tiếp nối bước liền trước).
DEMO_CONVERSATIONS: list[dict] = [
    {
        "name": "話題を戻すケース / Quay lại chủ đề cũ",
        "messages": [
            "三平方の定理について教えてください",
            "直角三角形の斜辺はどう求めますか",
            "円の面積の公式を知りたいです",
            "さっきの三平方の定理の証明も教えてください",
        ],
        "expected": [None, None, None, 0],
    },
    {
        "name": "自然な深掘り(分岐しない) / Đào sâu tự nhiên (không rẽ nhánh)",
        "messages": [
            "二次方程式の解き方を教えてください",
            "判別式とは何ですか",
            "判別式が negative のときはどうなりますか",
        ],
        "expected": [None, None, None],
    },
    {
        "name": "相槌(ステップにすべきでない) / Câu đệm (không nên thành bước)",
        "messages": [
            "微分の基本を教えてください",
            "積分との関係は何ですか",
            "そうですね",
        ],
        "expected": [None, None, None],
    },
    {
        "name": "3つ目の話題から1つ目へ戻る / Từ chủ đề thứ 3 quay về chủ đề đầu",
        "messages": [
            "Pythonのリスト内包表記について",
            "ジェネレータ式との違いは",
            "デコレータの書き方を教えて",
            "リスト内包表記のネストはどう書きますか",
        ],
        "expected": [None, None, None, 0],
    },
    # --- ここから下は「文字bigramが原理的に苦手」な想定ケース ---
    # --- Từ đây trở xuống là các ca mà bigram ký tự vốn dĩ không xử lý tốt ---
    {
        "name": "【難】語彙が重ならない参照 / [Khó] Tham chiếu không trùng từ vựng",
        "messages": [
            "三平方の定理について教えてください",
            "円の面積の公式を知りたいです",
            "さっきのやつをもう一度説明してください",
        ],
        # JA: 人間なら「さっきのやつ」=三平方の定理 と分かるが、共通する文字が無い。
        # VI: Người đọc hiểu "cái lúc nãy" = định lý Pythagoras, nhưng không có ký tự chung.
        "expected": [None, None, 0],
    },
    {
        "name": "【難】言い換え・同義語 / [Khó] Diễn đạt lại, từ đồng nghĩa",
        "messages": [
            "微分の基本を教えてください",
            "行列の掛け算について知りたいです",
            "接線の傾きの求め方をもう一度お願いします",
        ],
        # JA: 「微分」と「接線の傾き」は同じ話題だが文字は共有しない。
        # VI: "Đạo hàm" và "độ dốc tiếp tuyến" cùng chủ đề nhưng không chung ký tự.
        "expected": [None, None, 0],
    },
    {
        "name": "【難】共通語による誤検知の誘い / [Khó] Dễ nhận nhầm do từ chung",
        "messages": [
            "二次方程式の解き方を教えてください",
            "一次方程式との違いは何ですか",
            "連立方程式はどう解きますか",
        ],
        # JA: 「方程式」が全部に出るので誤って古いノードへ分岐しやすい。
        #     正解は「直前の続き」(分岐なし)。
        # VI: "Phương trình" xuất hiện ở mọi câu nên dễ rẽ nhầm về node cũ.
        #     Đáp án đúng là tiếp nối câu liền trước (không rẽ nhánh).
        "expected": [None, None, None],
    },
]


class Command(BaseCommand):
    help = (
        "文字bigramによる分岐推定の精度を確認する / "
        "Kiểm tra độ chính xác của việc đoán nhánh bằng bigram ký tự"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--demo",
            action="store_true",
            help="サンプル会話で評価する(DB不要) / Đánh giá trên hội thoại mẫu (không cần DB)",
        )
        parser.add_argument(
            "--session",
            type=str,
            default=None,
            help="特定のセッションIDだけ評価する / Chỉ đánh giá 1 session ID cụ thể",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            f"閾値 / Ngưỡng: MIN_SCORE={branching.MIN_SCORE} "
            f"MIN_MARGIN={branching.MIN_MARGIN} "
            f"HIGH_CONFIDENCE_MARGIN={branching.HIGH_CONFIDENCE_MARGIN}\n"
        )
        if options["demo"]:
            self._run_demo()
        else:
            self._run_on_database(session_id=options["session"])

    def _run_demo(self) -> None:
        total = 0
        correct = 0

        for conversation in DEMO_CONVERSATIONS:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n■ {conversation['name']}"))
            messages = conversation["messages"]
            expected = conversation["expected"]

            for index, text in enumerate(messages):
                # JA: 「その発言時点で存在した過去の発言」だけを候補にする(実運用と同条件)。
                # VI: Chỉ lấy các phát ngôn đã tồn tại tại thời điểm đó làm ứng viên (giống thực tế).
                candidates = [(str(i), messages[i]) for i in range(index)]
                suggestion = branching.suggest_parent(new_text=text, candidates=candidates)

                # JA: 実際にservices側で採用される判断(confidence=highのみ)で正誤を測る。
                #     生の候補ではなく「本番で何が起きるか」を評価しないと意味がない。
                # VI: Chấm đúng/sai theo quyết định thực sự được services dùng (chỉ confidence=high).
                #     Phải đánh giá "điều gì xảy ra khi chạy thật", không phải ứng viên thô.
                adopted = branching.should_adopt(suggestion)
                expected_index = expected[index]
                actual_index = int(suggestion.parent_id) if adopted else None
                is_correct = actual_index == expected_index

                total += 1
                correct += int(is_correct)

                mark = self.style.SUCCESS("OK ") if is_correct else self.style.ERROR("NG ")
                self.stdout.write(f"  {mark}[{index}] {text}")
                self.stdout.write(
                    f"       期待 / Mong đợi : {self._describe(expected_index, messages)}"
                )
                if suggestion:
                    verdict = "採用 / dùng" if adopted else "不採用(low) / bỏ qua (low)"
                    raw = self._describe(int(suggestion.parent_id), messages)
                    self.stdout.write(
                        f"       推定 / Đoán được: {raw} "
                        f"(score={suggestion.score} margin={suggestion.margin} "
                        f"confidence={suggestion.confidence} → {verdict})"
                    )
                else:
                    self.stdout.write("       推定 / Đoán được: 分岐なし / không rẽ nhánh")

        rate = (correct / total * 100) if total else 0.0
        self.stdout.write(self.style.SUCCESS(f"\n正解 / Đúng: {correct}/{total} ({rate:.1f}%)"))

    def _describe(self, index: int | None, messages: list[str]) -> str:
        if index is None:
            return "分岐なし / không rẽ nhánh"
        return f"[{index}] {messages[index]}"

    def _run_on_database(self, *, session_id: str | None) -> None:
        sessions = ChatSession.objects.all().order_by("created_at")
        if session_id:
            sessions = sessions.filter(id=session_id)

        evaluated = 0
        for session in sessions:
            user_messages = list(
                session.messages.filter(sender=ChatMessage.Sender.USER).order_by("created_at")
            )
            # JA: 出戻り先が存在しない短いセッションは評価対象にしない。
            # VI: Session quá ngắn (không có bước cũ để quay lại) thì bỏ qua.
            if len(user_messages) < 3:
                continue

            evaluated += 1
            self.stdout.write(
                self.style.MIGRATE_HEADING(f"\n■ session={session.id} title={session.title}")
            )

            for index, message in enumerate(user_messages):
                if index < 2:
                    self.stdout.write(f"  -  [{index}] {message.message_text[:60]}")
                    continue

                candidates = [
                    (str(user_messages[i].id), user_messages[i].message_text) for i in range(index)
                ]
                suggestion = branching.suggest_parent(
                    new_text=message.message_text, candidates=candidates
                )

                self.stdout.write(f"     [{index}] {message.message_text[:60]}")
                if suggestion:
                    parent = next(
                        (m for m in user_messages if str(m.id) == suggestion.parent_id), None
                    )
                    parent_text = parent.message_text[:50] if parent else "?"
                    self.stdout.write(
                        self.style.WARNING(
                            f"       → 分岐候補 / Ứng viên rẽ nhánh: {parent_text} "
                            f"(score={suggestion.score} margin={suggestion.margin} "
                            f"confidence={suggestion.confidence})"
                        )
                    )
                else:
                    self.stdout.write("       → 分岐なし / không rẽ nhánh")

                # JA: 実際にDBへ保存されているAI推定と見比べる(AI方式で動かした履歴がある場合)。
                # VI: So với kết quả AI đã lưu trong DB (nếu từng chạy bằng phương thức AI).
                if message.suggested_parent_id:
                    stored = next(
                        (m for m in user_messages if m.id == message.suggested_parent_id), None
                    )
                    stored_text = stored.message_text[:50] if stored else "?"
                    self.stdout.write(
                        f"       (AI推定の記録 / AI đã đoán: {stored_text} "
                        f"confidence={message.parent_confidence})"
                    )

        if evaluated == 0:
            self.stdout.write(
                self.style.WARNING(
                    "\n評価できるセッションがありません(USER発言が3件以上必要)。"
                    "--demo でサンプル会話を試せます。 / "
                    "Không có session nào để đánh giá (cần >= 3 phát ngôn USER). "
                    "Dùng --demo để thử hội thoại mẫu."
                )
            )
