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
