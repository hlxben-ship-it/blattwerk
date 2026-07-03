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

## Vault

Project knowledge lives in the Glia space at `C:\dev\glia\spaces\blattwerk`.
