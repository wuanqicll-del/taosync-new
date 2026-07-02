<template>
	<div class="login">
		<div class="login-card glass-card">
			<div class="login-title">TaoSync</div>
			<div class="login-subtitle">密码登录</div>
			<el-form :model="loginForm" :rules="rules" ref="loginForm" label-width="0">
				<el-form-item prop="userName">
					<el-input placeholder="请输入用户名" prefix-icon="el-icon-user" v-model="loginForm.userName"></el-input>
				</el-form-item>
				<el-form-item prop="passwd">
					<el-input placeholder="请输入密码" prefix-icon="el-icon-lock" v-model="loginForm.passwd" show-password
						@keyup.enter.native="login"></el-input>
				</el-form-item>
			</el-form>
			<div class="login-forget" @click="fogetPwd">忘记密码？</div>
			<el-button class="login-btn" type="primary" @click="login">登录</el-button>
			<div class="login-theme" @click="toggleTheme">
				<i :class="vuex_theme === 'dark' ? 'el-icon-sunrise' : 'el-icon-moon'"></i>
			</div>
		</div>

		<el-dialog :visible.sync="showPwd" :append-to-body="true" title="重置密码"
			width="480px" :before-close="closePwd">
			<el-form :model="pwdForm" :rules="pwdRules" ref="resetForm" label-width="80px">
				<el-form-item prop="userName" label="用户名">
					<el-input placeholder="请输入用户名" v-model="pwdForm.userName"></el-input>
				</el-form-item>
				<el-form-item prop="key" label="加密秘钥">
					<el-input placeholder="在 data/secret.key 文件中复制全部" v-model="pwdForm.key"></el-input>
				</el-form-item>
				<el-form-item prop="passwd" label="新密码">
					<el-input placeholder="请输入新密码" v-model="pwdForm.passwd" show-password></el-input>
				</el-form-item>
				<el-form-item prop="passwd2" label="确认密码">
					<el-input placeholder="请确认新密码" v-model="pwdForm.passwd2" show-password></el-input>
				</el-form-item>
			</el-form>
			<span slot="footer">
				<el-button @click="closePwd">取消</el-button>
				<el-button type="primary" @click="fogetSubmit">确定</el-button>
			</span>
		</el-dialog>
	</div>
</template>

<script>
	import Cookies from 'js-cookie';
	import { login, resetPwd } from "@/api/user";
	export default {
		name: 'Login',
		data() {
			var validatePass2 = (rule, value, callback) => {
				if (value == '' || value == null) {
					callback(new Error('请再次输入新密码'));
				} else if (value !== this.pwdForm.passwd) {
					callback(new Error('两次输入密码不一致!'));
				} else {
					callback();
				}
			};
			return {
				loginForm: { userName: null, passwd: null },
				loading: false,
				rules: {
					userName: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
					passwd: [{ required: true, message: '请输入密码', trigger: 'blur' }]
				},
				pwdRules: {
					userName: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
					key: [{ required: true, message: '请输入key', trigger: 'blur' }],
					passwd: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
					passwd2: [{ validator: validatePass2, trigger: 'blur' }]
				},
				showPwd: false,
				pwdForm: { userName: null, key: null, passwd: null, passwd2: null }
			};
		},
		computed: {
			vuex_theme() { return this.$store.state.vuex_theme; }
		},
		created() {
			document.body.className = this.vuex_theme;
		},
		methods: {
			login() {
				this.$refs.loginForm.validate((valid) => {
					if (valid) {
						Cookies.remove(this.vuex_cookieName);
						this.loading = true;
						login(this.loginForm).then(res => {
							this.$setVuex('vuex_userInfo', res.data);
							this.$router.replace('/home');
							this.loading = false;
						}).catch(() => { this.loading = false; })
					}
				});
			},
			toggleTheme() {
				const newTheme = this.vuex_theme === 'dark' ? 'light' : 'dark';
				this.$setVuex('vuex_theme', newTheme);
				document.body.className = newTheme;
			},
			fogetPwd() { this.showPwd = true; },
			closePwd() {
				this.showPwd = false;
				this.pwdForm = { userName: null, key: null, passwd: null, passwd2: null };
			},
			fogetSubmit() {
				this.$refs.resetForm.validate((valid) => {
					if (valid) {
						this.loading = true;
						resetPwd(this.pwdForm).then(() => {
							this.closePwd();
							this.$message({ message: '密码重置成功，请使用新密码登录', type: 'success' });
							this.loading = false;
						}).catch(() => { this.loading = false; })
					}
				});
			}
		}
	}
</script>
<style lang="scss" scoped>
	.login {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--bg-primary);
	}

	.login-card {
		width: 400px;
		padding: 40px 36px;
		border-radius: 22px;
		position: relative;

		.login-title {
			font-size: 28px;
			font-weight: 700;
			color: var(--color-primary);
			text-align: center;
			letter-spacing: 2px;
			margin-bottom: 4px;
		}

		.login-subtitle {
			text-align: center;
			color: var(--text-muted);
			font-size: 14px;
			margin-bottom: 32px;
		}

		.login-forget {
			text-align: right;
			font-size: 13px;
			color: var(--text-muted);
			cursor: pointer;
			margin-top: -8px;
			margin-bottom: 16px;
			&:hover { color: var(--color-primary); }
		}

		.login-btn {
			width: 100%;
			height: 42px;
			border-radius: 22px;
			font-size: 15px;
			font-weight: 600;
		}

		.login-theme {
			position: absolute;
			top: 16px;
			right: 16px;
			width: 36px;
			height: 36px;
			display: flex;
			align-items: center;
			justify-content: center;
			border-radius: 50%;
			cursor: pointer;
			color: var(--text-muted);
			font-size: 18px;
			transition: all 0.25s;
			&:hover { background: var(--bg-tertiary); color: var(--text-primary); }
		}
	}

	@media screen and (max-width: 768px) {
		.login-card {
			width: 90vw;
			padding: 28px 24px;

			.login-title { font-size: 24px; }
			.login-subtitle { margin-bottom: 24px; }
		}
	}
</style>
