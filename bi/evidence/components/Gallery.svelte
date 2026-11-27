<!--
	A responsive grid of GalleryCards: one column on phones, two on tablets, three on desktop.
	Used as a single line in markdown (<Gallery items={cards}/>), so no HTML block has to survive
	the markdown parser. `items` is a list of GalleryCard props.
-->
<script>
	import GalleryCard from './GalleryCard.svelte';

	/** @type {Array<{title: string, href: string, thumb: string, description?: string, folder?: string, marimo?: string}>} */
	export let items = [];
</script>

<div class="not-prose mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
	{#each items as item (item.href)}
		<GalleryCard {...item} />
	{/each}
</div>
