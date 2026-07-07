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
				<div class="topbar-icon github-icon" @click="openGitHub">
					<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
						<path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
					</svg>
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
		},
		openGitHub() {
			window.open('https://github.com/wuanqicll-del/taosync-new', '_blank');
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
	.github-icon {
		svg {
			width: 18px;
			height: 18px;
		}
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
