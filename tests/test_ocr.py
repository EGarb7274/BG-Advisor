import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).parent.parent))

from ocr import capture_crop


def test_capture_crop_crops_to_region():
    mock_img = MagicMock()
    mock_img.crop.return_value = mock_img
    with patch("ocr.ImageGrab.grab", return_value=mock_img):
        result = capture_crop([100, 200, 300, 400])
    mock_img.crop.assert_called_once_with((100, 200, 400, 600))  # x, y, x+w, y+h
    assert result is mock_img


def test_capture_crop_none_returns_full_screen():
    mock_img = MagicMock()
    with patch("ocr.ImageGrab.grab", return_value=mock_img):
        result = capture_crop(None)
    mock_img.crop.assert_not_called()
    assert result is mock_img


from ocr import run_ocr, match_tribes, scan_tribes, ALL_TRIBES


def test_run_ocr_returns_text_from_lines():
    mock_img = MagicMock()
    mock_result = MagicMock()
    mock_result.lines = [MagicMock(text="Murloc"), MagicMock(text="Pirates")]
    with patch("ocr.asyncio.run", return_value=mock_result):
        lines = run_ocr(mock_img)
    assert "Murloc" in lines
    assert "Pirates" in lines


def test_run_ocr_returns_empty_on_exception():
    mock_img = MagicMock()
    with patch("ocr.asyncio.run", side_effect=Exception("OCR failed")):
        lines = run_ocr(mock_img)
    assert lines == []


def test_match_tribes_exact_match():
    matched, unmatched = match_tribes(["Murloc", "Mech"], ALL_TRIBES)
    assert "Murloc" in matched
    assert "Mech" in matched
    assert unmatched == []


def test_match_tribes_fuzzy_corrects_typo():
    matched, unmatched = match_tribes(["Murioc", "Mechs"], ALL_TRIBES)
    assert "Murloc" in matched
    assert "Mech" in matched


def test_match_tribes_flags_unrecognized_tokens():
    matched, unmatched = match_tribes(["XyzGarbage123"], ALL_TRIBES)
    assert matched == []
    assert "XyzGarbage123" in unmatched


def test_match_tribes_no_duplicates():
    matched, _ = match_tribes(["Murioc", "Murlo c"], ALL_TRIBES)
    assert matched.count("Murloc") == 1


def test_scan_tribes_integrates_capture_and_ocr():
    mock_img = MagicMock()
    mock_result = MagicMock()
    mock_result.lines = [MagicMock(text="Murloc"), MagicMock(text="Dragon")]
    with patch("ocr.ImageGrab.grab", return_value=mock_img), \
         patch("ocr.asyncio.run", return_value=mock_result):
        matched, unmatched = scan_tribes(None)
    assert "Murloc" in matched
    assert "Dragon" in matched
    assert unmatched == []
