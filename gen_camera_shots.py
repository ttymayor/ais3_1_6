import os

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.join(os.path.dirname(__file__), "static", "camera")
os.makedirs(OUT_DIR, exist_ok=True)

W, H = 720, 500


def font(size):
    for path in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def cctv_frame(name, id_number, cam_id, location, ts, filename):
    img = Image.new("RGB", (W, H), (18, 22, 28))
    d = ImageDraw.Draw(img)

    # 背景漸層（模擬黑白監視畫面）
    for y in range(H):
        shade = 26 + int(40 * (y / H))
        d.line([(0, y), (W, y)], fill=(shade, shade + 4, shade + 8))

    # 地板與走道透視線
    d.polygon(
        [(0, H), (W, H), (W // 2 + 160, 300), (W // 2 - 160, 300)], fill=(34, 40, 50)
    )
    d.polygon(
        [(W // 2, 300), (W // 2 - 160, 300), (0, H), (W // 2 - 90, H)],
        fill=(30, 36, 46),
    )
    d.polygon(
        [(W // 2, 300), (W // 2 + 160, 300), (W, H), (W // 2 + 90, H)],
        fill=(26, 32, 42),
    )

    # 人物剪影（監視畫面中的人）
    px = W // 2
    d.ellipse([px - 34, 150, px + 34, 218], fill=(8, 10, 12))  # 頭
    d.polygon(
        [(px - 46, 300), (px + 46, 300), (px + 40, 400), (px - 40, 400)],
        fill=(10, 12, 14),
    )  # 身體
    d.line([(px - 30, 230), (px - 70, 320)], fill=(10, 12, 14), width=16)  # 左手
    d.line([(px + 30, 230), (px + 70, 320)], fill=(10, 12, 14), width=16)  # 右手
    d.line([(px - 34, 320), (px - 30, 460)], fill=(10, 12, 14), width=18)  # 左腳
    d.line([(px + 34, 320), (px + 30, 460)], fill=(10, 12, 14), width=18)  # 右腳

    # CCTV 掃描線效果
    for y in range(0, H, 4):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, 60))
    for x in range(0, W, 24):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 6))

    # 邊框角標
    for cx, cy, dx, dy in [
        (10, 10, 1, 1),
        (W - 10, 10, -1, 1),
        (10, H - 10, 1, -1),
        (W - 10, H - 10, -1, -1),
    ]:
        d.line([(cx, cy), (cx + 46 * dx, cy)], fill=(0, 255, 0), width=3)
        d.line([(cx, cy), (cx, cy + 46 * dy)], fill=(0, 255, 0), width=3)

    # 頂部狀態列
    d.rectangle([0, 0, W, 30], fill=(0, 0, 0))
    d.rectangle([0, 0, 8, 30], fill=(220, 0, 0))
    d.text((20, 6), "REC", font=font(18), fill=(255, 60, 60))
    d.text((82, 8), cam_id, font=font(16), fill=(240, 240, 240))
    d.text((W - 240, 8), location, font=font(15), fill=(200, 200, 200))

    # 底部資訊列（含時間戳記 20260919_15:30:52 格式）
    d.rectangle([0, H - 52, W, H], fill=(0, 0, 0))
    d.text((14, H - 44), name, font=font(18), fill=(255, 255, 255))
    d.text(
        (14 + len(name) * 12 + 10, H - 42),
        id_number,
        font=font(14),
        fill=(170, 220, 170),
    )
    d.text((W - 250, H - 44), ts, font=font(17), fill=(120, 230, 120))

    img.save(os.path.join(OUT_DIR, filename))
    print("saved", filename)


# 示範人物資料（身分證 -> 監控畫面）
# A118153566 是主示範目標，時間戳記為 20260919_15:30:52
cctv_frame(
    "威利",
    "A118153566",
    "CAM-01 ｜ 大門口",
    "一樓大廳入口",
    "20260919_15:30:52",
    "A118153566.jpg",
)
cctv_frame(
    "陳小美",
    "B223456789",
    "CAM-02 ｜ 電梯口",
    "東側電梯前",
    "20260919_15:28:10",
    "B223456789.jpg",
)
cctv_frame(
    "李大明",
    "C123456789",
    "CAM-03 ｜ 停車場",
    "地下停車場 B2",
    "20260919_15:25:44",
    "C123456789.jpg",
)
cctv_frame(
    "王阿豪",
    "D123456789",
    "CAM-04 ｜ 走道",
    "三樓走道",
    "20260919_15:22:07",
    "D123456789.jpg",
)
