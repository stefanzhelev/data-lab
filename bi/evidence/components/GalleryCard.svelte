<!--
	A gallery card for the index page, styled like the barnacles gallery cards.
	Thumbnails are screenshots of each page that CI takes after the build (bi/thumbnails.py evidence)
	and serves at /evidence/thumbnails/<thumb>.png and <thumb>-dark.png. Without them
	(e.g. `npm run dev`) the card shows the folder name instead.

	Used by Gallery.svelte; on its own:
	<GalleryCard title="Customer orders" href="/practice/customer-orders" thumb="practice-customer-orders"
		folder="Practice" description="…" marimo="https://lab.stefanzhelev.com/notebooks/practice/customer-orders/" />
-->
<script>
	import { onMount } from 'svelte';
	import { addBasePath } from '@evidence-dev/sdk/utils/svelte';

	export let title;
	export let href; // page path inside the Evidence site, e.g. /practice/customer-orders
	export let thumb; // thumbnail name, see thumbnails.py
	export let description = '';
	export let folder = undefined; // badge, e.g. "Practice"
	export let marimo = undefined; // URL of the same dashboard in the marimo gallery

	let missing = false;
	// Images are added in the browser only: thumbnails are made after `npm run build`, and the
	// build's prerender step would otherwise fail on the (not yet existing) image URLs.
	let mounted = false;
	onMount(() => (mounted = true));
	$: url = addBasePath(href);
	$: light = addBasePath(`/thumbnails/${thumb}.png`);
	$: dark = addBasePath(`/thumbnails/${thumb}-dark.png`);
</script>

<div
	class="group flex flex-col overflow-hidden rounded-lg border border-base-300 bg-base-100 transition-colors hover:border-primary"
>
	<a href={url} class="block aspect-video overflow-hidden border-b border-base-300 bg-base-200" aria-label={title}>
		{#if missing || !mounted}
			<div class="flex h-full items-center justify-center text-4xl font-semibold text-base-content-muted">
				{(folder ?? title).charAt(0)}
			</div>
		{:else}
			<img src={light} alt="" class="block h-full w-full object-cover object-top dark:hidden"
				loading="lazy" on:error={() => (missing = true)} />
			<img src={dark} alt="" class="hidden h-full w-full object-cover object-top dark:block"
				loading="lazy" on:error={() => (missing = true)} />
		{/if}
	</a>
	<div class="flex flex-1 flex-col gap-2 p-4">
		<a href={url} class="text-base font-semibold text-base-content no-underline group-hover:text-primary">
			{title}
		</a>
		{#if description}
			<p class="m-0 text-sm leading-snug text-base-content-muted">{description}</p>
		{/if}
		<div class="mt-auto flex flex-wrap items-center gap-2 pt-2 text-xs">
			{#if folder}
				<span class="rounded-full border border-base-300 px-2 py-0.5 font-mono text-base-content-muted">{folder}</span>
			{/if}
			{#if marimo}
				<a href={marimo} class="ml-auto text-primary no-underline hover:underline">marimo version →</a>
			{/if}
		</div>
	</div>
</div>
