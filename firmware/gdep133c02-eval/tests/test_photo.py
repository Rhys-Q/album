import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from convert_photo import encode, convert, WIDTH, HEIGHT
from PIL import Image


class PhotoTests(unittest.TestCase):
    def test_header_and_packing(self):
        frame = bytes([0, 5]) * (WIDTH * HEIGHT // 2)
        file = encode(frame)
        self.assertEqual(len(file), 960032)
        self.assertEqual(file[:4], b'EPF1')
        self.assertEqual(file[32:], bytes([5]) * 960000)
        self.assertEqual(struct.unpack_from('<I', file, 20)[0], zlib.crc32(file[32:]))

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            encode(bytes(10))
        with self.assertRaises(ValueError):
            encode(bytes([6]) * (WIDTH * HEIGHT))

    def test_letterbox_and_palette(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'square.png'
            Image.new('RGB', (200, 200), 'black').save(source)
            file = convert(source)
        payload = file[32:]
        self.assertEqual(payload[0], 0x11)
        self.assertEqual(payload[(600 * WIDTH + 800)//2], 0)
        self.assertTrue(all((v >> 4) <= 5 and (v & 15) <= 5 for v in payload))

    def test_transparency(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'transparent.png'
            Image.new('RGBA', (16, 12), (0, 0, 0, 0)).save(source)
            file = convert(source)
        self.assertEqual(file[32:], bytes([0x11]) * 960000)


if __name__ == '__main__':
    unittest.main()
