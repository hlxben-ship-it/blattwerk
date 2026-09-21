#!/usr/bin/env python3
"""Build "Blattschrift" — the worksheet face embedded in index.html.

Base: Andika (SIL, OFL) — a sans designed for beginning readers, so a and g
are single-storey out of the box, which classic Comic-Sans-style faces are not.

Three German Druckschrift digit forms are hard-wired into cmap rather than left
as OpenType features, so they survive renderers that ignore font-feature-settings
(print pipelines, PDF engines):

    1 -> one.NoBase   (cv01)  no foot serif
    4 -> four.Open    (cv04)  open at the top
    7 -> seven.Bar    (cv07)  with crossbar

Capital I has no alternate in Andika and ships with serifs, so its outline is
replaced by a plain stem matching the lowercase l.

"Andika" and "SIL" are Reserved Font Names under the OFL, so the modified font
is renamed to "Blattschrift". Copyright and license notices are kept intact and
fonts/OFL.txt ships alongside.

Usage:  python tools/build_font.py
Needs:  pip install --user fonttools brotli
Writes: fonts/Blattschrift-{Regular,Bold}.woff2 + the base64 @font-face block
        on stdout, ready to paste into index.html.
"""
import base64
import io
import pathlib
import urllib.request
import zipfile

from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.subset import main as subset_main

SOURCE   = "https://software.sil.org/downloads/r/andika/Andika-6.200.zip"
ROOT     = pathlib.Path(__file__).resolve().parent.parent
FONTDIR  = ROOT / "fonts"
BUILDDIR = FONTDIR / ".build"

NEW_FAMILY = "Blattschrift"
CAP_TOP    = 1460   # Andika's existing cap-I height, in font units (upm 2048)
SIDE       = 220    # side bearing for the rebuilt capital I

DIGITS = {
    0x31: "one.NoBase",
    0x34: "four.Open",
    0x37: "seven.Bar",
}

# Subset: Latin + German umlauts + the punctuation and math signs the
# worksheets actually print. Keeps each weight around 8 KB.
UNICODES = (
    "U+0020-007E,U+00A0,U+00C4,U+00D6,U+00DC,U+00E4,U+00F6,U+00FC,U+00DF,"
    "U+00B7,U+00D7,U+00F7,U+2010-2015,U+2018,U+2019,U+201A,U+201C,U+201D,"
    "U+201E,U+2022,U+2026,U+2212,U+2260,U+2264,U+2265,U+2190-2193,U+00A9"
)
LAYOUT_FEATURES = "kern,ccmp,mark,mkmk,liga"


def fetch_source():
    """Download + unpack the Andika release once; reuse it afterwards."""
    BUILDDIR.mkdir(parents=True, exist_ok=True)
    if (BUILDDIR / "Andika-Regular.ttf").exists():
        return
    print(f"downloading {SOURCE}")
    blob = urllib.request.urlopen(SOURCE).read()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for member in z.namelist():
            name = pathlib.Path(member).name
            if name in ("Andika-Regular.ttf", "Andika-Bold.ttf", "OFL.txt", "FONTLOG.txt"):
                (BUILDDIR / name).write_bytes(z.read(member))
    # the license has to travel with the font
    (FONTDIR / "OFL.txt").write_bytes((BUILDDIR / "OFL.txt").read_bytes())


def plain_capital_i(font):
    """Andika's I has serifs and no cv alternate — rebuild it as a bare stem."""
    glyf, hmtx = font["glyf"], font["hmtx"]
    stem = glyf["l"].xMax - glyf["l"].xMin
    new_adv = stem + 2 * SIDE
    old_adv, _ = hmtx["I"]
    delta = old_adv - new_adv

    pen = TTGlyphPen(None)
    x0, x1 = SIDE, SIDE + stem
    pen.moveTo((x0, 0)); pen.lineTo((x1, 0)); pen.lineTo((x1, CAP_TOP)); pen.lineTo((x0, CAP_TOP))
    pen.closePath()
    glyf["I"] = pen.glyph()
    hmtx["I"] = (new_adv, SIDE)

    # Í Î Ï Ì … reference I as a component; re-centre them over the narrower stem
    fixed = 0
    for name in font.getGlyphOrder():
        g = glyf[name]
        if name == "I" or not g.isComposite():
            continue
        if not any(c.glyphName == "I" for c in g.components):
            continue
        for c in g.components:
            c.x -= delta // 2
        adv, lsb = hmtx[name]
        hmtx[name] = (max(adv - delta, 0), lsb - delta // 2)
        fixed += 1
    return stem, old_adv, new_adv, fixed


def bake_digits(font):
    order = set(font.getGlyphOrder())
    for table in font["cmap"].tables:
        for cp, target in DIGITS.items():
            if cp in table.cmap:
                assert target in order, f"missing alternate glyph {target}"
                table.cmap[cp] = target


def rename(font, weight):
    """OFL: a modified font may not carry the Reserved Font Name."""
    full = f"{NEW_FAMILY} {weight}"
    ps   = f"{NEW_FAMILY}-{weight}"
    for rec in font["name"].names:
        if rec.nameID == 1:    # family
            rec.string = NEW_FAMILY
        elif rec.nameID == 2:  # subfamily
            rec.string = weight
        elif rec.nameID == 3:  # unique id
            rec.string = f"{full}: derived from Andika 6.200 (SIL, OFL)"
        elif rec.nameID == 4:  # full name
            rec.string = full
        elif rec.nameID == 6:  # postscript name
            rec.string = ps
        elif rec.nameID in (16, 17, 18, 20, 21, 22):  # typographic / compat names
            rec.string = NEW_FAMILY if rec.nameID in (16, 21) else weight
    # nameIDs 0 (copyright), 13 (license), 14 (license URL) are deliberately kept


def build(weight):
    src = BUILDDIR / f"Andika-{weight}.ttf"
    ttf = BUILDDIR / f"{NEW_FAMILY}-{weight}.ttf"
    out = FONTDIR / f"{NEW_FAMILY}-{weight}.woff2"

    font = TTFont(src)
    stem, old_adv, new_adv, fixed = plain_capital_i(font)
    bake_digits(font)
    rename(font, weight)
    font.save(ttf)
    print(f"{weight}: I stem={stem} advance {old_adv}->{new_adv}, {fixed} composites re-centred")

    subset_main([
        str(ttf),
        f"--unicodes={UNICODES}",
        f"--layout-features={LAYOUT_FEATURES}",
        "--flavor=woff2",
        f"--output-file={out}",
        "--no-hinting",
        "--desubroutinize",
    ])
    print(f"{weight}: {out.name} {out.stat().st_size / 1024:.1f} KB")
    return out


def face(path, weight_value):
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        "  @font-face {\n"
        f'    font-family: "{NEW_FAMILY}";\n'
        f"    font-weight: {weight_value};\n"
        "    font-style: normal;\n"
        "    font-display: swap;\n"
        f"    src: url(data:font/woff2;base64,{b64}) format('woff2');\n"
        "  }\n"
    )


if __name__ == "__main__":
    fetch_source()
    faces = [
        face(build("Regular"), 400),
        face(build("Bold"), 700),
    ]
    snippet = FONTDIR / "blattschrift-fontface.css"
    snippet.write_text("".join(faces), encoding="utf-8")
    print(f"\n@font-face block -> {snippet} ({snippet.stat().st_size / 1024:.0f} KB)")
    print("paste it over the existing @font-face rules in index.html")
