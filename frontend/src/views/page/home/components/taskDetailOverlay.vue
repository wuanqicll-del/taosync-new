<template>
	<transition name="fade">
		<div v-if="visible" class="overlay-mask" @click.self="$emit('close')">
			<div class="overlay-panel" @click.stop>
				<div class="overlay-header">
					<span class="overlay-title">文件详情</span>
				</div>
				<div class="overlay-filters">
					<span class="filter-label">状态</span>
					<el-select v-model="params.status" placeholder="状态" @change="getTaskItemList" size="mini" style="width:90px;">
						<el-option label="全部" :value="null"></el-option>
						<el-option label="已失败" :value="7"></el-option>
						<el-option label="已取消" :value="4"></el-option>
					</el-select>
					<span class="filter-label">操作</span>
					<el-select v-model="params.type" placeholder="类型" @change="getTaskItemList" size="mini" style="width:80px;">
						<el-option label="全部" :value="null"></el-option>
						<el-option label="复制" :value="0"></el-option>
						<el-option label="删除" :value="1"></el-option>
						<el-option label="移动" :value="2"></el-option>
					</el-select>
				</div>
				<div class="overlay-body">
					<div class="file-list" v-if="taskItemData.dataList.length > 0">
						<div v-for="item in taskItemData.dataList" :key="item.id" class="file-item glass-card">
							<div class="file-item-grid">
								<span class="file-item-name">{{item.fileName || item.dstPath}}</span>
								<div :class="['tag', statusTagClass(item.status)]">
									<template v-if="item.status == 7">
										<el-popover placement="top-end" title="错误原因" width="200" trigger="hover" :content="item.errMsg">
											<span slot="reference">失败，原因</span>
										</el-popover>
									</template>
									<template v-else>{{item.status | taskItemStatusFilter}}</template>
								</div>
								<div v-if="item.type != 1" class="file-item-size">{{item.fileSize | sizeFilter}}</div>
								<div style="grid-column:2;justify-self:end;"><span class="tag tag-default">{{item.type == 0 ? (item.isPath ? '创建' : '复制') : (item.type == 1 ? '删除' : '移动')}}</span></div>
							</div>
							<div class="file-item-detail" v-if="item.srcPath || item.dstPath">
								<div v-if="item.type != 1" class="file-item-path">
									<span class="file-item-path-label">来源</span>
									<span class="file-item-path-text">{{item.srcPath}}</span>
								</div>
								<div class="file-item-path">
									<span class="file-item-path-label">目标</span>
									<span class="file-item-path-text">{{item.dstPath}}</span>
								</div>
								<div class="file-item-path">
									<span class="file-item-path-label">时间</span>
									<span class="file-item-path-text">{{item.createTime | timeStampFilter}}</span>
								</div>
							</div>
						</div>
					</div>
					<div v-else class="empty-state">暂无数据</div>
					<div class="page" v-if="taskItemData.count > params.pageSize">
						<el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
							:current-page="params.pageNum" :page-size="params.pageSize" :total="taskItemData.count"
							layout="total, sizes, prev, pager, next" :page-sizes="[10, 20, 50, 100]">
						</el-pagination>
					</div>
				</div>
			</div>
		</div>
	</transition>
</template>

<script>
import { jobGetTaskItem } from "@/api/job";

export default {
	name: 'TaskDetailOverlay',
	props: {
		visible: Boolean,
		taskId: [Number, String]
	},
	data() {
		return {
			taskItemData: { dataList: [], count: 0 },
			params: { taskId: null, pageSize: 50, pageNum: 1, status: null, type: null },
			loading: false
		};
	},
	watch: {
		visible(val) {
			if (val && this.taskId) {
				this.params.taskId = this.taskId;
				this.params.pageNum = 1;
				this.params.status = null;
				this.params.type = null;
				this.getTaskItemList();
			}
		}
	},
	created() {
	},
	methods: {
		getTaskItemList() {
			if (this.params.taskId == null) return;
			this.loading = true;
			jobGetTaskItem(this.params).then(res => {
				this.loading = false;
				this.taskItemData = res.data;
			}).catch(() => { this.loading = false; });
		},
		pageChange(val) {
			this.params.pageSize = val.pageSize;
			this.params.pageNum = val.pageNum;
			this.getTaskItemList();
		},
		handleSizeChange(val) { this.params.pageSize = val; this.params.pageNum = 1; this.getTaskItemList(); },
		handleCurrentChange(val) { this.params.pageNum = val; this.getTaskItemList(); },
		statusTagClass(status) {
			const map = { 0: 'tag-yellow', 1: 'tag-running', 2: 'tag-green', 3: 'tag-yellow', 4: 'tag-red', 5: 'tag-red', 6: 'tag-red', 7: 'tag-red' };
			return map[status] || 'tag-default';
		}
	}
}
</script>

<style lang="scss" scoped>
.overlay-mask {
	position: fixed;
	top: 0; left: 0; right: 0; bottom: 0;
	background: rgba(0,0,0,0.45);
	z-index: 2100;
	display: flex;
	align-items: center;
	justify-content: center;
}
.overlay-panel {
	width: 92vw;
	max-width: 960px;
	height: 70vh;
	max-height: 70vh;
	background: var(--bg-primary);
	border-radius: 22px;
	display: flex;
	flex-direction: column;
	overflow: hidden;
	box-shadow: 0 1px 0 rgba(255,255,255,0.25), 0 8px 32px rgba(0,20,80,0.12);
}
.overlay-header {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 14px 20px 10px;
	flex-shrink: 0;
}
.overlay-title {
	font-weight: 700;
	font-size: 16px;
}
.overlay-filters {
	display: flex;
	align-items: center;
	gap: 6px;
	padding: 0 20px 12px;
	border-bottom: 1px solid var(--border-light);
	flex-shrink: 0;
}
.overlay-filters ::v-deep .el-input__inner {
	height: 24px !important;
	line-height: 24px !important;
	padding: 0 24px 0 8px !important;
	font-size: 12px !important;
}
.overlay-filters ::v-deep .el-input__suffix {
	right: 4px !important;
}
.overlay-filters ::v-deep .el-input__icon {
	line-height: 24px !important;
}
.filter-label {
	font-size: 12px;
	color: var(--text-muted);
	font-weight: 500;
}
.overlay-body {
	flex: 1;
	overflow-y: auto;
	padding: 16px 20px;
}
.file-list {
	display: flex;
	flex-direction: column;
	gap: 8px;
}
.file-item {
	padding: 12px 16px;
	border-radius: 22px;
	background: #FFFFFF;
	border: 1px solid #E5E7EB;
	box-shadow: 0 1px 0 rgba(255,255,255,0.25), 0 4px 16px rgba(0,20,80,0.08);
}
.file-item-grid {
	display: grid;
	grid-template-columns: 1fr auto;
	row-gap: 6px;
	align-items: center;
}
.file-item-name {
	font-size: 13px;
	font-weight: 600;
	color: var(--text-primary);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.file-item-size {
	font-size: 12px;
	color: var(--text-muted);
}
.file-item-detail {
	margin-top: 10px;
	padding-top: 10px;
	border-top: 1px solid var(--border-light);
	display: flex;
	flex-direction: column;
	gap: 6px;
}
.file-item-path {
	display: flex;
	align-items: flex-start;
	gap: 8px;
	font-size: 12px;
}
.file-item-path-label {
	flex-shrink: 0;
	font-weight: 600;
	color: var(--text-muted);
	width: 28px;
}
.file-item-path-text {
	flex: 1;
	color: var(--text-secondary);
	word-break: break-all;
	line-height: 1.4;
}
.tag {
	display: inline-block;
	padding: 2px 10px;
	border-radius: 22px;
	font-size: 12px;
	font-weight: 500;
	white-space: nowrap;
	flex-shrink: 0;
}
.tag-default { background: var(--bg-tertiary); color: var(--text-muted); }
.tag-success { background: rgba(52,199,89,0.12); color: var(--color-success); }
.tag-danger { background: rgba(255,59,48,0.10); color: var(--color-danger); }
.tag-running { background: rgba(0,122,255,0.12); color: var(--color-primary); animation: pulse 1.5s infinite; }
.tag-green { background: rgb(40,210,85); color: #fff; }
.tag-red { background: rgb(255,59,48); color: #fff; }
.tag-yellow { background: rgb(255,180,30); color: #fff; }
@keyframes pulse {
	0%, 100% { opacity: 1; }
	50% { opacity: 0.5; }
}
.page {
	margin-top: 16px;
	display: flex;
	justify-content: flex-end;
}
.empty-state {
	text-align: center;
	padding: 60px 0;
	color: var(--text-muted);
	font-size: 15px;
}

@media screen and (max-width: 768px) {
	.overlay-panel { width: 96vw; }
	.overlay-body { padding: 10px 12px; }
	.overlay-header { padding: 10px 14px 8px; }
	.overlay-filters { padding: 0 14px 10px; gap: 6px; }
	.file-item { padding: 10px 12px; }
}
</style>
