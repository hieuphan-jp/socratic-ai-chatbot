# Đề xuất: Thiết kế lại tính năng ôn tập (Bỏ việc AI tự sinh bài tương tự)

> Tài liệu song song: [`REVIEW_REDESIGN_PROPOSAL.ja.md`](./REVIEW_REDESIGN_PROPOSAL.ja.md)
> Số mục được đánh giống nhau ở cả hai bản để tiện tham chiếu qua lại giữa hai
> ngôn ngữ trong lúc họp.

---

## 0. Bối cảnh

Tính năng ôn tập hiện tại được thiết kế như sau:

> Chọn một knowledge node muốn ôn tập từ cây học tập → AI tự sinh một bài tương
> tự dựa trên node đó → quay lại đúng màn hình chat đã dùng khi node đó được
> tạo ra lần đầu → trao đổi về bài tương tự đó ngay trong chat đó → ghi lại số
> lần dùng gợi ý và thời gian hoàn thành.

Trong khi đó, vai trò của AI Tutor trong app này đã được chốt là: **đặt câu
hỏi để thúc đẩy người dùng học tập một cách chủ động**. Việc xác nhận xem
người dùng có thực sự "tư duy" chủ động hay không thì tạm thời không làm (vì
khó đánh giá).

Việc AI tự sinh bài tương tự, rồi (trong tương lai) chấm đúng/sai, giải thích
đáp án... là những hành vi lệch khỏi phương châm "thúc đẩy bằng câu hỏi" nói
trên, đồng thời khiến phần triển khai trở nên phức tạp không cần thiết.

Vì vậy, đề xuất **bỏ "AI tự động sinh bài tương tự"** trong tính năng ôn tập.
Còn luồng "chọn knowledge node → quay lại đúng phiên chat 1:1 gắn với node đó"
thì **KHÔNG bỏ — ngược lại, sẽ chỉnh lại thiết kế DB để luồng này thực sự hoạt
động đúng** (chi tiết ở mục 2-3). Đây là thay đổi trung tâm của đề xuất, hỗ
trợ trực tiếp cho việc làm cho việc ôn tập dễ hơn để thúc đẩy học chủ động.

---

## 1. Phạm vi những gì sẽ bỏ (thống nhất trước)

Trước tiên, làm rõ "bỏ cái gì":

- **1-1.** AI tự động sinh bài tương tự (`generate_similar_problem`)
- **1-2.** Cơ chế lưu bài tương tự đã sinh thành một knowledge node mới
  (có `origin_node`) trong DB
- **1-3.** Hành vi hiện tại **mỗi lần ôn tập lại tạo một phiên chat mới**
  (*hiện tại phần này đang lỗi runtime, chưa thực sự chạy được:
  `start_review()` đang gọi `chat.services.start_attempt` — hàm này không
  tồn tại; `reviews/views.py` cũng đang tham chiếu `attempt.chat_session` —
  field này cũng không tồn tại*). Sẽ bỏ hành vi này, nhưng thay bằng luồng
  "cùng một knowledge node thì luôn quay lại đúng một phiên chat cố định"
  (chỉ bỏ việc tạo mới, không bỏ việc quay lại chat cũ).
- **1-4.** Tính năng chấm đúng/sai và giải thích đáp án cho bài tương tự
  (chưa triển khai, nhưng có trong ý tưởng ban đầu)

Còn việc tính toán **khi nào nên ôn tập lại** (lặp lại ngắt quãng / SM-2) thì
**không nằm trong phạm vi bị bỏ lần này** — các phần dưới đây được viết theo
giả định đó. Nếu hiểu sai chỗ này, xin nêu ra để thống nhất lại.

---

## 2. Ảnh hưởng tới thiết kế DB

### 2-1. Những gì sẽ xoá

| Đối tượng | Lý do |
|---|---|
| `KnowledgeNode.origin_node` (FK tự tham chiếu) | Chỉ tồn tại để đánh dấu node nào là bài tương tự do AI sinh; không còn dùng vào việc gì khác |
| `topics.services.create_derived_node()` | Hàm tạo node bài tương tự; sẽ không còn nơi nào gọi tới |
| Điều kiện lọc `origin_node__isnull=True` trong `topics.services.build_learning_tree()` | Vì mọi node đều là node cố định, không cần lọc nữa |
| `reviews.services.generate_similar_problem()` | Bỏ hẳn việc sinh bài tương tự |
| `reviews.services.resolve_schedule_node()` | Không cần phán đoán `node.origin_node or node` nữa |

### 2-2. Những gì giữ nguyên

- `ReviewSchedule` (`easiness_factor` / `interval_days` / `repetitions` /
  `next_review_at` / `last_learned_at` / `learned_count`, và
  `retention_level` / `retention_color`) — việc tính "khi nào nên ôn tập"
  không liên quan tới phạm vi bỏ lần này, nên giữ nguyên
- `apply_sm2()` / `rating_from_hint_count()` — bản thân thuật toán không đổi

### 2-3. Những gì cần thay đổi

Các thay đổi dưới đây là trung tâm của đề xuất, hỗ trợ trực tiếp cho phương
châm ở mục 0 (làm việc ôn tập dễ hơn để thúc đẩy học chủ động).

- **`ChatSession.knowledge_node`**: đổi từ `ForeignKey` thông thường sang
  `OneToOneField`. Mỗi knowledge node sẽ luôn chỉ có đúng một phiên chat,
  nhờ đó luồng "quay lại đúng chat đã tạo ra node đó" mới thực sự thành lập
  được.
- **Vị trí lưu `hint_count` / `completed_at`**: hiện đang lưu trực tiếp trên
  `ChatSession`. Nhưng vì một phiên chat giờ sẽ được dùng lại nhiều lần cho
  nhiều lượt ôn tập, nên cần ghi nhận theo từng "lượt" riêng biệt. Vì vậy đề
  xuất tạo thêm một thực thể mới (tạm gọi là `Attempt`), có quan hệ 1:N với
  `ChatSession`, đại diện cho "một lượt học/ôn tập", và chuyển `hint_count` /
  `completed_at` sang đó.
  - `Attempt`: `chat_session` (FK, 1 `ChatSession` có nhiều `Attempt`),
    `hint_count`, `completed_at`
- **`ReviewLog.attempt`**: hiện đang trỏ tới model `Attempt` cũ (thực chất
  chỉ là alias của `chat.ChatSession`, gần như một bảng rỗng). Sẽ đổi để trỏ
  sang `Attempt` mới nêu trên.

### 2-4. 【Cần đội thống nhất】Các điểm còn mở

- **Điểm A — Có cần tạo bảng `Attempt` mới hay không**:
  SM-2 là thuật toán đánh giá "có nhớ lại được nội dung hay không" qua **nhiều
  lần lặp lại**. Nếu vẫn để `hint_count` / `completed_at` trực tiếp trên
  `ChatSession`, thì lượt ôn tập thứ 2 sẽ ghi đè lên dữ liệu của lượt thứ 1,
  khiến thuật toán không còn hoạt động đúng. Đây là lý do đề xuất tạo
  `Attempt`, nhưng nếu có phương án thay thế tốt hơn thì rất hoan nghênh
  thảo luận.
- **Điểm B — Có nên gắn `ChatMessage` với `Attempt` hay không**:
  Tức là mỗi `ChatMessage` có biết nó thuộc về `Attempt` nào (lượt ôn tập thứ
  mấy) hay không. Nếu muốn UI phân biệt trực quan "lượt học đầu tiên" và
  "lượt ôn tập lần 2" thì cần có; nếu độ ưu tiên chưa cao thì có thể để sau
  (Phase 2) cũng không sao.
- **Điểm C — Tiêu chí hoàn thành một lượt ôn tập**:
  Tiêu chí để coi là "đã hoàn thành một lượt ôn tập" là gì. Chỉ cần mở lại
  đoạn chat cũ và xem là được (thụ động), hay phải thực hiện một hành động
  nào đó trong đó mới tính (chủ động — ví dụ: gửi tin nhắn, trả lời câu hỏi
  của AI)? Cách trước đơn giản nhưng có nguy cơ "chỉ mở ra xem" cũng được
  tính vào đánh giá SM-2. Cách sau khớp hơn với phương châm "thúc đẩy học
  chủ động bằng câu hỏi" ở mục 0, nhưng cần chốt cụ thể yêu cầu hành động
  nào. Tiêu chí này quyết định trực tiếp thời điểm ghi `Attempt.completed_at`.

---

## 3. Phần nào giữ nguyên, phần nào cần sửa trong hiện trạng code

### 3-1. Giữ nguyên

- `SYSTEM_PROMPT` trong `apps/chat/services.py` (hành vi AI Tutor: đưa gợi ý
  từng chút một, không đưa thẳng đáp án) — phần này vốn đã khớp với phương
  châm lần này nên không cần sửa
- Tính năng đoán nhánh của `ChatMessage` (`parent_message` /
  `suggested_parent` / `parent_confidence`...) — độc lập với chủ đề lần này
  nên giữ nguyên
- Model `Topic` và phần cây phân cấp Topic của cây học tập — không liên quan
  nên giữ nguyên
- Logic gửi/nhận và hiển thị cơ bản của tính năng `hintChat` ở frontend —
  dùng lại được

### 3-2. Cần thay đổi (backend)

- **`apps/topics`**: xoá `KnowledgeNode.origin_node`; xoá
  `create_derived_node`; đơn giản hoá điều kiện lọc trong
  `build_learning_tree`; xoá tham chiếu `origin_node` trong
  `serializers.py` và `admin.py`
- **`apps/chat`**: đổi `ChatSession.knowledge_node` thành `OneToOneField`;
  tạo model `Attempt` mới; chuyển `hint_count` / `completed_at` từ
  `ChatSession` sang `Attempt`; đổi `create_chat_session_for_node` thành
  kiểu "có sẵn thì dùng lại, chưa có thì tạo mới"; đổi đối tượng thao tác
  của `record_hint_or_completion` sang `Attempt`
- **`apps/reviews`**: xoá `generate_similar_problem` và
  `resolve_schedule_node`; đơn giản hoá `record_review_result` — bỏ điều
  kiện rẽ nhánh theo `origin_node`, luôn tạo `ReviewLog`; viết lại hoàn
  toàn `start_review` theo hướng đơn giản hơn nhiều: chỉ lấy phiên chat có
  sẵn rồi tạo `Attempt` mới; đổi FK tham chiếu của `ReviewLog.attempt`

Một hệ quả phụ tích cực: luồng `start_review` hiện đang lỗi runtime (xem mục
1-3) cũng sẽ được giải quyết luôn nhờ lần thiết kế lại này.

### 3-3. Ảnh hưởng tới frontend

- **Tính năng `learningTree`**: hiện tại luồng chuyển sang chat khi click
  vào node còn chưa được triển khai, nên không phải làm lại gì nhiều. Khi
  triển khai có thể làm thẳng theo hướng "chuyển tới phiên chat đã có sẵn"
  ngay từ đầu.
- **Tính năng `hintChat`**: các API cơ bản (tạo phiên, gửi tin nhắn) dùng
  lại được nguyên vẹn. Cần thêm UI cho luồng mới, ví dụ nút "Bắt đầu ôn
  tập".

### 3-4. Đề xuất mới: Trực quan hoá mức độ ghi nhớ trên cây học tập

`ReviewSchedule` hiện đã có sẵn 4 mức `retention_level` (`unlearned` /
`fresh` / `fading` / `overdue`, tính từ tỷ lệ giữa số ngày đã trôi qua và
`interval_days`) cùng `retention_color` tương ứng. Đề xuất tận dụng dữ liệu
này để tô màu từng knowledge node trên cây học tập theo mức độ ghi nhớ —
đúng như ý tưởng ban đầu.

Ngoài việc tô màu từng node, đề xuất thêm một UI mới hiển thị **tỷ lệ phần
trăm** của toàn bộ cây học tập theo các mức độ ghi nhớ này, để người dùng
nắm được "cây học tập của mình đang khoẻ mạnh tới đâu" chỉ trong một cái
nhìn. Mục tiêu là tạo động lực bắt đầu ôn tập từ sự tự nhận thức này, thay
vì thông báo nhắc nhở hay ép buộc.

Ví dụ (màu dùng đúng theo `ReviewSchedule.RETENTION_COLORS` đã có sẵn
trong code, số liệu chỉ là minh hoạ):

| Mức độ ghi nhớ | Màu | Tỷ lệ (ví dụ) |
|---|---|---|
| Mới (fresh) | `#2E7D46` | 40% |
| Đang phai (fading) | `#7FB894` | 25% |
| Cần ôn tập (overdue) | `#C9622A` | 20% |
| Chưa học (unlearned) | `#9E9E9E` | 15% |

**Chi phí triển khai**: gần như không cần phát triển backend mới
(`retention_level` / `retention_color` đã có sẵn). Công việc chính là mở
rộng response của `build_learning_tree` để trả kèm `retention_level` của
từng node, và triển khai UI tô màu + thống kê tỷ lệ ở phía
`features/learningTree`.

---

## 4. Những điều cần đội quyết định trong buổi họp (tóm tắt)

- **Mục 1**: Thống nhất phạm vi những gì sẽ bỏ
- **Mục 2-4, Điểm A**: Có cần tạo bảng `Attempt` mới hay không
- **Mục 2-4, Điểm B**: Có cần gắn `ChatMessage` với `Attempt` hay không, ưu
  tiên tới đâu
- **Mục 2-4, Điểm C**: Tiêu chí hoàn thành ôn tập (thụ động hay chủ động)
- **Mục 3-3**: Đặc tả UI cho luồng bắt đầu ôn tập mới (vị trí nút, v.v.)
- **Mục 3-4**: Có triển khai trực quan hoá mức độ ghi nhớ (tô màu & hiển
  thị %) hay không
