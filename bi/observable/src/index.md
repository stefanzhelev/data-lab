---
title: Data Lab · Observable
toc: false
---

# Data Lab · Observable

The [marimo gallery](https://lab.stefanzhelev.com/) rebuilt in
[Observable Framework](https://observablehq.com/framework/): the same files from `data/input/` and
the same SQL, so each dashboard can be compared with its [marimo](https://lab.stefanzhelev.com/) and
[Evidence](https://lab.stefanzhelev.com/evidence/) versions.

```js
// One card per page; `thumb` is the screenshot name written by bi/thumbnails.py in CI
// (thumbnails/<thumb>-dark.png). Without it (e.g. `npm run dev`) the card shows a letter.
const LAB = "https://lab.stefanzhelev.com";
const cards = [
  {
    title: "Customer orders", href: "./practice/customer-orders", thumb: "practice-customer-orders", folder: "Practice",
    description: "Cleaning, quarantining and reconciling a deliberately messy orders feed.",
    marimo: `${LAB}/notebooks/practice/customer-orders/`, evidence: `${LAB}/evidence/practice/customer-orders/`
  },
  {
    title: "Electricity transition", href: "./energy/energy", thumb: "energy-energy", folder: "Energy",
    description: "Who is moving off fossil electricity? OWID energy data in six charts.",
    marimo: `${LAB}/notebooks/energy/energy/`, evidence: `${LAB}/evidence/energy/energy/`
  },
  {
    title: "Example", href: "./example", thumb: "example",
    description: "Sliders that re-run a query in your browser.",
    marimo: `${LAB}/notebooks/example/`, evidence: `${LAB}/evidence/example/`
  }
];

function card({title, href, thumb, folder, description, marimo, evidence}) {
  const image = html`<img src="./thumbnails/${thumb}-dark.png" alt="" loading="lazy">`;
  const fallback = html`<div class="thumb-fallback">${(folder ?? title)[0]}</div>`;
  image.onerror = () => image.replaceWith(fallback);
  return html`<div class="card gallery-card">
    <a class="thumb" href=${href} aria-label=${title}>${image}</a>
    <div class="body">
      <a class="title" href=${href}>${title}</a>
      <p>${description}</p>
      <div class="meta">
        ${folder ? html`<span class="badge">${folder}</span>` : ""}
        <span class="links"><a href=${marimo}>marimo</a> · <a href=${evidence}>Evidence</a></span>
      </div>
    </div>
  </div>`;
}

display(html`<div class="grid grid-cols-3">${cards.map(card)}</div>`);
```

<style>
.gallery-card { padding: 0; overflow: hidden; display: flex; flex-direction: column; }
.gallery-card:hover { border-color: var(--theme-foreground-focus); }
.gallery-card .thumb { display: block; aspect-ratio: 16 / 9; overflow: hidden; border-bottom: solid 1px var(--theme-foreground-faintest); background: var(--theme-background); }
.gallery-card .thumb img { width: 100%; height: 100%; object-fit: cover; object-position: top; display: block; }
.gallery-card .thumb-fallback { height: 100%; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: 600; color: var(--theme-foreground-muted); }
.gallery-card .body { padding: 1rem; display: flex; flex-direction: column; gap: 0.5rem; flex: 1; }
.gallery-card .title { font-weight: 600; font-size: 1.05rem; color: var(--theme-foreground); text-decoration: none; }
.gallery-card .title:hover { color: var(--theme-foreground-focus); }
.gallery-card p { margin: 0; color: var(--theme-foreground-muted); font-size: 0.9rem; line-height: 1.4; }
.gallery-card .meta { margin-top: auto; padding-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; }
.gallery-card .badge { border: solid 1px var(--theme-foreground-faint); border-radius: 999px; padding: 0.1rem 0.5rem; font-family: var(--monospace); color: var(--theme-foreground-muted); }
.gallery-card .links { margin-left: auto; }
</style>
