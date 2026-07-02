<template>
	<div id="app" class="app-all-main">
		<div>
			<router-view />
		</div>
	</div>
</template>
<script>
	export default {
		name: "App",
		watch: {
			$route(to, from) {
				this.$setVuex('vuex_letfIndex', to.meta ? (to.meta.letfIndex || null) : null);
			}
		}
	};
</script>
<style lang="scss">
	@import '@/assets/style/style.scss';
</style>
