<template>
	<div class="setting-page">
		<div v-if="vuex_userInfo" class="setting-card glass-card">
			<div class="card-header">
				<div class="card-title">个人信息</div>
				<div class="card-meta">创建时间：{{vuex_userInfo.createTime | timeStampFilter}}</div>
			</div>
			<div class="card-body">
				<div class="info-row">
					<span class="info-label">用户名</span>
					<span class="info-value">{{vuex_userInfo.userName}}</span>
				</div>
				<div class="divider"></div>
				<div class="card-title" style="margin-top: 16px; margin-bottom: 12px;">修改密码</div>
				<el-form :model="resetForm" :rules="rules" ref="resetForm" label-width="0">
					<el-form-item prop="oldPasswd">
						<el-input placeholder="请输入旧密码" show-password v-model="resetForm.oldPasswd"></el-input>
					</el-form-item>
					<el-form-item prop="passwd">
						<el-input placeholder="请输入新密码" show-password v-model="resetForm.passwd"></el-input>
					</el-form-item>
					<el-form-item prop="passwd2">
						<el-input placeholder="确认新密码" show-password v-model="resetForm.passwd2"
							@keyup.enter.native="resetPasswd"></el-input>
					</el-form-item>
				</el-form>
				<el-button type="primary" class="full-btn" @click="resetPasswd">修改密码</el-button>
			</div>
		</div>
		<div class="setting-footer">TaoSync</div>
	</div>
</template>

<script>
	import { editPwd } from "@/api/user";
	export default {
		name: 'User',
		data() {
			var validatePass2 = (rule, value, callback) => {
				if (value == '' || value == null) {
					callback(new Error('请再次输入新密码'));
				} else if (value !== this.resetForm.passwd) {
					callback(new Error('两次输入密码不一致!'));
				} else {
					callback();
				}
			};
			return {
				resetForm: { oldPasswd: null, passwd: null, passwd2: null },
				loading: false,
				rules: {
					oldPasswd: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
					passwd: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
					passwd2: [{ validator: validatePass2, trigger: 'blur' }]
				}
			};
		},
		methods: {
			resetPasswd() {
				this.$refs.resetForm.validate((valid) => {
					if (valid) {
						this.loading = true;
						editPwd(this.resetForm).then(res => {
							this.$message({ message: res.msg, type: 'success' });
							this.$refs.resetForm.resetFields();
							this.loading = false;
						}).catch(() => { this.loading = false; })
					}
				});
			}
		}
	}
</script>

<style lang="scss" scoped>
	.setting-page {
		max-width: 480px;
		margin: 0 auto;
		padding: 16px;
	}

	.setting-card {
		border-radius: 22px;
		overflow: hidden;
	}

	.card-header {
		padding: 20px 20px 0;

		.card-title {
			font-size: 17px;
			font-weight: 600;
			color: var(--text-primary);
		}
		.card-meta {
			font-size: 12px;
			color: var(--text-muted);
			margin-top: 4px;
		}
	}

	.card-body {
		padding: 16px 20px 20px;
	}

	.info-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 8px 0;

		.info-label {
			font-size: 14px;
			color: var(--text-muted);
		}
		.info-value {
			font-size: 14px;
			color: var(--text-primary);
			font-weight: 500;
		}
	}

	.divider {
		height: 1px;
		background: var(--border-light);
		margin: 8px 0;
	}

	.full-btn {
		width: 100%;
		border-radius: 22px;
		height: 40px;
		font-size: 14px;
		font-weight: 600;
	}

	.setting-footer {
		text-align: center;
		padding: 24px;
		font-size: 13px;
		color: var(--text-muted);
		letter-spacing: 1px;
	}

	@media screen and (max-width: 768px) {
		.setting-page {
			padding: 12px;
			max-width: 100%;
		}
	}
</style>
