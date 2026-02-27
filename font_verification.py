from fonttools import ttLib
from dataclasses import dataclass, field


# --- Predefined ranges you can reuse or extend ---
UNICODE_RANGES = {
    "ascii_control":        (0x0000, 0x001F, "ASCII Control Characters"),
    "ascii_printable":      (0x0020, 0x007E, "ASCII Printable Characters"),
    "latin_1_supplement":   (0x0080, 0x00FF, "Latin-1 Supplement"),
    "latin_extended_a":     (0x0100, 0x017F, "Latin Extended-A"),
    "latin_extended_b":     (0x0180, 0x024F, "Latin Extended-B"),
    "greek_coptic":         (0x0370, 0x03FF, "Greek and Coptic"),
    "cyrillic":             (0x0400, 0x04FF, "Cyrillic"),
    "hebrew":               (0x0590, 0x05FF, "Hebrew"),
    "arabic":               (0x0600, 0x06FF, "Arabic"),
    "thai":                 (0x0E00, 0x0E7F, "Thai"),
    "general_punctuation":  (0x2000, 0x206F, "General Punctuation"),
    "currency_symbols":     (0x20A0, 0x20CF, "Currency Symbols"),
    "letterlike_symbols":   (0x2100, 0x214F, "Letterlike Symbols"),
    "arrows":               (0x2190, 0x21FF, "Arrows"),
    "math_operators":       (0x2200, 0x22FF, "Mathematical Operators"),
    "box_drawing":          (0x2500, 0x257F, "Box Drawing"),
    "emoji_misc":           (0x2600, 0x26FF, "Miscellaneous Symbols (Emoji block)"),
    "emoji_dingbats":       (0x2700, 0x27BF, "Dingbats (Emoji block)"),
    "cjk_unified":          (0x4E00, 0x9FFF, "CJK Unified Ideographs"),
    "emoji_main":           (0x1F300, 0x1F9FF, "Emoji Main Block"),
}


@dataclass
class RangeResult:
    name:            str
    start:           int
    end:             int
    total:           int
    supported_count: int
    missing:         list[tuple[int, str]] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        return (self.supported_count / self.total * 100) if self.total else 0.0

    @property
    def fully_supported(self) -> bool:
        return self.supported_count == self.total


def verify_range(font_path: str, *ranges: str | tuple) -> dict[str, RangeResult]:
    """
    Verify font coverage for one or more Unicode ranges.

    Each range can be:
      - A key from UNICODE_RANGES         e.g. "ascii_printable"
      - A custom tuple (start, end, name) e.g. (0x0020, 0x007E, "My Range")
      - A custom tuple (start, end)       e.g. (0x0020, 0x007E)  — name auto-generated
    """
    tt = ttLib.TTFont(font_path)
    cmap = tt.getBestCmap()

    if cmap is None:
        raise ValueError("Font has no usable cmap table.")

    supported_codepoints = set(cmap.keys())
    results = {}

    for r in ranges:
        # Resolve the range definition
        if isinstance(r, str):
            if r not in UNICODE_RANGES:
                raise ValueError(f"Unknown range key '{r}'. Available: {list(UNICODE_RANGES.keys())}")
            start, end, name = UNICODE_RANGES[r]
        elif isinstance(r, tuple):
            start, end = r[0], r[1]
            name = r[2] if len(r) > 2 else f"U+{start:04X}–U+{end:04X}"
        else:
            raise TypeError(f"Range must be a string key or tuple, got {type(r)}")

        block = range(start, end + 1)
        missing = [(cp, chr(cp)) for cp in block if cp not in supported_codepoints]

        results[name] = RangeResult(
            name=name,
            start=start,
            end=end,
            total=len(block),
            supported_count=len(block) - len(missing),
            missing=missing,
        )

    return results


def print_report(results: dict[str, RangeResult], show_missing: bool = False) -> None:
    print(f"\n{'Range':<40} {'Coverage':>10}  {'Supported':>12}  Status")
    print("-" * 80)
    for name, r in results.items():
        status = "✓ Full" if r.fully_supported else "✗ Partial"
        print(f"{name:<40} {r.coverage:>9.1f}%  {r.supported_count:>5}/{r.total:<5}   {status}")
        if show_missing and r.missing:
            # Print up to 20 missing chars to avoid flooding the terminal
            preview = r.missing[:20]
            chars = " ".join(f"U+{cp:04X}({ch!r})" for cp, ch in preview)
            ellipsis = f" ... +{len(r.missing) - 20} more" if len(r.missing) > 20 else ""
            print(f"  {'Missing:':<10} {chars}{ellipsis}")
    print()


# --- Usage ---
font_path = "MyFont.ttf"

results = verify_range(
    font_path,
    # Pass predefined range keys
    "ascii_printable",
    "latin_1_supplement",
    "currency_symbols",
    "emoji_main",
    # Or pass a fully custom range as a tuple
    (0x2600, 0x26FF, "Misc Symbols Custom Check"),
)

print_report(results, show_missing=True)
```

**Example output:**
```
Range                                     Coverage     Supported  Status
--------------------------------------------------------------------------------
ASCII Printable Characters                   100.0%     95/95     ✓ Full
Latin-1 Supplement                            82.3%    105/128    ✗ Partial
  Missing:    U+0080('...') U+0081('...') ... +20 more
Currency Symbols                              53.3%     16/48     ✗ Partial
  Missing:    U+20A0('₠') U+20A1('₡') U+20A2('₢') ...
Emoji Main Block                               0.0%      0/1792   ✗ Partial
Misc Symbols Custom Check                     48.0%    122/256    ✗ Partial
