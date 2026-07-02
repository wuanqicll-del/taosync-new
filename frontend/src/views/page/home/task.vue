<template>
	<div class="task">
		<div class="top-box">
			<el-button type="primary" size="small" @click="goback">返回</el-button>
			<div class="top-box-title">任务详情</div>
			<menuRefresh :autoRefresh="false" :needShow="1" @getData="getTaskList"></menuRefresh>
		</div>
		<taskCurrent @currentChange="currentChange" class="task-current" :style="`height: ${currentHeight}px;`"
			:jobId="params.id"></taskCurrent>
		<div class="task-card-list">
			<div v-for="(item, index) in taskData.dataList" :key="item.id" class="task-card glass-card" @click="detail(item.id)" style="cursor:pointer;">
				<div class="task-card-idx">{{(params.pageNum - 1) * params.pageSize + index + 1}}</div>
				<div class="task-card-body">
					<div class="task-card-row">
						<div :class="`bg-status bg-${item.status < 6 ? item.status : 7}`">
								<span v-if="item.status != 6">{{item.status | taskStatusFilter}}</span>
								<el-popover v-else placement="top-end" title="错误原因" width="200" trigger="hover" :content="item.errMsg">
									<span slot="reference">失败，<span style="color: #409eff;">原因</span></span>
								</el-popover>
						</div>
						<span class="task-card-time">始{{item.createTime | fmtTime}}　末{{item.finishTime | fmtTime}}</span>
					</div>
					<div class="task-card-progress">
							<span class="prgNum bg-8">{{item.allNum}}</span>
							<span class="prgNum bg-2">{{item.successNum}}</span>
							<span class="prgNum bg-7">{{item.failNum}}</span>
							<span class="prgNum bg-3">{{item.otherNum}}</span>
					</div>
				</div>
				<div class="task-card-actions" @click.stop>
					<el-button type="danger" @click="delTask(item.id)"
						:disabled="item.status == 1"
						size="mini">{{item.status == 1 ? '暂不能' : ''}}删除</el-button>
				</div>
			</div>
			<div v-if="!loading && taskData.dataList.length === 0" class="empty-state">暂无任务</div>
		</div>
		<div class="page">
			<div class="page-tip">
				<span class="prgNum bg-8">总数</span>
				<span class="prgNum bg-2">成功</span>
				<span class="prgNum bg-7">失败</span>
				<span class="prgNum bg-3">其他</span>
			</div>
			<el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
				:current-page="params.pageNum" :page-size="params.pageSize" :total="taskData.count"
				layout="total, sizes, prev, pager, next, jumper" :page-sizes="[10, 20, 50, 100]">
			</el-pagination>
		</div>
	</div>

<script>
	import {
		jobGetTask,
		jobDeleteTask
	} from "@/api/job";
	import menuRefresh from './components/menuRefresh';
	import taskCurrent from './components/taskCurrent';
	export default {
		name: 'Task',
		components: {
			menuRefresh,
			taskCurrent
		},
		data() {
			return {
				taskData: {
					dataList: []
				},
				params: {
					id: null,
					pageSize: 10,
					pageNum: 1
				},
				loading: false,
				btnLoading: false,
				currentHeight: 0
			};
		},
		created() {
			if (this.$route.query.hasOwnProperty('jobId')) {
				this.params.id = this.$route.query.jobId;
			}
		},
		beforeDestroy() {},
		methods: {
			getTaskList() {
				if (this.params.id != null) {
					this.loading = true;
					jobGetTask(this.params).then(res => {
						this.loading = false;
						this.taskData = res.data;
					}).catch(err => {
						this.loading = false;
					})
				}
			},
			delTask(taskId) {
				this.$confirm("操作不可逆，将永久删除该记录，确定吗？", '提示', {
					confirmButtonText: '确定',
					cancelButtonText: '取消',
					type: 'warning'
				}).then(() => {
					this.btnLoading = true;
					jobDeleteTask(taskId).then(res => {
						this.btnLoading = false;
						this.$message({
							message: res.msg,
							type: 'success'
						});
						this.getTaskList();
					}).catch(err => {
						this.btnLoading = false;
					})
				});
			},
			detail(taskId) {
				this.$router.push({
					path: '/home/task/detail',
					query: {
						taskId
					}
				})
			},
			goback() {
				this.$router.go(-1);
			},
			handleSizeChange(val) {
				this.params.pageSize = val;
				this.getTaskList();
			},
			handleCurrentChange(val) {
				this.params.pageNum = val;
				this.getTaskList();
			},
			currentChange(val) {
				this.currentHeight = val;
				this.getTaskList();
			}
		}
	}
</script>

<style lang="scss" scoped>
	.task {
		width: 100%;
		height: 100%;
		overflow-y: auto;
		padding: 16px;
		box-sizing: border-box;

		.top-box {
			display: flex;
			align-items: center;
			justify-content: space-between;
			margin-bottom: 16px;

			.top-box-title {
				font-weight: bold;
			}
		}

		.task-current {
			transition: height 0.5s ease;
		}
	}

	.task-card-list {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.task-card {
		padding: 14px 16px;
		border-radius: 22px;
		display: flex;
		align-items: flex-start;
		gap: 12px;
		background: var(--bg-secondary);
		border: 1px solid var(--border-light);
		box-shadow: var(--shadow-sm);
		transition: box-shadow 0.25s, transform 0.25s;
		&:hover {
			box-shadow: var(--shadow-md);
		}
	}

	.task-card-idx {
		flex-shrink: 0;
		width: 32px;
		height: 32px;
		border-radius: 50%;
		background: var(--color-primary);
		color: #fff;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 13px;
		font-weight: 700;
	}

	.task-card-body {
		flex: 1;
		min-width: 0;
	}

	.task-card-row {
		display: flex;
		align-items: center;
		gap: 10px;
		flex-wrap: wrap;
	}

	.task-card-time {
		font-size: 12px;
		color: var(--text-muted);
	}

	.task-card-progress {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 4px;
		margin-top: 6px;
		font-size: 13px;
		color: var(--text-muted);
	}

	.task-card-actions {
		flex-shrink: 0;
		display: flex;
		align-items: center;
	}

	.prgNum {
		font-size: 14px;
		padding: 1px 3px;
		text-align: center;
		font-weight: bold;
		margin: 1px 3px;
		min-width: 56px;
		border-radius: 22px;
	}

	.prgNum:last-child {
		margin-right: 0;
	}

	.empty-state {
		text-align: center;
		padding: 60px 0;
		color: var(--text-muted);
		font-size: 15px;
	}

	.page {
		margin-top: 16px;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	@media screen and (min-width: 769px) {
		.task-card {
			flex-direction: column;
			align-items: flex-start;
		}
	}

	@media screen and (max-width: 768px) {
		.task {
			padding: 6px;

			.top-box {
				flex-wrap: wrap;
				gap: 4px;
				margin-bottom: 4px;
			}

			.top-box-title {
				font-size: 13px;
			}
		}

		.task-card {
			flex-direction: column;
			align-items: flex-start;
			padding: 12px 14px;
		}

		.task-card-idx {
			width: 26px;
			height: 26px;
			font-size: 11px;
		}

		.task-card-actions {
			width: 100%;
			margin-top: 4px;
		}

		.prgNum {
			min-width: 36px;
			font-size: 11px;
			padding: 1px 2px;
			margin: 1px 2px;
		}

		.page {
			margin-top: 8px;
			flex-wrap: wrap;
			gap: 4px;
		}
	}
</style>