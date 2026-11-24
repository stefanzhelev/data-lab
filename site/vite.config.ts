import tailwindcss from '@tailwindcss/vite';
import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// BASE_PATH lets the same build move from lab.stefanzhelev.com (base "")
// to stefanzhelev.com/lab (BASE_PATH=/lab) without code changes.
const base = (process.env.BASE_PATH ?? '') as '' | `/${string}`;

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			// Fully static: every route is prerendered to HTML for Cloudflare Pages.
			adapter: adapter({ pages: 'build', assets: 'build', fallback: '404.html', strict: true }),
			paths: { base },
			prerender: { handleHttpError: 'fail' }
		})
	]
});
