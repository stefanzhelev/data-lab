<script lang="ts">
	import './layout.css';
	import favicon from '#lib/assets/favicon.svg';
	import { resolve } from '$app/paths';
	import { DATA_URL, REPO_URL } from '#lib/manifest.js';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="flex min-h-svh flex-col bg-background text-foreground">
	<header class="border-b">
		<nav class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
			<a href={resolve('/')} class="font-semibold tracking-tight">Data Lab</a>
			<div class="flex items-center gap-4 text-sm text-muted-foreground">
				<a href={resolve('/')} class="hover:text-foreground">Demos</a>
				<a href={DATA_URL + '/'} class="hover:text-foreground">Data</a>
				<a href={REPO_URL} class="hover:text-foreground">GitHub</a>
				<!-- Handled by the inline script in app.html, so it also works on
				     dashboard pages, which ship no SvelteKit JS (csr = false). -->
				<button
					type="button"
					class="hover:text-foreground"
					data-theme-toggle
					aria-label="Toggle dark mode"
				>
					◐
				</button>
			</div>
		</nav>
	</header>

	<main class="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
		{@render children()}
	</main>

	<footer class="border-t">
		<div class="mx-auto max-w-6xl px-4 py-4 text-xs text-muted-foreground">
			Stefan Zhelev · Dashboards run in your browser with
			<a class="underline" href="https://marimo.io">marimo</a> + DuckDB (WebAssembly) ·
			<a class="underline" href={REPO_URL}>source</a>
		</div>
	</footer>
</div>
