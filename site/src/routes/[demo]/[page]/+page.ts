import { error } from '@sveltejs/kit';
import { demos } from '#lib/manifest.js';
import type { EntryGenerator, PageLoad } from './$types';

// The page is plain prerendered HTML with no SvelteKit client JS: the marimo
// islands runtime owns these DOM nodes, so Svelte must not hydrate over them.
export const csr = false;

const fragments = import.meta.glob('/src/generated/**/*.html', {
	query: '?raw',
	import: 'default',
	eager: true
}) as Record<string, string>;

export const entries: EntryGenerator = () =>
	demos.flatMap((d) => d.pages.map((p) => ({ demo: d.slug, page: p.slug })));

export const load: PageLoad = ({ params }) => {
	const demo = demos.find((d) => d.slug === params.demo);
	const page = demo?.pages.find((p) => p.slug === params.page);
	if (!demo || !page) error(404, 'Dashboard not found');

	const prefix = `/src/generated/${demo.slug}/${page.slug}`;
	return {
		demo,
		page,
		head: fragments[`${prefix}.head.html`],
		body: fragments[`${prefix}.body.html`]
	};
};
