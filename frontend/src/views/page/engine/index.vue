<template>
	<div class="engine">
		<div class="loading-box content-none-data" v-if="getLoading">加载中</div>
		<div v-else class="card-box">
			<div class="card-item glass-card" v-for="item in alistList">
				<div class="card-item-top">
					<div class="card-item-user">{{item.userName}}
						<div class="card-item-remark" v-if="item.remark != null">[{{item.remark}}]</div>
					</div>
					<div class="card-item-url">{{item.url}}</div>
				</div>
				<div class="card-item-bottom">
					<el-button size="small" type="primary" @click="editShowDialog(item)">编辑</el-button>
					<el-button size="small" type="danger" @click="delAlist(item.id)">删除</el-button>
				</div>
			</div>
			<div class="card-item card-add glass-card" @click="addShow" v-if="!getLoading">
				<template v-if="alistList.length == 0">
					暂无引擎，请新增
				</template>
				<span v-else>新增</span>
			</div>
			<el-dialog :visible.sync="editShow" :title="editFlag ? '编辑' : '新增'" width="600px"
				:before-close="closeShow" :append-to-body="true">
				<div class="elform-box">
					<el-form :model="editData" :rules="editFlag ? editRule : addRule" ref="addRule" v-if="editShow"
						label-width="66px">
						<el-form-item prop="url" label="地址">
							<el-input v-model="editData.url" placeholder="请输入地址，如http://127.0.0.1:5244"></el-input>
						</el-form-item>
						<el-form-item prop="remark" label="备注">
							<el-input v-model="editData.remark" placeholder="备注方便你标识引擎，非必填"></el-input>
						</el-form-item>
						<el-form-item prop="token" label="令牌">
							<el-input v-model="editData.token" show-password
								:placeholder="`请输入令牌，${editFlag ? '留空表示不修改' : '请到AList管理-设置-其他中复制，保存后不要重置令牌'}`"
								@keyup.enter.native="submit"></el-input>
						</el-form-item>
					</el-form>
				</div>
				<span slot="footer" class="dialog-footer">
					<el-button @click="closeShow">取 消</el-button>
					<el-button type="primary" @click="submit">确 定</el-button>
				</span>
			</el-dialog>
		</div>
	</div>
</template>

<script>
	import {
		alistGet,
		alistPost,
		alistPut,
		alistDelete
	} from "@/api/job";
	export default {
		name: 'Engine',
		components: {},
		data() {
			return {
				alistList: [],
				getLoading: false,
				deleteLoading: false,
				editLoading: false,
				editData: null,
				editFlag: false,
				editShow: false,
				editRule: {
					url: [{
						required: true,
						message: '请输入地址',
						trgger: 'blur'
					}]
				},
				addRule: {
					url: [{
						required: true,
						message: '请输入地址',
						trgger: 'blur'
					}],
					token: [{
						required: true,
						message: '请输入令牌，请到AList管理-设置-其他中复制，保存后不要重置令牌否则令牌失效',
						trgger: 'blur'
					}]
				}
			};
		},
		created() {
			this.getAlistList();
		},
		beforeDestroy() {},
		methods: {
			getAlistList() {
				this.getLoading = true;
				alistGet().then(res => {
					this.getLoading = false;
					this.alistList = res.data;
				}).catch(err => {
					this.getLoading = false;
				})
			},
			addShow() {
				this.editFlag = false;
				this.editData = {
					remark: '',
					url: '',
					token: ''
				}
				this.editShow = true;
			},
			editShowDialog(row) {
				this.editData = {
					...row,
					token: ''
				};
				this.editFlag = true;
				this.editShow = true;
			},
			closeShow() {
				this.editShow = false;
			},
			submit() {
				this.$refs.addRule.validate((valid) => {
					if (valid) {
						this.editData.url = this.ensureHttpPrefix(this.editData.url);
						this.editLoading = true;
						if (this.editFlag) {
							alistPut(this.editData).then(res => {
								this.editLoading = false;
								this.$message({
									message: res.msg,
									type: 'success'
								});
								this.closeShow();
								this.getAlistList();
							}).catch(err => {
								this.editLoading = false;
							})
						} else {
							alistPost(this.editData).then(res => {
								this.editLoading = false;
								this.$message({
									message: res.msg,
									type: 'success'
								});
								this.closeShow();
								this.getAlistList();
							}).catch(err => {
								this.editLoading = false;
							})
						}
					}
				})
			},
			delAlist(alistId) {
				this.$confirm("操作不可逆，将永久删除该引擎，请确认没有任务使用该引擎，否则会导致错误，仍要删除吗？", '提示', {
					confirmButtonText: '确定',
					cancelButtonText: '取消',
					type: 'warning'
				}).then(() => {
					this.deleteLoading = true;
					alistDelete(alistId).then(res => {
						this.deleteLoading = false;
						this.$message({
							message: res.msg,
							type: 'success'
						});
						this.getAlistList();
					}).catch(err => {
						this.deleteLoading = false;
					})
				});
			},
			ensureHttpPrefix(url) {
				if (!/^https?:\/\//i.test(url)) {
					if (url.startsWith('//')) {
						return 'http:' + url;
					}
					return 'http://' + url;
				}
				return url;
			}
		}
	}
</script>

<style lang="scss">
	.engine {
		box-sizing: border-box;
		width: 100%;

		.loading-box {
			padding: 60px 0;
			text-align: center;
			color: var(--text-muted);
		}

		.card-box {
			display: grid;
			grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
			gap: 12px;
		}

		.card-item {
			padding: 16px;
			border-radius: 22px;
			background: var(--bg-secondary);
			border: 1px solid var(--border-light);
			box-shadow: var(--shadow-sm);
			transition: box-shadow 0.25s, border-color 0.25s;

			&:hover {
				box-shadow: var(--shadow-md);
				border-color: var(--color-primary);
			}
		}

		.card-item-top {
			margin-bottom: 12px;

			.card-item-user {
				font-size: 15px;
				font-weight: 600;
				color: var(--text-primary);
				display: flex;
				align-items: center;
				gap: 4px;
			}

			.card-item-remark {
				font-size: 13px;
				color: var(--color-primary);
				font-weight: 500;
			}

			.card-item-url {
				margin-top: 6px;
				font-size: 12px;
				color: var(--text-muted);
				word-break: break-all;
			}
		}

		.card-item-bottom {
			display: flex;
			flex-wrap: wrap;
			gap: 6px;
		}

		.card-add {
			display: flex;
			align-items: center;
			justify-content: center;
			cursor: pointer;
			font-size: 15px;
			color: var(--text-muted);
			min-height: 100px;
			border: 2px dashed var(--border-color);
			border-radius: 22px;
			transition: all 0.25s;

			&:hover {
				font-size: 18px;
				color: var(--color-primary);
				border-color: var(--color-primary);
				font-weight: bold;
			}
		}
	}

	@media screen and (max-width: 768px) {
		.engine .card-box {
			grid-template-columns: 1fr;
		}
	}
</style>
</style>
