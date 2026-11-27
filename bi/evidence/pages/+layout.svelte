<script>
	// Evidence's default layout with the Data Lab wordmark instead of Evidence's.
	// One `logo` (not lightLogo/darkLogo): the mobile menu drawer only reads `logo` and would
	// otherwise fall back to the Evidence wordmark. Logo URLs are used as given, so they
	// include the basePath (evidence.config.yaml).
	import '@evidence-dev/tailwind/fonts.css';
	import '../app.css';
	import { EvidenceDefaultLayout } from '@evidence-dev/core-components';
	export let data;
</script>

<!-- builtWithEvidence={false}: no "Built with Evidence" link at the foot of the sidebar. -->
<EvidenceDefaultLayout {data} logo="/evidence/data-lab.svg" homePageName="Data Lab" builtWithEvidence={false}>
	<slot slot="content" />
</EvidenceDefaultLayout>
