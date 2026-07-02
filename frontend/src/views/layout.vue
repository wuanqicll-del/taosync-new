<template>
	<div class="layout">
		<div class="lay-topbar">
			<div class="topbar-left">
				<div class="topbar-logo" @click="showSettings = true">TaoSync</div>
			</div>
			<div class="topbar-right">
				<div class="topbar-icon" @click="toggleTheme">
					<i :class="vuex_theme === 'dark' ? 'el-icon-sunrise' : 'el-icon-moon'"></i>
				</div>
				<div class="topbar-icon" @click="logout()">
					<i class="el-icon-switch-button"></i>
				</div>
			</div>
		</div>
		<div class="lay-content">
			<router-view />
		</div>
		<settingsOverlay :visible="showSettings" @close="showSettings = false" />
	</div>
</template>
<script>
import { logout } from "@/api/user";
import settingsOverlay from "@/components/settingsOverlay.vue";
export default {
	components: { settingsOverlay },
	data() {
		return { showSettings: false };
	},
	methods: {
		logout() {
			logout().then(() => {
				this.$router.push('/login');
				this.$setVuex('vuex_userInfo', null);
			});
		},
		toggleTheme() {
			const newTheme = this.vuex_theme === 'dark' ? 'light' : 'dark';
			this.$setVuex('vuex_theme', newTheme);
			document.body.className = newTheme;
		}
	}
}
</script>
<style lang="scss" scoped>
	.layout {
		position: fixed;
		top: 0; bottom: 0; left: 0; right: 0;
		display: flex;
		flex-direction: column;
		background: var(--bg-primary);
	}
	.lay-topbar {
		height: 52px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 16px;
		border-bottom: 1px solid var(--border-light);
		background: var(--bg-secondary);
		flex-shrink: 0;
	}
	.topbar-left { display: flex; align-items: center; }
	.topbar-logo {
		font-size: 18px;
		font-weight: 700;
		color: var(--color-primary);
		letter-spacing: 1px;
		cursor: pointer;
		transition: opacity 0.2s;
		&:hover { opacity: 0.8; }
	}
	.topbar-right {
		display: flex;
		align-items: center;
		gap: 4px;
	}
	.topbar-icon {
		width: 36px; height: 36px;
		display: flex; align-items: center; justify-content: center;
		border-radius: 22px; cursor: pointer;
		font-size: 18px; color: var(--text-muted);
		transition: all 0.2s;
		&:hover { background: var(--bg-tertiary); color: var(--text-primary); }
	}
	.lay-content {
		flex: 1;
		overflow-y: auto;
		padding: 16px;
	}
	@media screen and (max-width: 768px) {
		.lay-content { padding: 12px; }
	}
</style>
