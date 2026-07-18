# API Kiểm tra Nạp tiền từ MBBank

## Giới thiệu

API này kiểm tra xem một nội dung cụ thể có xuất hiện trong lịch sử giao dịch nhận tiền của tài khoản MBBank hay không.

## Cấu hình

File `app.py` chứa cấu hình MBBank tại phần đầu:

```python
MB_USERNAME = "0866005531"
MB_PASSWORD = "Ngoctruong123@@@@"
MB_ACCOUNT_NO = "0174117062005"
```

**Thay đổi các giá trị này với tài khoản MBBank của bạn.**

## Endpoints

### GET /api/check-deposit

Kiểm tra nội dung có xuất hiện trong lịch sử giao dịch.

#### URL Parameters

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|----------|-------|
| description | string | Có | Nội dung cần kiểm tra |
| minutes | integer | Không | Số phút cần lấy (mặc định: 5) |

#### Ví dụ

```
GET http://localhost:5000/api/check-deposit?description=Premium&minutes=5
GET http://localhost:5000/api/check-deposit?description=Zalo
GET http://localhost:5000/api/check-deposit?description=Premium&minutes=30
```

#### Response

**Thành công (200):**
```json
{
    "result": true
}
```

**Lỗi (400):**
```json
{
    "error": "Missing description parameter"
}
```

**Lỗi server (500):**
```json
{
    "error": "Lỗi chi tiết"
}
```

## Cách sử dụng

### 1. Chạy API

```bash
python app.py
```

API sẽ chạy trên `http://localhost:5000`

### 2. Test với cURL

```bash
# Kiểm tra xem có "Premium" trong lịch sử 5 phút qua
curl "http://localhost:5000/api/check-deposit?description=Premium"

# Kiểm tra trong 30 phút qua
curl "http://localhost:5000/api/check-deposit?description=Zalo&minutes=30"
```

### 3. Test với Python

```python
import requests

url = "http://localhost:5000/api/check-deposit"
params = {
    "description": "Premium",
    "minutes": 5
}

response = requests.get(url, params=params)
data = response.json()

if data.get("result"):
    print("✓ Có nội dung này trong lịch sử")
else:
    print("✗ Không có nội dung này")
```

### 4. Test với JavaScript

```javascript
const url = new URL('http://localhost:5000/api/check-deposit');
url.searchParams.append('description', 'Premium');
url.searchParams.append('minutes', '5');

fetch(url)
    .then(res => res.json())
    .then(data => {
        if (data.result) {
            console.log("✓ Có nội dung này");
        } else {
            console.log("✗ Không có nội dung này");
        }
    });
```

## Logic hoạt động

1. **Kết nối MBBank** - Sử dụng thư viện `mbbank` để đăng nhập
2. **Lấy lịch sử giao dịch** - Từ `now - hours` đến hiện tại
3. **Lọc giao dịch** - Chỉ lấy giao dịch nhận tiền (creditAmount > 0)
4. **Tìm kiếm** - Kiểm tra xem `description` có chứa nội dung cần tìm (không phân biệt hoa/thường)
5. **Trả kết quả** - `true` nếu tìm thấy, `false` nếu không

## Xử lý lỗi

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-----------|----------|
| "Missing description parameter" | Không truyền description | Thêm `?description=xxx` vào URL |
| Lỗi kết nối MBBank | Tài khoản/mật khẩu sai | Kiểm tra `MB_USERNAME` và `MB_PASSWORD` |
| Lỗi timeout | Server MBBank không phản hồi | Thử lại sau |

## Bảo mật

⚠️ **Lưu ý:**
- Credentials được lưu trực tiếp trong code (giống test.py)
- Chỉ sử dụng trên mạng nội bộ
- Không chia sẻ credentials với ai

## Ví dụ thực tế

### Kiểm tra thanh toán Zalo trong 5 phút

```
http://localhost:5000/api/check-deposit?description=Zalo
```

Response:
```json
{
    "result": true
}
```

### Kiểm tra nạp tiền gói Premium trong 30 phút

```
http://localhost:5000/api/check-deposit?description=Premium&minutes=30
```

Response:
```json
{
    "result": false
}
```

## Cài đặt phụ thuộc

```bash
pip install flask flask-cors
# mbbank library đã có trong project
```

## Ghi chú

- API sử dụng GET request (có thể gán trực tiếp vào URL trình duyệt)
- Tìm kiếm không phân biệt hoa/thường
- Chỉ kiểm tra giao dịch nhận tiền (creditAmount > 0)
- Mặc định kiểm tra 5 phút gần nhất

---

**Phiên bản:** 1.0  
**Cập nhật:** 16/01/2026
