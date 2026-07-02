<template>
	<transition name="fade">
		<div v-if="visible" class="overlay-mask" @click.self="$emit('close')">
			<div class="overlay-panel" @click.stop>
				<div class="overlay-header">
					<span class="overlay-title">任务执行记录</span>
				</div>
				<div class="overlay-body">
					<div class="task-card-list">
						<div v-for="item in taskData.dataList" :key="item.id" v-if="item.status != 1" class="task-card glass-card" @click="openDetail(item.id)" style="cursor:pointer;">
							<div class="task-card-top">
								<span class="task-card-time">{{item.createTime | fmtTime}} → {{item.finishTime | fmtTime}}</span>
								<div :class="`tag ${statusTagClass(item.status, item.allNum)}`">
									<template v-if="item.status == 1 && item.allNum == 0">扫描同步中</template>
									<template v-else-if="item.status == 2 && item.allNum == 0">无需同步</template>
									<template v-else>
										<span v-if="item.status != 6">{{item.status | taskStatusFilter}}</span>
										<el-popover v-else placement="top-end" title="错误原因" width="200" trigger="hover" :content="item.errMsg">
											<span slot="reference">失败，<span style="color: #409eff;">原因</span></span>
										</el-popover>
									</template>
								</div>
							</div>
							<div class="task-card-divider"></div>
							<div class="task-card-bottom" v-if="item.status != 1 || item.allNum != 0">
								<div class="task-card-progress">
									<span class="prg-item prg-blue"><span class="prg-num">{{item.allNum}}</span><span class="prg-label">总数</span></span>
									<span class="prg-item prg-green"><span class="prg-num">{{item.successNum}}</span><span class="prg-label">成功</span></span>
									<span class="prg-item prg-red"><span class="prg-num">{{item.failNum}}</span><span class="prg-label">失败</span></span>
									<span class="prg-item prg-yellow"><span class="prg-num">{{item.otherNum}}</span><span class="prg-label">其他</span></span>
								</div>
								<div class="task-card-actions" @click.stop>
									<el-button type="danger" @click="delTask(item.id)"
										:disabled="item.status == 1"
										size="mini">{{item.status == 1 ? '暂不能' : ''}}删除</el-button>
								</div>
							</div>
						</div>
						<div v-if="!loading && taskData.dataList.length === 0" class="empty-state">暂无任务</div>
					</div>
				</div>
			</div>
			<!-- 第二层：文件详情浮窗 -->
			<taskDetailOverlay :visible="detailShow" :taskId="detailTaskId" @close="detailShow = false"></taskDetailOverlay>
		</div>
	</transition>
</template>

<script>
import { jobGetTask, jobDeleteTask } from "@/api/job";
import taskDetailOverlay from './taskDetailOverlay';

export default {
	name: 'TaskOverlay',
	components: { taskDetailOverlay },
	props: {
		visible: Boolean,
		jobId: [Number, String]
	},
	data() {
		return {
			taskData: { dataList: [] },
			taskParams: { pageSize: 100 },
			loading: false,
			btnLoading: false,
			currentHeight: 0,
			detailShow: false,
			detailTaskId: null
		};
	},
	watch: {
		visible(val) {
			if (val && this.jobId) this.getTaskList();
		}
	},
	methods: {
		getTaskList() {
			if (this.jobId == null) return;
			this.loading = true;
			jobGetTask({ id: this.jobId, pageSize: this.taskParams.pageSize, pageNum: 1 }).then(res => {
				this.loading = false;
				this.taskData = res.data;
			}).catch(() => { this.loading = false; });
		},
		delTask(taskId) {
			this.$confirm("操作不可逆，将永久删除该记录，确定吗？", '提示', { type: 'warning' }).then(() => {
				this.btnLoading = true;
				jobDeleteTask(taskId).then(res => {
					this.btnLoading = false;
					this.$message({ message: res.msg, type: 'success' });
					this.getTaskList();
				}).catch(() => { this.btnLoading = false; });
			});
		},
		openDetail(taskId) {
			this.detailTaskId = taskId;
			this.detailShow = true;
		},
		statusTagClass(status, allNum) {
			if (status == 1 && allNum == 0) return 'tag-running';
			if (status == 2 && allNum == 0) return 'tag-green';
			const map = { 0: 'tag-yellow', 1: 'tag-running', 2: 'tag-green', 3: 'tag-yellow', 4: 'tag-red', 5: 'tag-red', 6: 'tag-red', 7: 'tag-red', 8: 'tag-red' };
			return map[status] || 'tag-default';
		},
	}
}
</script>

<style lang="scss" scoped>
.overlay-mask {
	position: fixed;
	top: 0; left: 0; right: 0; bottom: 0;
	background: rgba(0,0,0,0.45);
	z-index: 2000;
	display: flex;
	align-items: center;
	justify-content: center;
}
.overlay-panel {
	width: 90vw;
	max-width: 960px;
	height: 70vh;
	max-height: 70vh;
	background: var(--bg-primary);
	border-radius: 22px;
	display: flex;
	flex-direction: column;
	overflow: hidden;
	box-shadow: var(--shadow-lg);
}
.overlay-header {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 14px 20px;
	border-bottom: 1px solid var(--border-light);
	flex-shrink: 0;
}
.overlay-title {
	font-weight: 700;
	font-size: 16px;
}
.overlay-body {
	flex: 1;
	overflow-y: auto;
	padding: 16px 20px;
}

.task-current { transition: height 0.5s ease; }

.task-card-list {
	display: flex;
	flex-direction: column;
	gap: 8px;
	margin-top: 12px;
}
.task-card {
	padding: 10px 12px;
	border-radius: 22px;
	display: flex;
	flex-direction: column;
	gap: 0;
	background: #FFFFFF;
	border: 1px solid #E5E7EB;
	box-shadow: 0 1px 0 rgba(255,255,255,0.25), 0 4px 16px rgba(0,20,80,0.08);
	transition: box-shadow 0.3s cubic-bezier(0.25,0.46,0.45,0.94), transform 0.3s cubic-bezier(0.25,0.46,0.45,0.94);
	&:hover { box-shadow: 0 1px 0 rgba(255,255,255,0.35), 0 8px 24px rgba(0,20,80,0.12); }
}
.task-card-top {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 10px;
	width: 100%;
	padding-bottom: 8px;
}
.task-card-time { font-size: 12px; font-weight: 500; color: var(--text-secondary); white-space: nowrap; }
.task-card .tag { font-size: 10px; padding: 2px 6px; flex-shrink: 0; }
.task-card-divider { display: none; }
.task-card-bottom {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 8px;
	width: 100%;
}
.task-card-progress { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.prg-item {
	display: inline-flex;
	align-items: center;
	gap: 4px;
	padding: 2px 8px;
	border-radius: 22px;
	font-size: 11px;
}
.prg-num { font-weight: 700; }
.prg-label { color: var(--text-muted); font-size: 10px; }
.prg-blue { background: rgba(0,122,255,0.08); color: #007AFF; }
.prg-green { background: rgba(52,199,89,0.08); color: #34C759; }
.prg-red { background: rgba(255,59,48,0.08); color: #FF3B30; }
.prg-yellow { background: rgba(255,159,10,0.08); color: #FF9F0A; }
.task-card-actions { flex-shrink: 0; }
.empty-state { text-align: center; padding: 60px 0; color: var(--text-muted); font-size: 15px; }
.page { margin-top: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.page-tip { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter, .fade-leave-to { opacity: 0; }

@media screen and (max-width: 768px) {
	.overlay-panel { width: 96vw; height: 70vh; max-height: 70vh; }
	.overlay-body { padding: 10px 12px; }
	.task-card {
		padding: 10px 12px;
		border-radius: 22px;
		cursor: pointer;
	}
	.task-card-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 6px;
		width: 100%;
	}
	.task-card-time {
		font-size: 11px;
		font-weight: 500;
		color: var(--text-secondary);
		white-space: nowrap;
	}
	.task-card .tag {
		font-size: 9px;
		padding: 2px 6px;
		flex-shrink: 0;
	}
	.task-card-divider {
		display: none;
	}
	.task-card-bottom {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		width: 100%;
	}
	.task-card-progress {
		display: flex;
		align-items: center;
		gap: 4px;
		flex-wrap: wrap;
	}
	.prg-item {
		display: inline-flex;
		align-items: center;
		gap: 3px;
		padding: 2px 8px;
		border-radius: 22px;
		font-size: 10px;
	}
	.prg-num { font-weight: 700; }
	.prg-label { color: var(--text-muted); font-size: 10px; }
	.prg-blue { background: rgba(0,122,255,0.08); color: #007AFF; }
	.prg-green { background: rgba(52,199,89,0.08); color: #34C759; }
	.prg-red { background: rgba(255,59,48,0.08); color: #FF3B30; }
	.prg-yellow { background: rgba(255,159,10,0.08); color: #FF9F0A; }
	.task-card-actions {
		flex-shrink: 0;
		margin-left: auto;
		.el-button {
			padding: 2px 4px !important;
			font-size: 9px !important;
			border-radius: 22px !important;
		}
	}
	.page { flex-direction: column; align-items: flex-start; }
}
</style>
