<script>
	// Evidence's default layout with the Data Lab wordmark instead of Evidence's.
	// Logo URLs are used as given, so they include the basePath (evidence.config.yaml).
	import '@evidence-dev/tailwind/fonts.css';
	import '../app.css';
	import { EvidenceDefaultLayout } from '@evidence-dev/core-components';
	export let data;
</script>

<EvidenceDefaultLayout
	{data}
	lightLogo="/evidence/data-lab-light.svg"
	darkLogo="/evidence/data-lab-dark.svg"
	homePageName="Data Lab"
>
	<slot slot="content" />
</EvidenceDefaultLayout>
