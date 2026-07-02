<template>
	<div class="taskCurrent">
		<div class="content-none-data" v-if="current === null">
			{{loading ? '加载中' : '任务未在进行中'}}
		</div>
		<div class="current-box" v-else>
			<div class="current-box-top">
				<div class="current-box-top-left">
					<div class="top-line">
						<div>当前状态：扫描{{current.scanFinish ? '完成，同步' : (current.firstSync === null ? '' : '并同步')}}中</div>
						<div>开始时间：{{current.createTime | timeStampFilter}}</div>
					</div>
				</div>
				<div class="current-box-top-right">
					<el-button type="danger" @click="abortJob">中止任务</el-button>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
	import {
		jobGetTaskCurrent,
		jobPut
	} from "@/api/job";
	export default {
		name: 'Task',
		props: {
			jobId: {
				type: String,
				default: null
			}
		},
		data() {
			return {
				loading: false,
				timer: null,
				current: null
			};
		},
		created() {
			this.startRefresh();
		},
		beforeDestroy() {
			this.endRefresh();
		},
		methods: {
			startRefresh() {
				this.timer = setInterval(() => {
					this.getCurrent();
				}, 610);
			},
			endRefresh() {
				if (this.timer) {
					clearInterval(this.timer);
				}
			},
			getCurrent() {
				if (this.loading) {
					return
				}
				this.loading = true;
				jobGetTaskCurrent({
					id: this.jobId
				}).then(res => {
					this.dealWithCurrent(res.data);
				}).catch(err => {
					setTimeout(() => {
						this.loading = false;
					}, 9973);
				})
			},
			dealWithCurrent(current) {
				if (current === null) {
					if (this.current !== null) {
						this.hide();
					}
					setTimeout(() => {
						this.loading = false;
					}, 9973);
				} else {
					if (this.current === null) {
						this.show();
					}
					current.durationText = this.formatSeconds(current.duration);
					this.current = current;
					this.loading = false;
				}
			},
			abortJob() {
				this.$confirm('确定要中止当前任务吗？', '提示', {
					confirmButtonText: '确定',
					cancelButtonText: '取消',
					type: 'warning'
				}).then(() => {
					jobPut({
						id: this.jobId
					}).then(res => {
						this.$message.success(res.msg);
					});
				});
			},
			formatSeconds(seconds) {
				const days = Math.floor(seconds / (24 * 3600));
				const hours = Math.floor((seconds % (24 * 3600)) / 3600);
				const minutes = Math.floor((seconds % 3600) / 60);
				const secs = seconds % 60;
				const timeUnits = [{
						value: days,
						unit: '天'
					},
					{
						value: hours,
						unit: '小时'
					},
					{
						value: minutes,
						unit: '分钟'
					},
					{
						value: secs,
						unit: '秒'
					}
				];
				const result = timeUnits
					.filter(({
						value
					}) => value > 0)
					.map(({
						value,
						unit
					}) => value + unit)
					.join('');
				return result || '0秒';
			},
			show() {
				this.$emit('currentChange', true);
			},
			hide() {
				this.$emit('currentChange', false);
			}
		}
	}
</script>

<style scoped lang="scss">
	.taskCurrent {
		transition: height 0.3s ease;
		overflow: hidden;
	}

	.content-none-data {
		text-align: center;
		padding: 20px;
		color: var(--text-secondary);
	}

	.current-box {
		padding: 16px;
	}

	.current-box-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.current-box-top-left {
		flex: 1;
	}

	.top-line {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.current-box-top-right {
		margin-left: 16px;
	}
</style>
