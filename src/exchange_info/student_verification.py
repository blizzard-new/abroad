from __future__ import annotations

import io
import os
import re
import shutil
import unicodedata
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageOps, ImageStat

from .university_registry import resolve_university


SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}
MIN_WIDTH = 640
MIN_HEIGHT = 360


class StudentCardVerificationError(ValueError):
    """Raised when the uploaded images cannot safely confirm a student card."""


@dataclass(frozen=True)
class StudentCardVerification:
    school_name: str
    checks: tuple[str, ...]
    department_name: str | None = None


def _open_card(data: bytes, side: str) -> Image.Image:
    try:
        with Image.open(io.BytesIO(data)) as source:
            image_format = source.format
            image = ImageOps.exif_transpose(source).convert("RGB")
    except (OSError, ValueError) as exc:
        raise StudentCardVerificationError(f"學生證{side}不是可辨識的圖片檔。") from exc
    try:
        if image_format not in SUPPORTED_FORMATS:
            raise StudentCardVerificationError("請上傳 JPG、PNG 或 WebP 圖片。")
        width, height = image.size
        if max(width, height) < MIN_WIDTH or min(width, height) < MIN_HEIGHT:
            raise StudentCardVerificationError(
                f"學生證{side}解析度太低，請靠近卡片重新拍攝。"
            )
        ratio = max(width, height) / min(width, height)
        if ratio < 1.15 or ratio > 2.6:
            raise StudentCardVerificationError(
                f"學生證{side}需完整拍到卡片四個邊角。"
            )
        if max(image.size) > 2200:
            image.thumbnail((2200, 2200), Image.Resampling.LANCZOS)
        return image
    except Exception:
        image.close()
        raise


def _ocr(image: Image.Image) -> str:
    try:
        import pytesseract
    except ImportError as exc:
        raise StudentCardVerificationError("學生證辨識服務尚未安裝完成。") from exc

    if os.name == "nt" and not shutil.which("tesseract"):
        default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_path):
            pytesseract.pytesseract.tesseract_cmd = default_path
    prepared = ImageOps.autocontrast(ImageOps.grayscale(image))
    try:
        return pytesseract.image_to_string(
            prepared,
            lang="chi_tra+eng",
            config="--psm 6",
            timeout=18,
        )
    except (RuntimeError, pytesseract.TesseractError, pytesseract.TesseractNotFoundError) as exc:
        raise StudentCardVerificationError("學生證辨識服務暫時無法使用，請稍後再試。") from exc
    finally:
        prepared.close()


def _normalized_ocr(text: str) -> str:
    return re.sub(r"[^A-Z0-9\u4e00-\u9fff]+", "", text.upper())


def _images_are_distinct(front: Image.Image, back: Image.Image) -> bool:
    size = (320, 200)
    front_gray = ImageOps.grayscale(front)
    back_gray = ImageOps.grayscale(back)
    left = right = difference = None
    try:
        left = ImageOps.fit(front_gray, size)
        right = ImageOps.fit(back_gray, size)
        difference = ImageChops.difference(left, right)
        return ImageStat.Stat(difference).mean[0] >= 5.0
    finally:
        if difference is not None:
            difference.close()
        if left is not None:
            left.close()
        if right is not None:
            right.close()
        front_gray.close()
        back_gray.close()


def _verified_department_from_ocr(text: str, expected_school: str) -> str | None:
    """Return only a short department label visibly present on the card.

    Raw OCR, names, and student numbers are deliberately not returned. If the
    card does not expose an unambiguous Chinese department label, school-only
    verification remains valid.
    """

    university = resolve_university(expected_school)
    school_labels = (
        (*university.aliases, university.school_name)
        if university is not None
        else (expected_school,)
    )
    for raw_line in re.split(r"[\r\n]+", unicodedata.normalize("NFKC", text)):
        line = re.sub(r"\s+", "", raw_line)
        if not line:
            continue
        for label in school_labels:
            line = re.sub(
                re.escape(re.sub(r"\s+", "", label)),
                "",
                line,
                flags=re.IGNORECASE,
            )
        line = re.sub(
            r"^(?:系所|科系|就讀系所|就讀學系|DEPARTMENT|DEPT|MAJOR)[:：-]*",
            "",
            line,
            flags=re.IGNORECASE,
        )
        for match in re.findall(r"[\u4e00-\u9fff]{2,24}(?:學系|研究所|學程)", line):
            candidate = re.sub(r"^.*?學院", "", match)
            if (
                4 <= len(candidate) <= 20
                and not any(
                    term in candidate
                    for term in ("學生證", "學生", "姓名", "學號", "大學")
                )
            ):
                return candidate
    return None


def verify_student_cards(
    front_bytes: bytes,
    back_bytes: bytes,
    *,
    expected_school: str = "長庚大學",
    school_signals: tuple[str, ...] | None = None,
) -> StudentCardVerification:
    front = back = None
    try:
        front = _open_card(front_bytes, "正面")
        back = _open_card(back_bytes, "反面")
        if not _images_are_distinct(front, back):
            raise StudentCardVerificationError("正反面圖片過於相似，請分別拍攝學生證兩面。")

        front_ocr = _ocr(front)
        back_ocr = _ocr(back)
        front_text = _normalized_ocr(front_ocr)
        back_text = _normalized_ocr(back_ocr)
        combined = f"{front_text}{back_text}"
        university = resolve_university(expected_school)
        if school_signals is None:
            school_signals = (
                university.student_card_signals
                if university
                else (expected_school,)
            )
        normalized_school_signals = tuple(
            _normalized_ocr(signal) for signal in school_signals
        )
        student_signals = (
            "學生證",
            "STUDENTID",
            "STUDENT",
            "學號",
            "姓名",
            "NAME",
            "DEPARTMENT",
            "有效",
            "VALID",
        )
        if not any(signal in combined for signal in normalized_school_signals):
            raise StudentCardVerificationError(
                f"目前無法辨識{expected_school}校名，請在光線充足處重新拍攝。"
            )
        if not any(signal in combined for signal in student_signals):
            raise StudentCardVerificationError("目前無法確認這是學生證，請避免反光並對焦文字。")
        if len(front_text) < 8 or len(back_text) < 4:
            raise StudentCardVerificationError("部分卡面文字不清楚，請重新拍攝正反面。")

        department_name = _verified_department_from_ocr(
            f"{front_ocr}\n{back_ocr}",
            expected_school,
        )
        checks = ["正反面不同", "校名可辨識", "學生證文字可辨識"]
        if department_name:
            checks.append("學系可辨識")
        return StudentCardVerification(
            school_name=expected_school.strip() or "長庚大學",
            checks=tuple(checks),
            department_name=department_name,
        )
    finally:
        if front is not None:
            front.close()
        if back is not None:
            back.close()
