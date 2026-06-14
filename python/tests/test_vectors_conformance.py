"""Cross-language conformance: the Python implementation must reproduce the
canonical vectors emitted by the C ``gen_vectors`` tool.

``vectors/test_vectors.txt`` is the single source of truth. Regenerate it with
``make vectors > vectors/test_vectors.txt`` (or build examples/gen_vectors.c)
after any wire-format change; this test then proves Python still matches C.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from arc_protocol import protocol as p

VECTORS_FILE = Path(__file__).resolve().parents[2] / "vectors" / "test_vectors.txt"

_FIELDS_RE = re.compile(
    r"src=0x([0-9a-f]+) dst=0x([0-9a-f]+) flags=0x([0-9a-f]+) "
    r"session=(\d+) seq=(\d+) family=0x([0-9a-f]+) type=0x([0-9a-f]+)"
)


def parse_vectors(text: str) -> list[dict]:
    vectors: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        if line.startswith("vector: "):
            cur = {"name": line[len("vector: "):].strip(), "payload": ""}
            vectors.append(cur)
            continue
        if cur is None:
            continue
        s = line.strip()
        m = _FIELDS_RE.match(s)
        if m:
            cur["src"] = int(m.group(1), 16)
            cur["dst"] = int(m.group(2), 16)
            cur["flags"] = int(m.group(3), 16)
            cur["session"] = int(m.group(4))
            cur["seq"] = int(m.group(5))
            cur["family"] = int(m.group(6), 16)
            cur["type"] = int(m.group(7), 16)
            continue
        for label in ("payload", "frame", "encoded"):
            if s.startswith(label):
                cur[label] = s[len(label):].strip()
                break
    return vectors


class TestCVectorConformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not VECTORS_FILE.exists():
            raise unittest.SkipTest(
                f"missing {VECTORS_FILE}; run 'make vectors > vectors/test_vectors.txt'"
            )
        cls.vectors = parse_vectors(VECTORS_FILE.read_text())
        if not cls.vectors:
            raise AssertionError(f"no vectors parsed from {VECTORS_FILE}")

    def test_build_and_encode_match(self):
        for v in self.vectors:
            with self.subTest(vector=v["name"]):
                frame = p.build_frame(
                    v["src"], v["dst"], v["flags"], v["session"],
                    v["seq"], v["family"], v["type"], bytes.fromhex(v["payload"]),
                )
                self.assertEqual(frame.hex(), v["frame"])
                self.assertEqual(p.cobs_encode(frame).hex(), v["encoded"])

    def test_parse_and_decode_match(self):
        for v in self.vectors:
            with self.subTest(vector=v["name"]):
                frame = p.parse_frame(bytes.fromhex(v["frame"]))
                self.assertEqual(frame.src, v["src"])
                self.assertEqual(frame.dst, v["dst"])
                self.assertEqual(frame.flags, v["flags"])
                self.assertEqual(frame.session, v["session"])
                self.assertEqual(frame.seq, v["seq"])
                self.assertEqual(frame.family, v["family"])
                self.assertEqual(frame.type, v["type"])
                self.assertEqual(frame.payload, bytes.fromhex(v["payload"]))
                self.assertEqual(p.decode_frame(bytes.fromhex(v["encoded"])), frame)


if __name__ == "__main__":
    unittest.main()