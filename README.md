# Blattwerk

Printable Übungsblatt generator for a preschool child. One HTML file, no build step.

## Use

Open `index.html` in a browser → pick a Vorlage, adjust options → **Drucken** (disable
"Kopf- und Fußzeilen" in the print dialog for a clean sheet). Output is one A4 page.

## Add a worksheet template

Everything layout-specific lives in the `TEMPLATES` registry in `index.html`.
A template is one object:

```js
myTemplate: {
  name: "…",                    // shown in the picker
  description: "…",
  options: [ /* declarative — the shell renders the form */ ],
  render(opts, ctx) { /* return the sheet body as a DOM node */ },
}
```

The shell owns the sheet header (Name / Datum / Titel), the option form, the
true-size A4 preview, and printing. `ctx` provides the usable page area in mm.

## Font

The worksheet face is **Blattschrift**, embedded as base64 in `index.html` so every OS prints
the same shapes. It is Andika (SIL, OFL) patched for German Druckschrift: single-storey `a`
and `g`, capital `I` as a bare stem, `1` without a foot serif, open `4`, barred `7`. The digit
forms are baked into the font's `cmap`, not set via `font-feature-settings`, so they survive
renderers that ignore OpenType features.

The app itself still has no build step — the font is built once, out of band:

```
pip install --user fonttools brotli
python tools/build_font.py     # -> fonts/*.woff2 + the @font-face block to paste
```

`AVG_CHAR_EM` in `index.html` is a *measured* property of this font. Re-measure it if the font
ever changes, or the Lesen sentences will wrap and push a card onto a second page.

License: `fonts/OFL.txt`. "Andika" and "SIL" are Reserved Font Names, hence the rename.

## Vault

Project knowledge lives in the Glia space at `C:\dev\glia\spaces\blattwerk`.
