# arc-protocol

The shared source of truth for the ARC video/telemetry network's wire format:
framing, COBS, CRC-16/CCITT-FALSE, addressing, a static destination router, a
reliable ACK/retry transport, and the per-family message catalogs.

It ships **two implementations** — portable C (for firmware: STM32, Teensy,
ESP32, AVR) and pure Python (for the Pi control plane and ground tools) — that
are held byte-identical by a shared set of canonical test vectors. Neither side
can drift without a test failing.

## Why one repo, two languages

C firmware and Python hosts don't share source files; they share **this repo**
and a **conformance contract** (`vectors/test_vectors.txt`). Each toolchain
consumes only its own subtree:

```
arc-protocol/
├── library.json          PlatformIO manifest — repo root IS the C library
├── Makefile              C build + tests + vector generation
├── src/                  C: arc_protocol, arc_router, arc_reliable, arc_messages_*
├── test/                 C unit tests
├── examples/gen_vectors.c  emits the canonical vectors
├── vectors/
│   └── test_vectors.txt  THE contract both languages test against
└── python/
    ├── arc_protocol/     Python: protocol, router, reliable, messages
    └── tests/            Python unit tests + vector conformance
```

## Consuming it

**Firmware (PlatformIO)** — the repo root is a valid library:

```ini
lib_deps = https://github.com/<you>/arc-protocol.git#v1.0.0
# or, for local development against a sibling checkout:
# lib_deps = symlink://../arc-protocol
```

**Python (control plane / ground tools)** — pin the same commit:

```bash
# as a git submodule, then put python/ on the path; or:
pip install "git+https://github.com/<you>/arc-protocol.git@v1.0.0#subdirectory=python"
```

```python
from arc_protocol import protocol, messages, router, reliable
```

Both consumers pin the same tag → both speak the identical wire format.

## Building and testing

C (mirrors the Makefile; on hosts without `make`, invoke `gcc` directly):

```bash
make test                              # build + run the C unit tests
make vectors > vectors/test_vectors.txt   # regenerate the canonical vectors
```

Python:

```bash
cd python && python -m unittest discover -s tests
```

The `tests/test_vectors_conformance.py` case parses `vectors/test_vectors.txt`
and asserts the Python build/encode/parse/decode reproduces the C output
exactly. **Regenerate the vectors and run both test suites after any change to
the wire format.**

## Scope

This is a pure library — no I/O, no transports, no application logic. Link
transports (UART/COBS, TCP), node orchestration, video, and routing-node
firmware live in the consuming repos and depend on this one. See `src/` headers
for the address map, families, and message-type catalogs.