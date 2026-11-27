// Observable Framework version of the marimo gallery, published at lab.stefanzhelev.com/observable/.
// Same files (data/input/) and the same SQL as bi/marimo and bi/evidence.
// Options: https://observablehq.com/framework/config

// The Data Lab wordmark (same as bi/evidence/static/data-lab.svg), inline so no file has to be copied.
const logo = `<svg xmlns="http://www.w3.org/2000/svg" width="112" height="24" viewBox="0 0 112 24" role="img" aria-label="Data Lab">
  <g fill="none" stroke="#3b82f6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M9 2.5h6M10 2.5v6.2L4.3 18.6A2 2 0 0 0 6 21.5h12a2 2 0 0 0 1.7-2.9L14 8.7V2.5"/>
  </g>
  <path d="M6.6 15.5h10.8l1.6 2.9a.9.9 0 0 1-.8 1.3H5.8a.9.9 0 0 1-.8-1.3z" fill="#3b82f6" fill-opacity=".35"/>
  <circle cx="11" cy="13" r="1" fill="#3b82f6"/><circle cx="13.6" cy="11" r=".7" fill="#3b82f6"/>
  <text x="28" y="17" fill="#3b82f6" font-family="ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="15" font-weight="700">Data Lab</text>
</svg>`;

export default {
  root: "src",
  base: "/observable/", // served next to the barnacles gallery and /evidence/
  title: "Data Lab · Observable",
  theme: "dark",
  header: `<a href="/" style="display:inline-flex;align-items:center">${logo}</a>`,
  footer: "", // no "Built with Observable" line (as on the Evidence site)
  pages: [
    {name: "Example", path: "/example"},
    {name: "Energy", pages: [{name: "Electricity transition", path: "/energy/energy"}]},
    {name: "Practice", pages: [{name: "Customer orders", path: "/practice/customer-orders"}]}
  ],
  pager: false,
  // Python data loaders run in the repo's uv environment (it has DuckDB); paths are relative to bi/observable.
  interpreters: {".py": ["uv", "run", "--project", "../..", "python"]}
};
