---
title: Data Lab · Evidence
---

<script>
	import Gallery from '$lib/Gallery.svelte';

	const LAB = 'https://lab.stefanzhelev.com/notebooks';
	// One card per page; `thumb` is the screenshot name written by thumbnails.py.
	const cards = [
		{
			title: 'Customer orders',
			href: '/practice/customer-orders',
			thumb: 'practice-customer-orders',
			folder: 'Practice',
			description: 'Cleaning, quarantining and reconciling a deliberately messy orders feed.',
			marimo: `${LAB}/practice/customer-orders/`
		},
		{
			title: 'Electricity transition',
			href: '/energy/energy',
			thumb: 'energy-energy',
			folder: 'Energy',
			description: 'Who is moving off fossil electricity? OWID energy data in six charts.',
			marimo: `${LAB}/energy/energy/`
		},
		{
			title: 'Example',
			href: '/example',
			thumb: 'example',
			description: 'Sliders that re-run a query in your browser.',
			marimo: `${LAB}/example/`
		}
	];
</script>

The [marimo gallery](https://lab.stefanzhelev.com/) rebuilt in [Evidence](https://github.com/evidence-dev/evidence):
the same files from `data/input/` and the same SQL, so each dashboard can be compared with its
marimo version.

<Gallery items={cards}/>
