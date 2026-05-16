import asyncio
import difflib
import logging
from PIL import ImageGrab, Image

logger = logging.getLogger(__name__)

ALL_TRIBES = [
    "Murloc", "Beast", "Mech", "Demon", "Dragon",
    "Elemental", "Pirate", "Naga", "Undead", "Quillboar",
    "Neutral",
]

FUZZY_THRESHOLD = 0.75


def capture_crop(crop_region: list | None) -> Image.Image:
    img = ImageGrab.grab()
    if crop_region:
        x, y, w, h = crop_region
        img = img.crop((x, y, x + w, y + h))
    return img


def run_ocr(img: Image.Image) -> list[str]:
    try:
        import winrt.windows.media.ocr as win_ocr
        import winrt.windows.graphics.imaging as imaging
        import winrt.windows.storage.streams as streams
        import io

        async def _recognize():
            engine = win_ocr.OcrEngine.try_create_from_user_profile_languages()
            buf = io.BytesIO()
            img.save(buf, format="BMP")
            buf.seek(0)
            data = buf.read()
            stream = streams.InMemoryRandomAccessStream()
            writer = streams.DataWriter(stream)
            writer.write_bytes(data)
            await writer.store_async()
            stream.seek(0)
            decoder = await imaging.BitmapDecoder.create_async(stream)
            bitmap = await decoder.get_software_bitmap_async()
            return await engine.recognize_async(bitmap)

        result = asyncio.run(_recognize())
        return [line.text for line in result.lines]
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return []


def match_tribes(
    ocr_tokens: list[str],
    known_tribes: list[str] = ALL_TRIBES,
) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    unmatched: list[str] = []
    for token in ocr_tokens:
        close = difflib.get_close_matches(token, known_tribes, n=1, cutoff=FUZZY_THRESHOLD)
        if close:
            tribe = close[0]
            if tribe not in matched:
                matched.append(tribe)
        else:
            unmatched.append(token)
    return matched, unmatched


def scan_tribes(crop_region: list | None) -> tuple[list[str], list[str]]:
    img = capture_crop(crop_region)
    tokens = run_ocr(img)
    return match_tribes(tokens)
