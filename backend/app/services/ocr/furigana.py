"""Furigana printed on the page.

The OCR engine reads printed furigana as separate thin lines (or tiny blocks of their own), which
would otherwise end up as stray kana lines in the document. A line is furigana when it is all
kana, much thinner than a line it sits against (above it in horizontal text, to its right in
vertical text), and overlaps that line along the reading direction. Its position along the base
line says which characters it reads; it is attached to the kanji run there, or dropped if it sits
over no kanji.
"""

import re
from dataclasses import dataclass, replace

from app.services.ocr.base import Ruby, TextBlock, TextLine

# Furigana are about half the size of the text they annotate.
MAX_THICKNESS_RATIO = 0.6
# How far past a kanji run's ends (in characters) a furigana's centre may fall.
RUN_SLACK = 0.3
# How far (in base-line thicknesses) a furigana line may sit from its base line.
MAX_GAP = 0.6
MAX_INTRUSION = 0.35

_KANA = re.compile(r"^[ぁ-ゟ゠-ヿー]+$")
_KANJI_RUN = re.compile(r"[一-鿿㐀-䶿々]+")


@dataclass(frozen=True)
class _Ref:
    block: int
    line: int
    vertical: bool


def _is_kana(text: str) -> bool:
    return bool(_KANA.match(text))


def _sits_on(ruby: TextLine, base: TextLine, vertical: bool) -> bool:
    """Is `ruby` placed where furigana for `base` would be?"""
    if ruby.thickness > MAX_THICKNESS_RATIO * base.thickness:
        return False
    r, b, t = ruby.box, base.box, base.thickness
    cx, cy = r.center
    if vertical:  # furigana to the right of the column
        return b.y1 <= cy <= b.y2 and b.x2 - MAX_INTRUSION * t <= r.x1 <= b.x2 + MAX_GAP * t
    # furigana above the line
    return b.x1 <= cx <= b.x2 and b.y1 - MAX_GAP * t <= r.y2 <= b.y1 + MAX_INTRUSION * t


def _position(ruby: TextLine, base: TextLine, vertical: bool) -> float:
    """Where the furigana's centre falls along the base line, in characters."""
    r, b = ruby.box, base.box
    if vertical:
        along = (r.center[1] - b.y1) / max(b.height, 1)
    else:
        along = (r.center[0] - b.x1) / max(b.width, 1)
    return along * len(base.text)


def _kanji_run_at(text: str, position: float) -> tuple[int, int] | None:
    """The kanji run under `position`, with a little slack for imprecise boxes."""
    for match in _KANJI_RUN.finditer(text):
        if match.start() - RUN_SLACK <= position <= match.end() + RUN_SLACK:
            return match.start(), match.end()
    return None


def extract(blocks: list[TextBlock]) -> list[TextBlock]:
    """Moves printed furigana onto the text they annotate. Blocks left empty are dropped."""
    refs = [_Ref(bi, li, block.vertical) for bi, block in enumerate(blocks) for li in range(len(block.lines))]
    line_at = {(r.block, r.line): blocks[r.block].lines[r.line] for r in refs}

    found: dict[tuple[int, int], dict[tuple[int, int], list[tuple[float, str]]]] = {}
    consumed: set[tuple[int, int]] = set()

    for ref in refs:
        candidate = line_at[(ref.block, ref.line)]
        if not _is_kana(candidate.text):
            continue
        bases = [
            base
            for base in refs
            if base != ref and _sits_on(candidate, line_at[(base.block, base.line)], base.vertical)
        ]
        if not bases:
            continue  # an ordinary kana line
        base = max(bases, key=lambda b: line_at[(b.block, b.line)].thickness)
        base_line = line_at[(base.block, base.line)]
        consumed.add((ref.block, ref.line))
        position = _position(candidate, base_line, base.vertical)
        run = _kanji_run_at(base_line.text, position)
        if run is not None:  # furigana over kana carry nothing worth keeping
            found.setdefault((base.block, base.line), {}).setdefault(run, []).append(
                (position, candidate.text)
            )

    result: list[TextBlock] = []
    for bi, block in enumerate(blocks):
        lines: list[TextLine] = []
        for li, line in enumerate(block.lines):
            if (bi, li) in consumed:
                continue
            runs = found.get((bi, li), {})
            # Several furigana over one run (one per kanji) read in order along the line.
            ruby = tuple(
                Ruby(start, end, "".join(kana for _, kana in sorted(parts)))
                for (start, end), parts in sorted(runs.items())
            )
            lines.append(replace(line, ruby=line.ruby + ruby))
        if lines:
            result.append(replace(block, lines=lines))
    return result
