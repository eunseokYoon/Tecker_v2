import hashlib
import io
import logging

from PIL import Image

log = logging.getLogger(__name__)


def resize_to_4_3(image_bytes: bytes, *, target: tuple[int, int] = (800, 600)) -> bytes:
    """
    이미지를 4:3 비율로 중앙 크롭 후 target 크기로 리사이즈한다.

    - 가로가 더 넓으면 좌우를 균등하게 잘라낸다.
    - 세로가 더 길면 상하를 균등하게 잘라낸다.
    결과는 JPEG(quality=92)로 인코딩된 bytes.
    """
    target_ratio = target[0] / target[1]

    with Image.open(io.BytesIO(image_bytes)) as im:
        w, h = im.size
        ratio = w / h

        if ratio > target_ratio:
            new_w = int(h * target_ratio)
            offset = (w - new_w) // 2
            im = im.crop((offset, 0, offset + new_w, h))
        elif ratio < target_ratio:
            new_h = int(w / target_ratio)
            offset = (h - new_h) // 2
            im = im.crop((0, offset, w, offset + new_h))

        im = im.resize(target, Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=92)
        return buf.getvalue()


def log_image(name: str, image_bytes: bytes, **ctx: object) -> None:
    """이미지 전체를 로깅하지 않고 SHA-1 앞 8자리와 크기만 기록한다."""
    digest = hashlib.sha1(image_bytes).hexdigest()[:8]
    extra = " ".join(f"{k}={v}" for k, v in ctx.items())
    log.info("image=%s bytes=%d sha1=%s %s", name, len(image_bytes), digest, extra)
