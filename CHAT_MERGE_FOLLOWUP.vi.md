# Checklist sau khi merge nhánh Chat / チャット機能マージ後の再確認リスト

> **Mục đích của tài liệu này**
> Ngày 2026-08-15, chúng tôi đã kiểm tra xem luồng mục tiêu của cây học tập & lập lịch ôn tập
> (mẫu 1 và mẫu 2 bên dưới) có chạy được với backend hiện tại không. Kết quả: có những vấn đề
> **chỉ sửa được khi thay đổi phần code sẵn có của tính năng Chat (`backend/apps/chat/`)**.
> Vì tính năng Chat đang được sửa ở nhánh khác nên nhánh này không đụng vào chúng.
>
> Ngay sau khi merge nhánh Chat vào `develop`, hãy kiểm tra lần lượt các mục trong tài liệu này.
> **Một số mục có thể đã được giải quyết sẵn** (cách dùng: tick dần vào ô "Đã xử lý chưa").
>
> Bản tiếng Nhật: `CHAT_MERGE_FOLLOWUP.ja.md`

---

## 0. Tiền đề: luồng dữ liệu mục tiêu

### Mẫu 1: nội dung học lần đầu

1. Bắt đầu chat → tạo 1 `ChatSession` (chưa có `Attempt` và `KnowledgeNode`)
2. User bấm "nút hoàn thành học tập" (đồng thời chọn / tạo mới Topic)
3. Đúng thời điểm bước 2, tạo 1 `KnowledgeNode` và 1 `Attempt`
   - `KnowledgeNode` ↔ `ChatSession` là quan hệ **1-1**
   - `Attempt` được tạo **mỗi lần**: lần học đầu tiên và từng lần ôn tập sau đó

### Mẫu 2: ôn tập từ lần thứ 2 trở đi

1. Màu xanh của lá đậm dần theo số lần ôn (độ ghi nhớ); lá quá hạn ôn được báo bằng UI riêng
2. User chọn chiếc lá đang có tín hiệu
3. Vào lại được phiên chat cũ tương ứng với chiếc lá đó
4. Đọc lại hội thoại / trò chuyện tiếp
5. Bấm "nút hoàn thành ôn tập" → ghi thời điểm hoàn thành vào `Attempt`, cập nhật ngày ôn kế tiếp
   (**chưa bấm nút thì chưa tạo `Attempt`**)
6. Màu của lá và tỉ lệ ghi nhớ (%) của cả cây được cập nhật

### Các quyết định thiết kế (2026-08-15)

| Ký hiệu | Quyết định |
|---|---|
| A | `hint_count` không còn công dụng nên **bỏ**. `Attempt` **chỉ tạo khi hoàn thành** |
| B | Màu của lá do **frontend** quyết định, bằng cách ghép `/api/learning-tree/` với `/api/review-schedules/` theo `node_id` (không thêm API thống kê ở backend) |
| C | **Độ đậm xanh = số lần ôn (độ ghi nhớ)**, **thời điểm ôn tập = UI riêng, tách khỏi màu**. Tỉ lệ ghi nhớ của cây (%) = "số lá chưa quá hạn ÷ tổng số lá" |
| D | **Không** cho user tự khai mức hiểu. Chỉ tính dựa trên "user tự mở lại node đúng hạn và bấm nút hoàn thành" (vẫn để ngỏ khả năng đổi sang cách tính linh hoạt hơn sau này) |
| F | Cấm copy & paste xử lý ở phía frontend (backend tạm thời không cần làm gì) |

---

## 1. Đã xử lý ở nhánh này (`feat/learning-tree-retention-api`)

Những việc không cần đụng tới tính năng Chat đã được làm xong. Sau khi merge không cần làm lại.

| Nội dung | Vị trí |
|---|---|
| Thêm cửa ngõ kiểm tra quyền sở hữu `get_owned_knowledge_node()` cho app khác (dùng ở mục 2-2) | `apps/topics/services.py` |
| Bỏ `retention_level` / `retention_color` (1 trục, 4 mức), đổi thành **2 trục: `mastery_level` (độ đậm xanh) + `is_due` / `days_overdue` (tín hiệu ôn tập)** (quyết định C) | `apps/reviews/models.py`, `serializers.py` |
| Backend không trả mã màu (hex) nữa; frontend tự quyết màu | như trên |
| Bỏ việc tự khai mức hiểu; hoàn thành được ghi bằng điểm cố định (quyết định D). Tham số `understood` của `record_review_result(attempt, understood)` **vẫn nhận nhưng bị bỏ qua** (vì phía Chat còn truyền) | `apps/reviews/services.py` |
| Sắp xếp danh sách `due` theo "quá hạn lâu nhất trước" | `apps/reviews/views.py` |
| **Sửa lại test của topics vốn đang lỗi toàn bộ 17 test** do chưa cập nhật theo việc xóa `origin_node` | `apps/topics/tests.py` |
| Thêm mới test cho việc lập lịch ôn tập (9 test) | `apps/reviews/tests.py` |

---

## 2. Các mục còn lại ở phía tính năng Chat (cần xử lý)

### 2-1. 【Ưu tiên cao nhất】Nút hoàn thành bị chặn với lỗi 400

- **Hiện tượng**: nếu chỉ bấm nút hoàn thành mà không nhập nội dung, mẫu 1-2 / 1-3 không chạy hết được.

  ```
  POST /api/chat-sessions/{id}/send-message/
  {"action_type": "COMPLETE", "topic_id": "..."}
  → 400 {"message_text": ["This field is required."]}

  {"message_text": "", "action_type": "COMPLETE", "topic_id": "..."}
  → 400 {"message_text": ["This field may not be blank."]}
  ```

- **Nguyên nhân**: `SendMessageInputSerializer.message_text` trong `apps/chat/serializers.py` để `required=True`,
  trong khi `send_message_and_get_ai_response()` ở `apps/chat/services.py` lại cho phép chuỗi rỗng
  (chỉ bắt buộc khi `ANSWER` / `REQUEST_CHANGE_METHOD`). **Chỉ riêng serializer bị lệch.**
- **Cách né tạm thời rất nguy hiểm**: nếu frontend gửi một chuỗi giả, chuỗi đó **được lưu như một phát ngôn thật**
  và nằm lại trong lịch sử hội thoại lẫn đồ thị (kèm theo cả vấn đề 2-5).
- **Cách sửa khuyến nghị**: tách nút hoàn thành ra khỏi API gửi tin nhắn.

  ```
  POST /api/chat-sessions/{id}/complete/      ← không cần nội dung; topic_id chỉ cần ở lần đầu
  POST /api/chat-sessions/{id}/send-message/  ← thuần túy hội thoại
  ```

  Như vậy vấn đề biến mất về mặt cấu trúc và nút hoàn thành không làm bẩn lịch sử hội thoại.
  Nếu không tách thì tối thiểu phải đổi thành `required=False, allow_blank=True, default=""`.
- **Đã xử lý chưa**: ☐

### 2-2. 【Bảo mật】Có thể gắn phiên chat của mình vào KnowledgeNode của người khác

- **Hiện tượng**: truyền `node_id` của user khác khi tạo session:

  - Nếu node đó đã có session → **500** với `UNIQUE constraint failed: chat_chatsession.knowledge_node_id`
  - Nếu chưa có → **session của mình gắn vào node của người khác, và các thao tác hoàn thành sau đó
    sẽ ghi đè lịch ôn tập của người khác**

- **Nguyên nhân**: `create_chat_session_for_node()` trong `apps/chat/services.py` dùng
  `KnowledgeNode.objects.filter(id=node_id)`, **không đưa chủ sở hữu vào điều kiện**.
  `KnowledgeNode` không giữ `user` trực tiếp (chủ sở hữu là `topic.user`) nên tự query ở mỗi app rất dễ sót.
- **Vi phạm CLAUDE.md**: thuộc mục kiểm tra bắt buộc số 3 "truy cập ORM trực tiếp vào model do app khác sở hữu".
- **Cách sửa**: chỉ cần thay bằng cửa ngõ đã chuẩn bị sẵn ở nhánh này.

  ```python
  from apps.topics import services as topics_services

  node = topics_services.get_owned_knowledge_node(user=user, node_id=node_id)
  # không tìm thấy / của người khác → ném NotFound (404)
  ```

  (Cùng dạng với `get_owned_topic()`, đã kèm kiểm tra quyền và có test ở `apps/topics/tests.py`.)
- **Đã xử lý chưa**: ☐

### 2-3. 【Toàn vẹn dữ liệu】Xử lý hoàn thành chưa được bọc transaction

- **Hiện tượng**: khi hoàn thành, các bước "tạo `KnowledgeNode` → đóng `Attempt` → ghi `ReviewLog` →
  cập nhật lịch kế tiếp" chạy lần lượt nhưng **commit riêng lẻ**. Nếu hỏng giữa chừng sẽ còn lại trạng thái dở dang
  **"có node nhưng không có lịch ôn tập"**.
- **Cách sửa**: gắn một `@transaction.atomic` ở đầu vào của xử lý hoàn thành.
- **Đã xử lý chưa**: ☐

### 2-4. 【Quyết định A】Bỏ `Attempt.hint_count` và thời điểm tạo Attempt

- **Hiện trạng**: bấm nút gợi ý cũng tạo `Attempt` (`get_or_create_active_attempt()`),
  **lệch** với luồng mục tiêu "chưa bấm nút hoàn thành thì chưa tạo `Attempt`".
- **Quyết định**: số lần gợi ý không còn công dụng (AI về cơ bản đặt câu hỏi, và tính năng sinh bài ôn tập đã bỏ), nên:
  - Xóa field `Attempt.hint_count` (1 migration)
  - `Attempt` **chỉ tạo khi hoàn thành** (tạo 1 bản ghi kèm `completed_at` là đủ)
  - Có giữ `action_type="HINT"` hay không là quyết định của phía Chat; nếu giữ thì cũng không đụng tới `Attempt`
- **Ảnh hưởng tới frontend**: kiểu `Attempt` trong `frontend/src/shared/types/index.ts` có `hint_count`,
  cần xóa theo (file dùng chung → phải ghi rõ ảnh hưởng tới tính năng khác trong mô tả PR).
- **Đã xử lý chưa**: ☐

### 2-5. 【Quyết định D】Gỡ bỏ `understood` (tự khai mức hiểu)

- **Hiện trạng**: đầu vào của `send-message` có `understood` (mặc định `False`), phía Chat truyền sang bằng
  `record_review_result(attempt, bool(understood))`.
- **Quyết định**: không tự khai mức hiểu. **Phía reviews đã chuyển sang bỏ qua `understood`**
  (ghi bằng điểm cố định; vẫn giữ lại field `ReviewLog.performance_rating` cho tương lai).
- **Việc cần làm**: xóa trường nhập `understood` và việc truyền tham số ở phía Chat, gọi `record_review_result(attempt)`.
  Tham số ở phía reviews đang được giữ để tương thích; sau khi Chat sửa xong có thể xóa luôn.
- **Lưu ý**: trước đây khai "chưa hiểu" sẽ kéo khoảng cách ôn tập về 1 ngày; theo quyết định này hành vi đó không còn
  (khoảng cách chỉ giãn ra: 1 ngày → 6 ngày → nhân hệ số).
- **Đã xử lý chưa**: ☐

### 2-6. 【Nhỏ】Phát ngôn của user khi hoàn thành / xin gợi ý bị lưu với loại `CHANGE_METHOD`

- **Hiện tượng**: mọi `action_type` khác `"ANSWER"` đều bị coi là `CHANGE_METHOD` (node đổi cách giải),
  nên lời nhắn kèm lúc hoàn thành hiện ra trong đồ thị tư duy như một node "đổi cách giải".
- **Cách sửa**: nếu tách endpoint hoàn thành như mục 2-1 thì nhánh code này biến mất luôn.
- **Đã xử lý chưa**: ☐

### 2-7. Cách đo `response_time_seconds`

- **Hiện trạng**: tính bằng `attempt.completed_at - attempt.created_at`.
  Sau khi áp dụng 2-4 (chỉ tạo `Attempt` lúc hoàn thành), **hiệu số này gần như bằng 0 và vô nghĩa**.
- **Lựa chọn**: (a) bỏ ghi nhận (b) đo từ lúc mở lại session (c) đo từ tin nhắn đầu tiên của lượt đó.
  Hiện UI chưa dùng nên chọn (a) cũng không sao.
- **Đã xử lý chưa**: ☐

### 2-8. 【CI】Các file của tính năng Chat chưa chạy `ruff format`

- Tại thời điểm `develop`, **CI đang đỏ**. Còn 3 file chưa được format:

  ```
  backend/apps/chat/services.py
  backend/apps/chat/views.py
  backend/apps/chat/migrations/0004_merge_20260814_1404.py
  ```

  (Các cảnh báo cùng loại ở phía `topics` đã được xử lý ở nhánh này.)
- **Cách sửa**: `cd backend && ruff format .`
- **Đã xử lý chưa**: ☐

### 2-9. `apps/chat/tests.py` đang trống

Hiện chỉ có đúng 1 dòng `# Create your tests here.`, không có test nào cho luồng chính.
Sau khi merge, tối thiểu hãy thêm các test sau (test tương ứng ở phía reviews nằm tại `apps/reviews/tests.py`).

- Ngay sau khi tạo session thì chưa tồn tại `Attempt` lẫn `KnowledgeNode` (mẫu 1-1)
- Bấm nút hoàn thành mà không có nội dung vẫn thành công (chặn hồi quy 2-1)
- Khi hoàn thành thì `KnowledgeNode` và `Attempt` mỗi loại được tạo **đúng 1 bản ghi** (mẫu 1-3)
- Hoàn thành lần 2 trên cùng session thì có 2 `Attempt` (mẫu 2-5)
- Không tạo được session bằng `node_id` của người khác (chặn hồi quy 2-2)
- Nếu có exception giữa chừng khi hoàn thành thì không sót lại node lẫn lịch ôn tập (chặn hồi quy 2-3)

---

## 3. Quy trình kiểm tra lại sau khi merge

Dùng một client đã đăng nhập, gọi lần lượt các API sau để xác nhận mẫu 1 và mẫu 2 chạy được.

```
# Mẫu 1
POST /api/chat-sessions/                      → 201; attempts=0, knowledge_node=null
POST /api/chat-sessions/{id}/send-message/    → hội thoại diễn ra bình thường
POST /api/topics/                             → tạo Topic để lưu vào
POST /api/chat-sessions/{id}/complete/        → 200 dù không có nội dung; có 1 KnowledgeNode và 1 Attempt
    (nếu chưa tách như 2-1 thì gọi send-message với COMPLETE)

# Mẫu 2
GET  /api/learning-tree/                      → lá (knowledge_node) xuất hiện trên cây
GET  /api/review-schedules/                   → trả về mastery_level / is_due / chat_session_id
GET  /api/review-schedules/due/               → chỉ lá quá hạn, sắp theo hạn cũ nhất trước
POST /api/chat-sessions/  {"node_id": "..."}  → trả về đúng session cũ (vào lại được)
POST /api/chat-sessions/{id}/complete/        → Attempt tăng thêm, ngày ôn kế tiếp giãn ra
```

Màu của cây ở frontend được quyết định bằng cách ghép `/api/learning-tree/` (danh sách lá) với
`/api/review-schedules/` (`mastery_level`, `is_due`) theo `node_id`. Lá không xuất hiện trong
`/api/review-schedules/` nghĩa là **chưa có ReviewSchedule = chưa học**, hãy tô màu xám.
Tỉ lệ ghi nhớ của cả cây (%) = `số lá có is_due = false ÷ tổng số lá`.
