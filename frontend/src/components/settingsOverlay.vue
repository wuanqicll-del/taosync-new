<template>
	<transition name="fade">
		<div v-if="visible" class="settings-mask" @click.self="$emit('close')">
			<div class="settings-panel" @click.stop>
				<!-- 头部 -->
				<div class="sp-header">
					<span class="sp-title">设置</span>
				</div>
				<!-- 内容 -->
				<div class="sp-body">
					<!-- ===== 引擎管理 ===== -->
					<div class="sp-section">
						<div class="sp-section-title">引擎管理</div>
						<div class="sp-section-desc">管理 Alist 引擎连接</div>
						<div>
							<div class="sp-card" v-for="item in alistList" :key="item.id">
								<div class="sp-card-info">
									<div class="sp-card-name">{{item.userName}}</div>
									<div class="sp-card-sub" v-if="item.remark">[{{item.remark}}]</div>
									<div class="sp-card-url">{{item.url}}</div>
								</div>
								<div class="sp-card-btns">
									<el-button size="mini" type="primary" @click="engineEdit(item)">编辑</el-button>
									<el-button size="mini" type="danger" @click="engineDel(item.id)">删除</el-button>
								</div>
							</div>
							<div class="sp-card sp-add" @click="engineAdd">
								{{alistList.length === 0 ? '暂无引擎，请新增' : '+ 新增引擎'}}
							</div>
						</div>
					</div>

					<!-- ===== 通知配置 ===== -->
					<div class="sp-section">
						<div class="sp-section-title">通知配置</div>
						<div class="sp-section-desc">配置同步结果通知方式</div>
						<div>
							<div class="sp-card" v-for="item in notifyList" :key="item.id">
								<div class="sp-card-info">
									<div class="sp-card-name">{{item.method | notifyMethodFilter}}</div>
									<div :class="['sp-card-status', item.enable == 1 ? 'on' : 'off']">
										{{item.enable == 1 ? '已启用' : '已禁用'}}
									</div>
								</div>
								<div class="sp-card-btns">
									<el-button size="mini" type="primary" @click="notifyEdit(item)">编辑</el-button>
									<el-button size="mini" :type="item.enable == 0 ? 'success' : 'warning'"
										@click="notifyToggle(item)">{{item.enable == 0 ? '启用' : '禁用'}}</el-button>
									<el-button size="mini" type="primary" @click="notifyTest(item)">测试</el-button>
									<el-button size="mini" type="danger" @click="notifyDel(item.id)">删除</el-button>
								</div>
							</div>
							<div class="sp-card sp-add" @click="notifyAdd">
								{{notifyList.length === 0 ? '暂无通知配置，请新增' : '+ 新增通知'}}
							</div>
						</div>
					</div>

					<!-- ===== 修改密码 ===== -->
					<div class="sp-section">
						<div class="sp-section-title">修改密码</div>
						<div class="sp-section-desc">修改登录密码</div>
						<div class="sp-pwd-form">
							<el-form :model="pwdForm" :rules="pwdRules" ref="pwdRef" label-width="0">
								<el-form-item prop="oldPasswd">
									<el-input placeholder="旧密码" show-password v-model="pwdForm.oldPasswd"></el-input>
								</el-form-item>
								<el-form-item prop="passwd">
									<el-input placeholder="新密码" show-password v-model="pwdForm.passwd"></el-input>
								</el-form-item>
								<el-form-item prop="passwd2">
									<el-input placeholder="确认新密码" show-password v-model="pwdForm.passwd2"
										@keyup.enter.native="pwdSubmit"></el-input>
								</el-form-item>
							</el-form>
							<el-button type="primary" class="sp-full-btn" @click="pwdSubmit">修改密码</el-button>
						</div>
					</div>
				</div>
			</div>
			<!-- 引擎编辑弹窗 -->
			<el-dialog :visible.sync="engineShow" :title="engineEditFlag ? '编辑引擎' : '新增引擎'" width="600px" append-to-body>
				<div class="elform-box">
					<el-form :model="engineEditData" :rules="engineEditFlag ? engineRules : engineAddRules" ref="engineRef" v-if="engineShow" label-width="66px">
						<el-form-item prop="url" label="地址">
							<el-input v-model="engineEditData.url" placeholder="请输入地址，如http://127.0.0.1:5244"></el-input>
						</el-form-item>
						<el-form-item prop="remark" label="备注">
							<el-input v-model="engineEditData.remark" placeholder="备注方便你标识引擎，非必填"></el-input>
						</el-form-item>
						<el-form-item prop="token" label="令牌">
							<el-input v-model="engineEditData.token" show-password
								:placeholder="`请输入令牌，${engineEditFlag ? '留空表示不修改' : '请到AList管理-设置-其他中复制，保存后不要重置令牌'}`"
								@keyup.enter.native="engineSubmit"></el-input>
						</el-form-item>
					</el-form>
				</div>
				<span slot="footer" class="dialog-footer">
					<el-button @click="engineShow = false">取 消</el-button>
					<el-button type="primary" @click="engineSubmit">确 定</el-button>
				</span>
			</el-dialog>
			<!-- 通知编辑弹窗 -->
			<el-dialog top="6vh" :visible.sync="notifyShow" :title="notifyEditFlag ? '编辑通知' : '新增通知'" width="680px" append-to-body>
				<div class="elform-box">
					<el-form :model="notifyEditData" :rules="notifyEditRule[notifyEditData.method]" ref="notifyRef" v-if="notifyShow" label-width="100px">
						<el-form-item prop="enable" label="是否启用">
							<el-switch v-model="notifyEditData.enable" :active-value="1" :inactive-value="0"></el-switch>
						</el-form-item>
						<el-form-item prop="method" label="方式">
							<el-select v-model="notifyEditData.method" @change="notifyMethodChange" style="width: 100%;">
								<el-option :key="meItem - 1" :value="meItem - 1" :label="meItem - 1 | notifyMethodFilter"
									v-for="meItem in notifyMethodLength"></el-option>
							</el-select>
						</el-form-item>
						<template v-if="notifyEditData.method == 0">
							<el-form-item prop="params.url" label="请求地址">
								<el-input v-model="notifyEditData.params.url" placeholder="请输入请求地址"></el-input>
							</el-form-item>
							<el-form-item prop="params.method" label="请求方法">
								<el-select v-model="notifyEditData.params.method" style="width: 100%;">
									<el-option key="POST" value="POST" label="POST"></el-option>
									<el-option key="PUT" value="PUT" label="PUT"></el-option>
									<el-option key="GET" value="GET" label="GET"></el-option>
								</el-select>
							</el-form-item>
							<el-form-item v-if="notifyEditData.params.method != 'GET'" prop="params.contentType" label="请求体类型">
								<el-select v-model="notifyEditData.params.contentType" style="width: 100%;">
									<el-option key="application/json" value="application/json" label="application/json"></el-option>
									<el-option key="application/x-www-form-urlencoded" value="application/x-www-form-urlencoded" label="application/x-www-form-urlencoded"></el-option>
								</el-select>
							</el-form-item>
							<el-form-item prop="params.titleName" label="标题参数名">
								<el-input v-model="notifyEditData.params.titleName" placeholder="请输入标题参数名"></el-input>
							</el-form-item>
							<el-form-item prop="params.needContent" label="是否需要内容">
								<el-select v-model="notifyEditData.params.needContent" style="width: 100%;">
									<el-option :key="true" :value="true" label="需要"></el-option>
									<el-option :key="false" :value="false" label="不需要"></el-option>
								</el-select>
							</el-form-item>
							<el-form-item prop="params.contentName" v-if="notifyEditData.params.needContent" label="内容参数名">
								<el-input v-model="notifyEditData.params.contentName" placeholder="请输入内容参数名"></el-input>
							</el-form-item>
						</template>
						<template v-else-if="notifyEditData.method == 1">
							<el-form-item prop="params.sendKey" label="SendKey">
								<el-input v-model="notifyEditData.params.sendKey" placeholder="请输入SendKey"></el-input>
							</el-form-item>
						</template>
						<template v-else-if="notifyEditData.method == 2">
							<el-form-item prop="params.url" label="WebHook">
								<el-input v-model="notifyEditData.params.url" placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxxx"></el-input>
							</el-form-item>
						</template>
						<template v-else-if="notifyEditData.method == 3">
							<el-form-item prop="params.corpid" label="企业ID">
								<el-input v-model="notifyEditData.params.corpid" placeholder="请输入企业ID"></el-input>
							</el-form-item>
							<el-form-item prop="params.agentid" label="应用ID">
								<el-input v-model="notifyEditData.params.agentid" placeholder="请输入应用ID/AgentId"></el-input>
							</el-form-item>
							<el-form-item prop="params.corpsecret" label="应用Secret">
								<el-input v-model="notifyEditData.params.corpsecret" placeholder="请输入应用Secret" type="password"></el-input>
							</el-form-item>
							<el-form-item prop="params.touser" label="接收用户">
								<el-input v-model="notifyEditData.params.touser" placeholder="请输入接收用户ID，多个用|分隔，@all表示全部"></el-input>
							</el-form-item>
						</template>
						<template v-else-if="notifyEditData.method == 4">
							<el-form-item prop="params.url" label="WebHook">
								<el-input v-model="notifyEditData.params.url" placeholder="https://open.larksuite.com/open-apis/bot/v2/hook/xxxxxxxxxx"></el-input>
							</el-form-item>
						</template>
						<template v-else-if="notifyEditData.method == 5">
							<el-form-item prop="params.url" label="地址">
								<el-input v-model="notifyEditData.params.url" placeholder="http://你的ntfy地址:端口/你的topic"></el-input>
							</el-form-item>
						</template>
						<el-form-item prop="params.notSendNull" label="忽略无同步">
							<el-switch v-model="notifyEditData.params.notSendNull" :active-value="1" :inactive-value="0"></el-switch>
						</el-form-item>
					</el-form>
				</div>
				<span slot="footer" class="dialog-footer">
					<el-button @click="notifyShow = false">取 消</el-button>
					<el-button type="primary" @click="notifySubmit">确 定</el-button>
				</span>
			</el-dialog>
		</div>
	</transition>
</template>

<script>
import { alistGet, alistPost, alistPut, alistDelete } from "@/api/job";
import { getNotifyList, putEditNotify, postAddNotify, putEnableNotify, delNotify } from "@/api/notify";
import { editPwd } from "@/api/user";
import notifyMethod from '@/utils/notifyMethod';

export default {
	props: { visible: Boolean },
	data() {
		var validatePass2 = (rule, value, callback) => {
			if (!value) callback(new Error('请再次输入新密码'));
			else if (value !== this.pwdForm.passwd) callback(new Error('两次输入密码不一致!'));
			else callback();
		};
		return {
			alistList: [],
			engineLoading: false,
			engineShow: false,
			engineEditFlag: false,
			engineEditData: {},
			engineRules: { url: [{ required: true, message: '请输入地址', trigger: 'blur' }] },
			engineAddRules: { url: [{ required: true, message: '请输入地址', trigger: 'blur' }], token: [{ required: true, message: '请输入令牌', trigger: 'blur' }] },
			notifyList: [],
			notifyLoading: false,
			notifyShow: false,
			notifyEditFlag: false,
			notifyEditData: { method: 0, enable: 1, params: {} },
			notifyMethodLength: notifyMethod.length,
			notifyEditRule: [{
				params: { url: [{ type: 'string', required: true, message: '请输入地址' }], titleName: [{ type: 'string', required: true, message: '请输入标题名' }], contentName: [{ type: 'string', required: true, message: '请输入内容名' }] }
			}, {
				params: { sendKey: [{ type: 'string', required: true, message: '请输入sendKey' }] }
			}, {
				params: { url: [{ type: 'string', required: true, message: '请输入WebHook地址' }] }
			}, {
				params: { corpid: [{ type: 'string', required: true, message: '请输入企业ID' }], agentid: [{ type: 'string', required: true, message: '请输入应用ID/AgentId' }], corpsecret: [{ type: 'string', required: true, message: '请输入应用Secret' }], touser: [{ type: 'string', required: false }] }
			}, {
				params: { url: [{ type: 'string', required: true, message: '请输入WebHook地址' }] }
			}, {
				params: { url: [{ type: 'string', required: true, message: '请输入地址' }] }
			}],
			tstLoading: false,
			pwdForm: { oldPasswd: null, passwd: null, passwd2: null },
			pwdLoading: false,
			pwdRules: {
				oldPasswd: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
				passwd: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
				passwd2: [{ validator: validatePass2, trigger: 'blur' }]
			}
		};
	},
	watch: {
		visible(val) {
			if (val) { this.loadEngine(); this.loadNotify(); }
		}
	},
	methods: {
		// ========== 引擎 ==========
		loadEngine() {
			this.engineLoading = true;
			alistGet().then(res => { this.alistList = res.data || []; this.engineLoading = false; }).catch(() => { this.engineLoading = false; });
		},
		engineAdd() {
			this.engineEditFlag = false;
			this.engineEditData = { url: '', token: '', remark: '' };
			this.engineShow = true;
		},
		engineEdit(item) {
			this.engineEditFlag = true;
			this.engineEditData = { ...item, token: '' };
			this.engineShow = true;
		},
		engineSubmit() {
			this.$refs.engineRef.validate(valid => {
				if (!valid) return;
				(this.engineEditFlag ? alistPut : alistPost)(this.engineEditData).then(res => {
					this.$message({ message: res.msg, type: 'success' });
					this.engineShow = false;
					this.loadEngine();
				});
			});
		},
		engineDel(id) {
			this.$confirm('确认删除该引擎？', '提示', { type: 'warning' }).then(() => {
				alistDelete(id).then(res => { this.$message({ message: res.msg, type: 'success' }); this.loadEngine(); });
			}).catch(() => {});
		},
		// ========== 通知 ==========
		loadNotify() {
			this.notifyLoading = true;
			getNotifyList().then(res => { this.notifyList = res.data || []; this.notifyLoading = false; }).catch(() => { this.notifyLoading = false; });
		},
		notifyAdd() {
			this.notifyEditFlag = false;
			this.notifyEditData = { method: 0, enable: 1, params: { url: '' } };
			this.notifyShow = true;
		},
		notifyEdit(item) {
			this.notifyEditFlag = true;
			this.notifyEditData = JSON.parse(JSON.stringify(item));
			this.notifyEditData.params = JSON.parse(this.notifyEditData.params);
			if (!this.notifyEditData.params.hasOwnProperty('notSendNull')) {
				this.notifyEditData.params.notSendNull = false;
			}
			this.notifyShow = true;
		},
		notifyMethodChange(val) {
			if (val === 0) this.notifyEditData.params = { url: '', method: 'POST', contentType: 'application/json', needContent: true, titleName: 'title', contentName: 'content', notSendNull: false };
			else if (val === 1) this.notifyEditData.params = { sendKey: '', notSendNull: false };
			else if (val === 2) this.notifyEditData.params = { url: '', notSendNull: false };
			else if (val === 3) this.notifyEditData.params = { corpid: '', agentid: '', corpsecret: '', touser: '@all', notSendNull: false };
			else if (val === 4) this.notifyEditData.params = { url: '', notSendNull: false };
			else if (val === 5) this.notifyEditData.params = { url: '', notSendNull: false };
			this.$nextTick(() => { this.$refs.notifyRef.clearValidate(); });
		},
		notifySubmit() {
			this.$refs.notifyRef.validate(valid => {
				if (!valid) return;
				let dt = JSON.parse(JSON.stringify(this.notifyEditData));
				dt.params = JSON.stringify(dt.params);
				(this.notifyEditFlag ? putEditNotify : postAddNotify)(dt).then(res => {
					this.$message({ message: res.msg, type: 'success' });
					this.notifyShow = false;
					this.loadNotify();
				});
			});
		},
		notifyToggle(item) {
			putEnableNotify(item.id, item.enable == 1 ? 0 : 1).then(res => {
				this.$message({ message: res.msg, type: 'success' });
				this.loadNotify();
			});
		},
		notifyTest(item) {
			this.tstLoading = true;
			let it = JSON.parse(JSON.stringify(item));
			if (typeof it.params === 'object') it.params = JSON.stringify(it.params);
			delete it.enable;
			postAddNotify(it).then(() => {
				this.tstLoading = false;
				this.$message({ message: '测试消息已发送', type: 'success' });
			}).catch(() => { this.tstLoading = false; });
		},
		notifyDel(id) {
			this.$confirm('确认删除该通知配置？', '提示', { type: 'warning' }).then(() => {
				delNotify(id).then(res => { this.$message({ message: res.msg, type: 'success' }); this.loadNotify(); });
			}).catch(() => {});
		},
		// ========== 密码 ==========
		pwdSubmit() {
			this.$refs.pwdRef.validate(valid => {
				if (!valid) return;
				this.pwdLoading = true;
				editPwd(this.pwdForm).then(res => {
					this.$message({ message: res.msg, type: 'success' });
					this.$refs.pwdRef.resetFields();
					this.pwdLoading = false;
				}).catch(() => { this.pwdLoading = false; });
			});
		}
	}
}
</script>

<style lang="scss" scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter, .fade-leave-to { opacity: 0; }

.settings-mask {
	position: fixed; top: 0; left: 0; right: 0; bottom: 0;
	background: rgba(0,0,0,0.45); z-index: 3000;
	display: flex; align-items: center; justify-content: center; padding: 12px;
}

.settings-panel {
	width: 520px; max-width: 100%; height: 70vh; max-height: 70vh;
	background: var(--bg-secondary); border-radius: 22px;
	box-shadow: var(--shadow-lg);
	display: flex; flex-direction: column; overflow: hidden;
}

.sp-header {
	display: flex; align-items: center; justify-content: center;
	padding: 18px 20px 0;
}
.sp-title { font-size: 18px; font-weight: 700; color: var(--text-primary); }

.sp-body {
	flex: 1; overflow-y: auto; padding: 16px 20px 24px;
}

.sp-section {
	margin-bottom: 28px;
	&:last-child { margin-bottom: 0; }
}
.sp-section-title {
	font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 2px;
}
.sp-section-desc {
	font-size: 12px; color: var(--text-muted); margin-bottom: 12px;
}

.sp-card {
	padding: 12px 14px; border-radius: 22px;
	background: var(--bg-tertiary); border: 1px solid var(--border-light);
	transition: border-color 0.2s; margin-bottom: 8px;
	&:last-child { margin-bottom: 0; }
	&:hover { border-color: var(--color-primary); }
}
.sp-add {
	text-align: center; color: var(--text-muted); cursor: pointer;
	border: 2px dashed var(--border-color); background: transparent;
	font-size: 13px; padding: 14px;
	&:hover { color: var(--color-primary); border-color: var(--color-primary); }
}

.sp-card-info {
	display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.sp-card-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.sp-card-sub { font-size: 12px; color: var(--color-primary); }
.sp-card-url { font-size: 11px; color: var(--text-muted); width: 100%; word-break: break-all; }
.sp-card-status { font-size: 11px; font-weight: 600; }
.sp-card-status.on { color: var(--color-success); }
.sp-card-status.off { color: var(--color-danger); }

.sp-card-btns {
	display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
}

.sp-pwd-form { max-width: 360px; }

.sp-full-btn {
	width: 100%; border-radius: 22px; height: 40px; font-weight: 600;
}

@media screen and (max-width: 768px) {
	.settings-panel { height: 70vh; max-height: 70vh; border-radius: 22px; }
	.sp-body { padding: 12px 16px 16px; }
}
</style>
