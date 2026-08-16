# Hướng dẫn cấu trúc thư mục (Bản tiếng Việt)

> Tài liệu này tóm tắt ngắn gọn **vai trò của từng thư mục** trong repo này và
> **kỹ sư nên viết gì** trong các file bên trong. Quy tắc hiện thực chi tiết và
> pattern để sao chép nằm ở [`CONVENTIONS.md`](./CONVENTIONS.md) — bắt buộc phải đọc.
> Hướng dẫn cài đặt xem ở [`README.md`](./README.md). Tài liệu này chỉ là "bản đồ" đi trước.

---

## Tổng quan

```
.
├── CONVENTIONS.md   # Quy ước phát triển (quan trọng nhất, có pattern để sao chép)
├── README.md        # Hướng dẫn cài đặt
├── .env.example     # Mẫu biến môi trường
├── .github/         # CI và mẫu PR
├── backend/         # Django + DRF (phía server)
└── frontend/        # React + TypeScript + Vite (phía màn hình / SPA)
```

Backend và frontend chỉ giao tiếp với nhau qua **URL dạng `/api/...` và JSON**.
Hai thư mục hoàn toàn độc lập, không import code trực tiếp lẫn nhau.

---

## 1. Gốc repo

| File / Thư mục | Vai trò | Viết / sửa gì ở đây |
|---|---|---|
| `CONVENTIONS.md` | Quy ước phát triển. §9 có pattern hiện thực toàn bộ tầng (nguồn để sao chép) | Chỉ sửa khi thay đổi quy ước. Bình thường chỉ để **đọc** |
| `README.md` | Hướng dẫn cài đặt, mô tả stack công nghệ | Cập nhật khi cách cài đặt thay đổi |
| `.env.example` | Mẫu biến môi trường | Thêm tên biến mới khi cần (để trống giá trị) |
| `.github/workflows/ci.yml` | Định nghĩa CI (backend: ruff + kiểm tra thiếu migration / frontend: kiểm kiểu + build) | Bình thường không sửa. Chỉ sửa khi cần thêm bước kiểm tra |
| `.github/PULL_REQUEST_TEMPLATE.md` | Mẫu tự động nạp khi tạo PR | Bình thường không sửa |

---

## 2. `backend/` (Django + DRF)

### File ở gốc

| File | Vai trò | Viết gì |
|---|---|---|
| `manage.py` | Điểm vào lệnh Django | Về cơ bản không sửa |
| `requirements/base.txt` | Thư viện phụ thuộc dùng chung mọi môi trường | Thêm package pip mới nếu cần |
| `requirements/local.txt` | Công cụ chỉ dùng khi phát triển (lint...) | Thêm package chỉ dùng khi dev nếu cần |
| `requirements/gemini.txt` | Dependency tùy chọn cho Gemini SDK (`google-generativeai`) | Tách riêng vì build lỗi trên Windows ARM64 v.v. Chỉ cài khi cần kiểm tra Gemini thật: `pip install -r requirements/gemini.txt` |

### `backend/config/` — Cấu hình toàn dự án (vai trò "bản đồ")

| File | Vai trò | Viết gì |
|---|---|---|
| `settings/base.py` | Cấu hình dùng chung mọi môi trường | Thêm `INSTALLED_APPS` mới, cấu hình DRF... miễn là không phụ thuộc môi trường |
| `settings/local.py` | Ghi đè riêng cho local (SQLite, DEBUG, CORS) | Bình thường không sửa |
| `settings/production.py` | Dành cho production (bộ khung chuyển sang PostgreSQL, chưa dùng) | Người phụ trách deploy mở rộng |
| `urls.py` | Điểm vào URL của toàn dự án | **Tạo app mới thì thêm 1 dòng `include()`** |
| `wsgi.py` / `asgi.py` | Điểm khởi động server | Bình thường không sửa |

### `backend/apps/` — Nơi đặt các app Django theo từng tính năng

Mỗi app gồm bộ 5 file chuẩn `models.py` / `serializers.py` / `services.py` / `views.py` / `urls.py`
(+ `admin.py`). **Không tách thành thư mục theo tầng như `views/` hay `models/`.**

Chiều phụ thuộc: **`views → services → models`** (cấm đi ngược).

| File | Viết cái này | KHÔNG viết cái này |
|---|---|---|
| `models.py` | Định nghĩa bảng, quan hệ | Logic nghiệp vụ |
| `serializers.py` | Định nghĩa hình dạng JSON, kiểm tra đầu vào | Xử lý lưu trữ, phán đoán nghiệp vụ |
| `services.py` | **Logic nghiệp vụ (hàm thuần, không biết HTTP)** | Đụng vào `request` hoặc HTTP |
| `views.py` | Phân quyền, kiểm tra đầu vào, **gọi services**, tuần tự hóa | Tự viết logic nghiệp vụ |
| `urls.py` | Đăng ký định tuyến trong app này | Việc khác |
| `admin.py` | Đăng ký vào trang quản trị Django | — |

#### `apps/common/` (nền tảng dùng chung mọi app — TUYỆT ĐỐI không viết logic riêng của một tính năng)

| File | Vai trò |
|---|---|
| `models.py` | `BaseModel` (khóa chính UUID + thời điểm tạo/cập nhật). Model mới chỉ cần kế thừa, hiếm khi sửa trực tiếp |
| `exceptions.py` | Exception nghiệp vụ như `ValidationError` và bộ xử lý exception của DRF. Chỉ thêm khi cần loại lỗi mới |
| `permissions.py` | Lớp quyền dùng chung như `IsOwner`. Chỉ thêm khi cần quyền chung mới |
| `management/commands/seed.py` | Lệnh nạp dữ liệu demo. **Có thể thêm phần tạo dữ liệu mẫu cho tính năng của bạn vào đây** |

#### `apps/accounts/` (xác thực người dùng — cấu trúc này là "mẫu" cho mọi app tính năng)

| File | Nội dung |
|---|---|
| `models.py` | `User` tùy biến (cố ý không thêm trường). Về cơ bản không sửa |
| `serializers.py` | Chỉ định nghĩa kiểu và kiểm tra đầu vào/ra khi đăng nhập |
| `services.py` | Kiểm tra thông tin đăng nhập (logic phán đoán thuần) |
| `views.py` | API `/api/auth/{csrf,login,logout,me}/`. Phân quyền, điều khiển session |
| `urls.py` | Định nghĩa endpoint xác thực |

#### `apps/ai/` (tầng trừu tượng nhà cung cấp LLM — không có model DB)

| File | Vai trò |
|---|---|
| `base.py` | Hợp đồng (`Protocol`) mọi provider phải thỏa. Không tự ý thay đổi |
| `fake.py` | Hiện thực giả, không cần API key. Mặc định dùng cái này |
| `gemini.py` | Hiện thực thật (bộ khung, chưa cài). **Người phụ trách AI sẽ hiện thực phần thân** |
| `client.py` | Cửa duy nhất để lấy provider. Dùng qua `get_llm()` (chỉ nơi này quyết định chọn fake hay gemini) |

#### Khi tạo app tính năng mới (ví dụ: `apps/items/`)

Làm theo các bước ở [`CONVENTIONS.md` §4](./CONVENTIONS.md), tạo đủ bộ 5 file giống `apps/accounts/`.
Khung hiện thực **bắt buộc sao chép từ [`CONVENTIONS.md` §9](./CONVENTIONS.md)** (chủ trương không đặt tính năng mẫu trong code).

---

## 3. `frontend/` (React + TypeScript + Vite)

Cấu trúc thiên về Feature-Sliced, phụ thuộc đi **một chiều từ trên xuống dưới**.

```
app/       … Provider, router, layout (lắp ghép ở cấp cao nhất)
  ↓
pages/     … Theo từng route. Chỉ "lắp ghép" các component lại
  ↓
features/  … Theo từng tính năng (api hook + components). Nội dung tính năng nằm ở đây
  ↓
shared/    … api client, UI dùng chung, kiểu (nền tảng cho mọi feature)
```

### `frontend/src/app/` — Nền tảng của app

| File | Vai trò | Viết gì |
|---|---|---|
| `App.tsx` | Gốc của app. Chỉ bọc router bằng Provider | Về cơ bản không sửa |
| `providers.tsx` | Gom các Provider bao toàn app (TanStack Query...) | Chỉ thêm khi cần Provider toàn cục mới |
| `router.tsx` | Bảng đối chiếu URL với page | **Tạo màn hình mới thì thêm 1 dòng ở đây** |
| `RequireAuth.tsx` | Chốt chặn xác thực (chưa đăng nhập thì đẩy về trang login) | Về cơ bản không sửa |

### `frontend/src/pages/` — Chỉ "lắp ghép" màn hình

- 1 màn hình = 1 file (ví dụ: `HomePage.tsx`, `LoginPage.tsx`).
- Chỉ xếp các component từ `features/` lại với nhau, **KHÔNG được viết logic nghiệp vụ hay giao tiếp API**.
- Tạo màn hình mới thì thêm 1 route vào `app/router.tsx`.

### `frontend/src/features/<tên-tính-năng>/` — Hiện thực theo từng tính năng (nội dung viết ở đây)

| Thư mục | Vai trò | Viết gì |
|---|---|---|
| `api/hooks.ts` | Hook TanStack Query xử lý trạng thái từ server | `useQuery`/`useMutation`. **Giao tiếp luôn qua `api` của `shared/api/client.ts`**, không gọi `fetch` trực tiếp |
| `api/mockData.ts` | Dữ liệu/logic giả khi backend API chưa có | Sau khi có API thật thì thay bằng lệnh gọi thật trong `api/hooks.ts` |
| `components/` | Component hiển thị | Chỉ nối UI với hook. Không mang logic giao tiếp vào đây |

**Bắt buộc**: các `features/` không import lẫn nhau. Muốn dùng chung thì đưa lên `shared/`.

### `frontend/src/shared/` — Nền tảng dùng chung cho mọi feature

| File / Thư mục | Vai trò | Viết gì |
|---|---|---|
| `api/client.ts` | **Cửa duy nhất cho mọi giao tiếp HTTP** (gửi Cookie, gắn CSRF, redirect khi 401, chuẩn hóa lỗi) | Chỉ sửa khi thay đổi chính sách auth/xử lý lỗi. Từng tính năng chỉ gọi file này |
| `api/queryKeys.ts` | Quản lý tập trung query key của TanStack Query | **Mỗi khi thêm tính năng mới, thêm 1 nhóm key vào đây** |
| `types/index.ts` | Kiểu dùng chung nhiều feature | Thêm kiểu khớp với output serializer backend. Kiểu riêng của feature để trong feature đó |
| `ui/index.tsx` | Component UI tối thiểu dùng chung mọi feature (Button/Input/Notice...) | Chỉ đặt component tổng quát "không phụ thuộc feature nào". Không mang logic nghiệp vụ |
| `lib/` | Nơi đặt logic/tiện ích dùng chung (hiện đang trống) | Thêm khi có hàm dùng chung nhiều feature |

### Gốc `frontend/`

| File | Vai trò | Viết gì |
|---|---|---|
| `vite.config.ts` | Cấu hình dev server, proxy `/api` | Bình thường không sửa |
| `tsconfig.json` | Cấu hình TypeScript, alias đường dẫn (`@/`) | Bình thường không sửa |
| `package.json` | Package phụ thuộc, script npm | Tự cập nhật khi thêm package mới |

---

## Giải thích bổ sung (theo từng mức kinh nghiệm)

### 🅰 Dành cho người đã quen React / Next.js (chưa quen Django)

- **`apps/<name>/` giống thư mục theo tính năng của Next.js, nhưng KHÔNG phải file-based routing.**
  Next.js chỉ cần tạo `app/items/page.tsx` là tự động có route `/items`, còn Django thì bạn phải
  tự viết đường dẫn trong `apps/items/urls.py`, rồi thêm `include()` vào `config/urls.py` thì
  URL mới hoạt động. Cảm giác "tạo thư mục là tự động thành route" KHÔNG áp dụng ở đây.
- **`views.py` giống Route Handler của Next.js (`app/api/.../route.ts`), nhưng theo quy ước này
  hầu như không viết logic ở đây.** Logic bắt buộc đặt ở `services.py`; `views.py` chỉ là
  controller mỏng lo "phân quyền, kiểm tra đầu vào, gọi services, tuần tự hóa".
- **`serializers.py` giống schema của Zod hoặc Yup** (định nghĩa kiểu + validate), nhưng khác
  ở chỗ nó còn đảm nhận việc chuyển đổi qua lại với model DB (`models.py`), điều mà thư viện
  validate phía frontend không làm.
- **`models.py` (Django ORM) giống khái niệm `schema.prisma` của Prisma.**
  Lệnh `python manage.py makemigrations` tương đương `prisma migrate dev`.
- **`config/settings/` (base/local/production) giống `next.config.js` + `.env.*` gộp lại
  và viết bằng Python.** Khác biệt là nó được tách theo môi trường thay vì gộp 1 file
  (`local.py` ghi đè lên `base.py`).
- Phía frontend (`app/`, `pages/`, `features/`, `shared/`) trông quen mắt, nhưng
  **`app/` ở đây KHÔNG giống thư mục `app/` của Next.js.** Ở đây `app/` chỉ là "nơi đặt Provider
  và định nghĩa router". Định tuyến thực sự dùng `react-router-dom`, khai báo tường minh trong
  `router.tsx` (không phải kiểu "cấu trúc thư mục = route" như Next.js).

### 🅱 Dành cho người đã quen Django (chưa quen React / Next.js)

- **`frontend/src/features/` có ý tưởng giống `apps/` của Django: chia theo từng tính năng.**
  Nhưng phía frontend đơn giản hơn nhiều: mỗi tính năng chỉ có 2 thư mục con là `api/`
  (logic lấy dữ liệu) và `components/` (giao diện), không chia nhỏ thành nhiều loại file như Django.
- **`pages/` có vị trí giống `templates/` của Django, nhưng quy ước ở đây khắt khe hơn.**
  `pages/` thực sự chỉ "xếp component lại với nhau", tuyệt đối không viết giao tiếp API hay
  logic gì cả (nội dung bắt buộc nằm ở `features/`).
- **`shared/api/client.ts` tương đương với "wrapper request dùng chung / middleware" trong Django.**
  Việc gom gửi Cookie, gắn CSRF token, xử lý lỗi vào một chỗ ở đây cùng tư duy thiết kế với
  `apps/common/exceptions.py` — nơi gom xử lý exception về một chỗ — chỉ khác là áp dụng ở phía frontend.
- **TanStack Query (dùng trong `api/hooks.ts`) là thư viện cache và quản lý dữ liệu lấy từ server
  ngay trên trình duyệt.** Khác với Django giữ trạng thái ở phía server bằng session, ở đây
  frontend cũng phải tự quản lý "dữ liệu này khi nào cần lấy lại". Có thể hình dung:
  `useQuery` = lấy dữ liệu + cache, `useMutation` = các thao tác thay đổi (POST/PUT/DELETE).
- **Về CSRF: vì SPA không dùng được cơ chế template của Django (`{% csrf_token %}`),
  nên phía SPA (`shared/api/client.ts`) phải tự đọc Cookie `csrftoken` rồi gắn thủ công vào header.**
  Cơ chế CSRF middleware bên Django không đổi, chỉ có "cách chuyển giao token" là thay đổi cho phù hợp với SPA.

### 🆕 Dành cho người chưa quen cả hai

- **`backend/` là phía server (hậu trường).** Phụ trách việc lưu vào cơ sở dữ liệu, kiểm tra
  đăng nhập... — những việc không hiển thị trực tiếp trên màn hình trình duyệt.
- **`frontend/` chính là màn hình bạn thấy trên trình duyệt.** Mọi nút bấm, form nhập liệu mà
  người dùng thao tác đều nằm ở đây.
- **Hai bên chỉ kết nối với nhau qua một quy ước chung gọi là "API".** `backend/` chuẩn bị sẵn
  các URL như `/api/items/`, còn `shared/api/client.ts` ở `frontend/` sẽ gửi yêu cầu tới URL đó
  và nhận kết quả (dạng JSON) trả về. Hai bên không đọc trực tiếp code của nhau.
- **Khi làm một tính năng, hãy nghĩ theo cặp "backend + frontend".** Ví dụ tính năng
  "quản lý item" thì cần tạo **cả hai**: `backend/apps/items/` và `frontend/src/features/items/`.
- Nếu chưa biết bắt đầu từ đâu, cách nhanh nhất là sao chép nguyên **§9 (pattern hiện thực)**
  trong [`CONVENTIONS.md`](./CONVENTIONS.md), chỉ đổi tên cho khớp tính năng của bạn rồi chạy thử.
  Vừa chạy code thật vừa đối chiếu với từng dòng trong tài liệu này để hiểu rõ hơn.
