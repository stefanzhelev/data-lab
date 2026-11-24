<script lang="ts">
	import { resolve } from '$app/paths';
	import * as Card from '#lib/components/ui/card/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import { demos } from '#lib/manifest.js';
</script>

<svelte:head>
	<title>Data Lab · Stefan Zhelev</title>
	<meta
		name="description"
		content="Small, end-to-end data projects: pipelines, models and live dashboards."
	/>
</svelte:head>

<section class="mb-8 max-w-2xl">
	<h1 class="text-3xl font-semibold tracking-tight">Data Lab</h1>
	<p class="mt-2 text-muted-foreground">
		Small, end-to-end data projects: ingestion, modelling, testing and a live dashboard you can
		explore in the browser. Every demo's code, data and pipeline are public.
	</p>
</section>

<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
	{#each demos as demo (demo.slug)}
		<Card.Root>
			<Card.Header>
				<Card.Title>{demo.title}</Card.Title>
				<Card.Description>{demo.description}</Card.Description>
			</Card.Header>
			<Card.Content class="flex flex-wrap gap-1.5">
				{#each demo.skills as skill (skill)}
					<Badge variant="secondary">{skill}</Badge>
				{/each}
			</Card.Content>
			<Card.Footer class="flex flex-wrap gap-3 text-sm">
				{#each demo.pages as page (page.slug)}
					<!-- Full page load: the marimo runtime boots once per document. -->
					<a
						data-sveltekit-reload
						class="font-medium underline underline-offset-4"
						href={resolve('/[demo]/[page]', { demo: demo.slug, page: page.slug })}
					>
						Open {page.slug} →
					</a>
				{/each}
			</Card.Footer>
		</Card.Root>
	{/each}
</div>
