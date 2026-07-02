<template>
	<div class="home">
		<div class="top-box">
			<el-button type="primary" @click="addShow" size="small">新建任务</el-button>
		</div>
		<div class="task-list" ref="taskList">
			<div v-for="item in jobData.dataList" :key="item.id" class="task-card glass-card" style="cursor:pointer;" @click="detail(item.id)"
				draggable="false"
				@mousedown="onDragStart($event, item)"
				@touchstart="onDragStart($event, item)">
				<div class="task-card-status" v-if="taskStatusMap[item.id]">
					<span v-if="taskStatusMap[item.id].running" class="tag tag-running">● {{taskStatusMap[item.id].text}}</span>
					<span v-else-if="taskStatusMap[item.id].text" :class="['tag', taskStatusMap[item.id].tagClass || 'tag-default']">{{taskStatusMap[item.id].text}}</span>
					<div class="task-time" v-if="taskStatusMap[item.id].running && taskStatusMap[item.id].progress">{{taskStatusMap[item.id].progress}}</div>
					<div class="task-time" v-else-if="taskStatusMap[item.id].lastTime">{{taskStatusMap[item.id].lastTime | fmtTime}}</div>
				</div>
				<div class="task-info">
					<div class="task-name">
						{{item.remark || '--'}}
					</div>
					<div class="task-meta">
						<span v-if="item.enable" class="tag tag-success">启用</span>
						<span v-else class="tag tag-danger">禁用</span>
						<span class="tag tag-default">{{item.method == 0 ? '仅新增' : (item.method == 1 ? '全同步' : '移动')}}</span>
						<span v-if="item.method != 2" class="tag tag-default">{{item.syncRule == 1 ? '数据库对比' : (item.syncRule == 2 ? '大小+名称' : '大小+名称+时间')}}</span>
					<span class="tag tag-default">{{item.isCron == 0 ? '间隔' : (item.isCron == 1 ? 'Cron' : '仅手动')}}</span>
					</div>
				</div>
				<div class="task-actions">
					<el-button v-if="taskStatusMap[item.id] && taskStatusMap[item.id].running" type="danger"
						@click.stop="abortJob(item)" size="mini">中止</el-button>
					<el-button v-else type="primary" @click.stop="putJob(item)"
						size="mini">执行</el-button>
					<el-button class="btn-purple" @click.stop="editJobShow(item)" size="mini">编辑</el-button>
					<template v-if="item.isCron != 2">
						<el-button v-if="item.enable" type="warning" @click.stop="putJob(item, true)"
							size="mini">禁用</el-button>
						<el-button v-else type="success" @click.stop="putJob(item, false)"
							size="mini">启用</el-button>
					</template>
					<span style="margin-left:auto"></span>
					<el-button type="danger" @click.stop="disableJobShow(item, true)"
						size="mini">删除</el-button>
				</div>
			</div>
			<div v-if="!loading && jobData.dataList.length === 0" class="empty-state">暂无任务</div>
		</div>
		<div class="page" v-if="jobData.count > params.pageSize">
			<el-pagination @size-change="handleSizeChange" @current-change="handleCurrentChange"
				:current-page="params.pageNum" :page-size="params.pageSize" :total="jobData.count"
				layout="prev, pager, next" :page-sizes="[10, 20, 50, 100]">
			</el-pagination>
		</div>
		<el-dialog top="5vh" :visible.sync="editShow" :append-to-body="true"
			:title="`${editData && editData.id != null ? '编辑' : '新增'}任务`" width="720px" custom-class="job-dialog" :before-close="closeShow">
			<el-form :model="editData" :rules="addRule" ref="jobRule" v-if="editShow" label-position="top" class="job-form">
				<!-- 基本信息 -->
				<div class="form-section">
					<div class="form-section-title">基本信息</div>
					<div class="form-grid">
						<el-form-item prop="remark" label="任务名称">
							<el-input v-model="editData.remark" placeholder="用来标识你的任务，选填" size="small"></el-input>
						</el-form-item>
						<el-form-item prop="alistId" label="引擎">
							<el-select v-model="editData.alistId" placeholder="请选择引擎" no-data-text="暂无引擎，请前往引擎管理创建" size="small" style="width:100%;">
								<el-option v-for="item in alistList" :label="item.url" :value="item.id">
									<span style="float: left;margin-right: 16px;">{{item.url}}{{item.remark != null ? `[${item.remark}]` : ''}}</span>
									<span style="float: right; color: #7b9dad; font-size: 13px;">{{item.userName}}</span>
								</el-option>
							</el-select>
						</el-form-item>
						<el-form-item prop="enable" label="启用状态">
							<el-switch v-model="editData.enable" :active-value="1" :inactive-value="0" v-if="editData.isCron != 2"></el-switch>
							<span v-else class="form-desc">仅手动任务始终启用</span>
						</el-form-item>
					</div>
					<el-form-item prop="srcPath" label="源目录">
						<div v-if="editData.alistId == null" class="form-desc">请先选择引擎</div>
						<div v-else>
							<div class="path-list">
								<div v-for="(item, index) in editData.srcPath" class="path-item">
									<span class="path-text">{{item}}</span>
									<el-button type="danger" size="mini" @click="delSrcPath(index)">删除</el-button>
								</div>
							</div>
							<el-button type="primary" size="mini" @click="selectPath(true)">{{editData.srcPath.length == 0 ? '选择' : '添加'}}目录</el-button>
						</div>
					</el-form-item>
					<el-form-item prop="dstPath" label="目标目录">
						<div v-if="editData.alistId == null" class="form-desc">请先选择引擎</div>
						<div v-else>
							<div class="path-list">
								<div v-for="(item, index) in editData.dstPath" class="path-item">
									<span class="path-text">{{item}}</span>
									<el-button type="danger" size="mini" @click="delDstPath(index)">删除</el-button>
								</div>
							</div>
							<el-button type="primary" size="mini" @click="selectPath(false)">{{editData.dstPath.length == 0 ? '选择' : '添加'}}目录</el-button>
						</div>
					</el-form-item>
				</div>
				<!-- 同步设置 -->
				<div class="form-section">
					<div class="form-section-title">同步设置</div>
					<div class="form-grid">
						<el-form-item prop="method" label="同步方法">
							<el-select v-model="editData.method" size="small" style="width:100%;">
								<el-option label="仅新增" :value="0">
									<span style="float: left;margin-right: 16px;">仅新增</span>
									<span style="float: right; color: #7b9dad; font-size: 13px;">仅新增目标目录没有的文件</span>
								</el-option>
								<el-option label="全同步" :value="1">
									<span style="float: left;margin-right: 16px;">全同步</span>
									<span style="float: right; color: #7b9dad; font-size: 13px;">目标目录比源目录多的文件将被删除</span>
								</el-option>
								<el-option label="移动模式" :value="2">
									<span style="float: left;margin-right: 16px;">移动模式</span>
									<span style="float: right; color: #7b9dad; font-size: 13px;">同步完成后删除源目录所有文件</span>
								</el-option>
							</el-select>
						</el-form-item>
						<el-form-item prop="syncRule" label="同步规则" v-if="editData.method != 2">
							<el-select v-model="editData.syncRule" size="small" style="width:100%;">
								<el-option label="数据库对比" :value="1">
									<span style="float: left;margin-right: 16px;">数据库对比</span>
									<span style="float: right; color: #7b9dad; font-size: 13px;">对比本地缓存，最快</span>
								</el-option>
								<el-option label="大小+名称" :value="2">
									<span style="float: left;margin-right: 16px;">大小+名称</span>
									<span style="float: right; color: #7b9dad; font-size: 13px;">对比目标目录，修复被删文件</span>
								</el-option>
								<el-option label="大小+名称+时间" :value="3">
									<span style="float: left;margin-right: 16px;">大小+名称+时间</span>
									<span style="float: right; color: #7b9dad; font-size: 13px;">三重校验，最严格</span>
								</el-option>
							</el-select>
						</el-form-item>
						<el-form-item prop="perPage" label="每页文件数">
							<el-input-number v-model="editData.perPage" :min="1" :max="500" :step="50" size="small" style="width:100%;"></el-input-number>
							<div class="form-hint">1-500，建议200</div>
						</el-form-item>
						<el-form-item prop="isCron" label="调用方式">
							<el-select v-model="editData.isCron" size="small" style="width:100%;">
								<el-option label="间隔" :value="0">
									<span style="float: left;margin-right: 16px;">间隔</span>
									<span style="float: right; color: #7b9dad; font-size: 13px;">每n分钟同步一次</span>
								</el-option>
								<el-option label="cron" :value="1">
									<span style="float: left;margin-right: 16px;">cron</span>
									<span style="float: right; color: #7b9dad; font-size: 13px;">推荐使用，有教程</span>
								</el-option>
								<el-option label="仅手动" :value="2">
									<span style="float: left;margin-right: 16px;">仅手动</span>
									<span style="float: right; color: #7b9dad; font-size: 13px;">不自动调用</span>
								</el-option>
							</el-select>
						</el-form-item>
						<template v-if="editData.isCron == 0">
							<el-form-item prop="interval" label="同步间隔">
								<el-input v-model.number="editData.interval" placeholder="请输入同步间隔" size="small">
									<template slot="append">分钟</template>
								</el-input>
								<div class="form-hint">间隔方式不会立即调用，如有需要可创建后手动执行</div>
							</el-form-item>
						</template>
						<template v-else-if="editData.isCron == 1">
							<el-form-item label="cron表达式">
								<el-input v-model="cronExpr" placeholder="分 时 日 月 周，如 0 4 * * *" size="small" @input="parseCron"></el-input>
							</el-form-item>
							<el-form-item label="执行说明" v-if="cronDesc">
								<div class="form-success">
									<div>{{cronDesc}}</div>
									<div v-if="cronNextRuns.length" style="margin-top:6px;font-size:12px;color:#909399;">
										<div>接下来执行时间</div>
										<div v-for="(t, i) in cronNextRuns.slice(0, 3)" :key="i">{{t}}</div>
										<div v-if="cronNextRuns.length > 3">...</div>
									</div>
								</div>
							</el-form-item>
						</template>
						<div class="form-grid form-grid-fixed">
							<el-form-item prop="overwriteDelete" label="覆盖前删除">
								<el-switch v-model="editData.overwriteDelete" :active-value="1" :inactive-value="0"></el-switch>
								<div class="form-hint">适合115等允许同名文件的存储</div>
							</el-form-item>
							<el-form-item prop="deleteDelay" label="删除后等待(秒)" v-if="editData.overwriteDelete == 1">
								<el-input v-model.number="editData.deleteDelay" placeholder="0" size="small" style="width:100%;height:24px;line-height:24px;"></el-input>
								<div class="form-hint">删除完成后等待指定秒数再复制，解决异步删除的网盘重复文件问题</div>
							</el-form-item>
							<el-form-item prop="srcDirName" label="追加源目录名">
								<el-switch v-model="editData.srcDirName" :active-value="1" :inactive-value="0"></el-switch>
								<div class="form-hint">目标路径下创建源目录同名文件夹</div>
							</el-form-item>
						</div>
					</div>
					<el-form-item prop="exclude" label="排除项规则">
						<div class="form-hint" style="margin-bottom:6px;">类gitignore语法 <span @click="toIgnore" style="color:var(--color-primary);text-decoration:underline;cursor:pointer;">查看教程</span></div>
						<div class="path-list">
							<div v-for="(item, index) in editData.exclude" class="path-item">
								<span class="path-text">{{item}}</span>
								<el-button type="danger" size="mini" @click="delExclude(index)">删除</el-button>
							</div>
						</div>
						<div style="display:flex;align-items:center;">
							<el-input v-model="excludeTmp" placeholder="输入排除规则" size="small" style="flex:1;margin-right:8px;"></el-input>
							<el-button type="primary" size="mini" @click="addExclude">添加</el-button>
						</div>
					</el-form-item>
				</div>
				<!-- 扫描参数 -->
				<div class="form-section">
					<div class="form-section-title">扫描参数</div>
					<div class="form-grid form-grid-fixed">
						<el-form-item prop="useCacheT" label="目标扫描缓存">
							<el-select v-model="editData.useCacheT" size="small" style="width:100%;">
								<el-option label="不使用" :value="0"></el-option>
								<el-option label="使用" :value="1"></el-option>
							</el-select>
						</el-form-item>
						<el-form-item prop="scanIntervalT" label="目标操作间隔（秒）">
							<el-input v-model.number="editData.scanIntervalT" placeholder="0" size="small" style="width:100%;"></el-input>
						</el-form-item>
						<el-form-item prop="useCacheS" label="源扫描缓存">
							<el-select v-model="editData.useCacheS" size="small" style="width:100%;">
								<el-option label="不使用" :value="0"></el-option>
								<el-option label="使用" :value="1"></el-option>
							</el-select>
						</el-form-item>
						<el-form-item prop="scanIntervalS" label="源操作间隔（秒）">
							<el-input v-model.number="editData.scanIntervalS" placeholder="0" size="small" style="width:100%;"></el-input>
						</el-form-item>
					</div>
				</div>
			</el-form>
			<span slot="footer" class="dialog-footer">
				<el-button v-if="editData && editData.id != null" type="warning" @click="clearCacheShow = true" size="small" style="float: left;">清除缓存</el-button>
				<el-button @click="closeShow" size="small">取 消</el-button>
				<el-button type="primary" @click="submit" size="small">确 定</el-button>
			</span>
		</el-dialog>
		<el-dialog :visible.sync="disableShow" :append-to-body="true" title="警告"
			width="460px" :before-close="closeDisableShow">
			<div style="color: #f56c6c;font-weight: bold;text-align: center;font-size: 20px;">
				{{disableIsDel ? '此操作不可逆，将永久删除该任务' : '将禁用任务'}}，确认吗？
			</div>
			<span slot="footer" class="dialog-footer">
				<el-button @click="closeDisableShow">取 消</el-button>
				<el-button type="primary" @click="submitDisable">确 定</el-button>
			</span>
		</el-dialog>
		<el-dialog :visible.sync="clearCacheShow" :append-to-body="true" title="确认"
			width="460px">
			<div style="text-align: center;font-size: 15px;">
				清除后下次同步将重新对比所有文件，确认清除缓存吗？
			</div>
			<span slot="footer" class="dialog-footer">
				<el-button @click="clearCacheShow = false">取 消</el-button>
				<el-button type="primary" @click="submitClearCache">确 定</el-button>
			</span>
		</el-dialog>
		<pathSelect v-if="editData" :alistId="editData.alistId" ref="pathSelect" @submit="submitPath"></pathSelect>
		<taskOverlay :visible="taskOverlayShow" :jobId="taskOverlayJobId" @close="taskOverlayShow = false"></taskOverlay>
	</div>
</template>

<script>
	import {
		jobGetJob,
		jobPut,
		jobDelete,
		jobPost,
		jobGetTask,
		jobClearCache,
		alistGet
	} from "@/api/job";
	import pathSelect from './components/pathSelect.vue';
	import taskOverlay from './components/taskOverlay';
	export default {
		name: 'Home',
		components: {
			pathSelect,
			taskOverlay
		},
		data() {
			return {
				jobData: {
					dataList: []
				},
				params: {
					pageSize: 10,
					pageNum: 1
				},
				alistList: [],
				cronExpr: '',
				cronDesc: '',
				cronNextRuns: [],
				cronList: [{
					label: 'year',
					palce: '2024'
				}, {
					label: 'month',
					palce: '1-12'
				}, {
					label: 'day',
					palce: '1-31'
				}, {
					label: 'week',
					palce: '1-53'
				}, {
					label: 'day_of_week',
					palce: '0-6 or mon,tue,wed,thu,fri,sat,sun'
				}, {
					label: 'hour',
					palce: '0-23'
				}, {
					label: 'minute',
					palce: '0-59'
				}, {
					label: 'second',
					palce: '0-59'
				}, {
					label: 'start_date',
					palce: '2000-01-01'
				}, {
					label: 'end_date',
					palce: '2040-12-31'
				}],
				cuIsSrc: false,
				loading: false,
				btnLoading: false,
				btnLoadingMap: {},
				editLoading: false,
				editData: null,
				excludeTmp: '',
				editShow: false,
				showAdvanced: false,
				disableShow: false,
				disableIsDel: false,
				disableCu: {
					id: null,
					pause: true
				},
				clearCacheShow: false,
				taskOverlayShow: false,
				taskOverlayJobId: null,
				taskStatusMap: {},
				sseSource: null,
				drag: {
					item: null, startX: 0, startY: 0, active: false,
					timer: null, clone: null, origEl: null, offsetY: 0,
					startIndex: -1, curIndex: -1, wasDragged: false, cards: []
				},
				addRule: {
					srcPath: [{
						type: 'array',
						required: true,
						message: '请选择来源目录',
						trgger: 'change'
					}],
					dstPath: [{
						type: 'array',
						required: true,
						message: '请选择目标目录',
						trgger: 'change'
					}],
					alistId: [{
						type: 'number',
						required: true,
						message: '请选择引擎',
						trgger: 'change'
					}],
					scanIntervalT: [{
						required: true,
						pattern: /^(0|[1-9]\d*)$/,
						message: '必填且须为非负整数',
						trgger: 'blur'
					}],
					scanIntervalS: [{
						required: true,
						pattern: /^(0|[1-9]\d*)$/,
						message: '必填且须为非负整数',
						trgger: 'blur'
					}]
				}
			};
		},
		created() {
			this.getJobList();
			this.connectSSE();
			this._onVisibilityChange = () => {
				if (document.visibilityState === 'visible') {
					this.checkSSEConnection();
				}
			};
			document.addEventListener('visibilitychange', this._onVisibilityChange);
		},
		beforeDestroy() {
			this.disconnectSSE();
			document.removeEventListener('visibilitychange', this._onVisibilityChange);
		},
		methods: {
			runAllJob() {
				this.$confirm("确认执行所有未禁用的任务吗？", '提示', {
					confirmButtonText: '确定',
					cancelButtonText: '取消',
					type: 'warning'
				}).then(() => {
					this.btnLoading = true;
					jobPut({
						pause: null
					}).then(res => {
						this.btnLoading = false;
						this.$message({
							message: res.msg,
							type: 'success'
						});
					}).catch(err => {
						this.btnLoading = false;
					})
				})
			},
			getJobList(silent) {
				if (!silent) this.loading = true;
				jobGetJob(this.params).then(res => {
					this.loading = false;
					this.jobData = res.data;
					// 恢复 localStorage 中保存的排序
					try {
						const savedOrder = JSON.parse(localStorage.getItem('taosync_task_order'));
						if (Array.isArray(savedOrder) && this.jobData.dataList.length > 0) {
							const idMap = {};
							this.jobData.dataList.forEach(j => { idMap[j.id] = j; });
							const ordered = [];
							savedOrder.forEach(id => { if (idMap[id]) { ordered.push(idMap[id]); delete idMap[id]; } });
							Object.values(idMap).forEach(j => ordered.push(j));
							this.jobData.dataList = ordered;
						}
					} catch (e) {}
					this.loadTaskStatuses();
				}).catch(err => {
					this.loading = false;
				})
			},
			loadTaskStatuses() {
				if (!this.jobData.dataList) return;
				const statusMap = { 0: '等待中', 1: '同步中', 2: '成功', 3: '已结束', 4: '异常中止', 5: '执行超时', 6: '创建失败', 7: '人为中止', 8: '扫描失败' };
				const classMap = { 2: 'tag-green', 3: 'tag-yellow', 4: 'tag-red', 5: 'tag-red', 6: 'tag-red', 7: 'tag-red', 8: 'tag-red', 0: 'tag-yellow', 1: 'tag-yellow' };
				const statusText = (status, allNum, phase, method) => {
					if (status === 1) {
						if (phase === 'mkdir') return '创建目录中';
						if (phase === 'pre-delete') return '复制前删除';
						if (phase === 'scanning') return '扫描中';
						if (phase === 'executing') {
							const methodMap = { 0: '复制中', 1: '同步中', 2: '移动中' };
							return methodMap[method] || '执行中';
						}
						return '扫描中';
					}
					if (status === 2 && allNum === 0) return '无需同步';
					return statusMap[status] || ('状态' + status);
				};
				const setStatus = (jobId, running, text, lastTime, statusCode, progress) => {
					this.$set(this.taskStatusMap, jobId, {
						running, text, lastTime, progress: progress || null,
						tagClass: running ? '' : (classMap[statusCode] || 'tag-default')
					});
				};
				const getProgress = (t) => {
					if (t.status !== 1) return null;
					if (t.phase === 'mkdir' && t.totalFiles > 0) {
						return (t.completedFiles || 0) + ' / ' + t.totalFiles;
					}
					if (t.phase === 'pre-delete' && t.totalFiles > 0) {
						return (t.completedFiles || 0) + ' / ' + t.totalFiles;
					}
					if (t.phase === 'executing' && t.totalFiles > 0) {
						return (t.completedFiles || 0) + ' / ' + t.totalFiles;
					}
					if (t.phase === 'scanning' && t.totalFiles > 0 && t.pendingFiles > 0) {
						return '已扫描 ' + t.totalFiles + '，待执行 ' + t.pendingFiles;
					}
					if (t.phase === 'scanning' && t.totalFiles > 0) {
						return '已扫描 ' + t.totalFiles + ' 个文件';
					}
					return null;
				};
				this.jobData.dataList.forEach(job => {
					jobGetTask({ id: job.id, pageSize: 1, pageNum: 1 }).then(res => {
						const tasks = res.data.dataList || [];
						if (tasks.length === 0) { setStatus(job.id, false, '未执行过', null, -1); return; }
						const t = tasks[0];
						const text = statusText(t.status, t.allNum || 0, t.phase, job.method);
						setStatus(job.id, t.status === 1, text, t.finishTime || t.createTime, t.status, getProgress(t));
					}).catch(() => { setStatus(job.id, false, '', null, -1); });
				});
			},
			connectSSE() {
				if (this.sseSource) {
					this.sseSource.close();
					this.sseSource = null;
				}
				this.sseSource = new EventSource('/svr/sse');
				this.sseSource.addEventListener('task_status', (e) => {
					this._sseRetryCount = 0;
					try {
						const data = JSON.parse(e.data);
						this.onTaskStatusChange(data);
					} catch (err) {}
				});
				this.sseSource.addEventListener('connected', () => {
					this._sseRetryCount = 0;
				});
				this.sseSource.onerror = () => {
					this._sseRetryCount = (this._sseRetryCount || 0) + 1;
					this.sseSource.close();
					this.sseSource = null;
					if (this._sseRetryCount <= 10) {
						const delay = Math.min(this._sseRetryCount * 2000, 10000);
						setTimeout(() => { this.connectSSE(); }, delay);
					}
					setTimeout(() => { this.loadTaskStatuses(); }, 1000);
				};
			},
			checkSSEConnection() {
				if (!this.sseSource || this.sseSource.readyState === EventSource.CLOSED) {
					this.connectSSE();
				}
			},
			disconnectSSE() {
				if (this.sseSource) {
					this.sseSource.close();
					this.sseSource = null;
				}
			},
			onTaskStatusChange(data) {
				const jobId = data.jobId;
				const status = data.status;
				const phase = data.phase;
				const allNum = data.allNum;
				const totalFiles = data.totalFiles;
				const completedFiles = data.completedFiles;
				const pendingFiles = data.pendingFiles;
				const statusMap = { 0: '等待中', 1: '同步中', 2: '成功', 3: '已结束', 4: '异常中止', 5: '执行超时', 6: '创建失败', 7: '人为中止', 8: '扫描失败' };
				const classMap = { 2: 'tag-green', 3: 'tag-yellow', 4: 'tag-red', 5: 'tag-red', 6: 'tag-red', 7: 'tag-red', 8: 'tag-red', 0: 'tag-yellow', 1: 'tag-yellow' };
				let running = status === 1;
				let text = statusMap[status] || ('状态' + status);
				let progress = null;
				if (status === 1) {
					if (phase === 'mkdir') {
						text = '创建目录中';
						if (totalFiles > 0) {
							progress = (completedFiles || 0) + ' / ' + totalFiles;
						}
					} else if (phase === 'pre-delete') {
						text = '复制前删除';
						if (totalFiles > 0) {
							progress = (completedFiles || 0) + ' / ' + totalFiles;
						}
					} else if (phase === 'executing') {
						const methodMap = { 0: '复制中', 1: '同步中', 2: '移动中' };
						const job = this.jobData.dataList && this.jobData.dataList.find(j => j.id === jobId);
						text = job ? (methodMap[job.method] || '执行中') : '执行中';
						if (totalFiles > 0) {
							progress = (completedFiles || 0) + ' / ' + totalFiles;
						}
					} else {
						text = '扫描中';
						if (totalFiles > 0 && pendingFiles > 0) {
							progress = '已扫描 ' + totalFiles + '，待执行 ' + pendingFiles;
						} else if (totalFiles > 0) {
							progress = '已扫描 ' + totalFiles + ' 个文件';
						}
					}
				}
				if (status === 2 && allNum === 0) {
					text = '无需同步';
				}
				const prev = this.taskStatusMap[jobId] || {};
				this.$set(this.taskStatusMap, jobId, {
					running, text, lastTime: data.time, progress: progress !== null ? progress : (running ? prev.progress : null),
					tagClass: running ? '' : (classMap[status] || 'tag-default')
				});
			},
			selectPath(isSrc) {
				this.cuIsSrc = isSrc;
				this.$refs.pathSelect.show();
			},
			getAlistList() {
				alistGet().then(res => {
					this.alistList = res.data;
				})
			},
			toCron() {
				window.open('https://dr34m.cn/2024/08/newpost-58/', '_blank');
			},
			toIgnore() {
				window.open('https://dr34m.cn/2024/09/newpost-60/', '_blank');
			},
			putJob(row, pause = null) {
				this.$set(this.btnLoadingMap, row.id, true);
				jobPut({
					id: row.id,
					pause: pause
				}).then(res => {
					this.$set(this.btnLoadingMap, row.id, false);
					this.$message({
						message: res.msg,
						type: 'success'
					});
					// 只更新本地数据的启用状态，不重新拉取列表（避免拖拽排序被打乱）
					if (pause !== null) {
						const item = this.jobData.dataList.find(j => j.id === row.id);
						if (item) item.enable = pause ? 0 : 1;
					}
				}).catch(err => {
					this.$set(this.btnLoadingMap, row.id, false);
				})
			},
			abortJob(row) {
				jobPut({
					id: row.id,
					pause: true,
					abort: true
				}).then(res => {
					this.$message({ message: '中止指令已发送', type: 'success' });
				}).catch(err => {})
			},
			disableJobShow(row, disableIsDel) {
				this.disableIsDel = disableIsDel;
				this.disableCu.id = row.id;
				this.disableShow = true;
			},
			editJobShow(row) {
				if (this.alistList.length == 0) {
					this.getAlistList();
				}
				this.excludeTmp = '';
				this.editData = JSON.parse(JSON.stringify(row));
				this.editData.srcPath = this.editData.srcPath.split(':');
				this.editData.dstPath = this.editData.dstPath.split(':');
				if (this.editData.exclude) {
					this.editData.exclude = this.editData.exclude.split(':');
				} else {
					this.editData.exclude = [];
				}
				// 组装 cron 表达式
				if (this.editData.isCron == 1) {
					const m = this.editData.minute || '*';
					const h = this.editData.hour || '*';
					const d = this.editData.day || '*';
					const mo = this.editData.month || '*';
					const w = this.editData.day_of_week || '*';
					this.cronExpr = `${m} ${h} ${d} ${mo} ${w}`;
					this.parseCron();
				} else {
					this.cronExpr = '';
					this.cronDesc = '';
					this.cronNextRuns = [];
				}
				this.editShow = true;
				this.showAdvanced = false;
			},
			addShow() {
				if (this.alistList.length == 0) {
					this.getAlistList();
				}
				let editData = {
					enable: 1,
					remark: '',
					srcPath: [],
					dstPath: [],
					alistId: null,
					useCacheT: 1,
					scanIntervalT: 1,
					useCacheS: 0,
					scanIntervalS: 0,
					method: 0,
					syncRule: 1,
					perPage: 200,
					overwriteDelete: 0,
					deleteDelay: 0,
						srcDirName: 1,
					interval: 1440,
					isCron: 0,
					exclude: []
				}
				this.cronList.forEach(item => {
					editData[item.label] = null;
				})
				this.editData = editData;
				this.cronExpr = '';
				this.cronDesc = '';
				this.cronNextRuns = [];
				this.excludeTmp = '';
				this.editShow = true;
				this.showAdvanced = false;
			},
			closeShow() {
				this.editShow = false;
				this.cronExpr = '';
				this.cronDesc = '';
				this.cronNextRuns = [];
			},
			parseCron() {
				const parts = this.cronExpr.trim().split(/\s+/);
				this.cronDesc = this.buildCronDesc(parts);
				this.cronNextRuns = this.calcNextRuns(parts);
			},
			getCronDesc(row) {
				const m = row.minute || '*';
				const h = row.hour || '*';
				const d = row.day || '*';
				const mo = row.month || '*';
				const w = row.day_of_week || '*';
				return this.buildCronDesc([m, h, d, mo, w]);
			},
			buildCronDesc(parts) {
				if (parts.length < 5) return '';
				const [min, hour, day, month, week] = parts;
				const desc = [];
				const weekNames = ['日','一','二','三','四','五','六'];

				// 辅助：展开字段为具体数值数组
				const expandField = (field, min, max) => {
					if (field === '*' || field === '?') {
						// 返回 null 表示全部
						return null;
					}
					const result = [];
					// 处理逗号分隔的多个值
					const tokens = field.split(',');
					for (const token of tokens) {
						if (token.includes('/')) {
							// 步长语法：*/N 或 N-M/S
							const [range, step] = token.split('/');
							const stepNum = parseInt(step);
							let start = min, end = max;
							if (range !== '*') {
								const parts = range.split('-');
								start = parseInt(parts[0]);
								end = parseInt(parts[1]);
							}
							for (let i = start; i <= end; i += stepNum) {
								result.push(i);
							}
						} else if (token.includes('-')) {
							// 范围语法：N-M
							const [s, e] = token.split('-').map(Number);
							for (let i = s; i <= e; i++) {
								result.push(i);
							}
						} else {
							// 单个值
							result.push(parseInt(token));
						}
					}
					return result.sort((a, b) => a - b);
				};

				// 展开各字段
				const weekList = expandField(week, 0, 6);
				const hourList = expandField(hour, 0, 23);
				const minList = expandField(min, 0, 59);

				// 周
				if (weekList) {
					if (weekList.length <= 3) {
						desc.push(weekList.map(w => `周${weekNames[w]}`).join('、'));
					} else {
						const first = weekList.slice(0, 2).map(w => `周${weekNames[w]}`).join('、');
						const last = `周${weekNames[weekList[weekList.length-1]]}`;
						desc.push(first + '...' + last);
					}
				}

				// 月
				if (month !== '*' && month !== '?') {
					const monthList = expandField(month, 1, 12);
					if (monthList) {
						if (monthList.length <= 3) {
							desc.push(monthList.join('、') + '月');
						} else {
							const first = monthList.slice(0, 2).join('、');
							const last = monthList[monthList.length-1];
							desc.push(first + '...' + last + '月');
						}
					}
				}

				// 日
				if (day !== '*' && day !== '?') {
					const dayList = expandField(day, 1, 31);
					if (dayList) {
						if (dayList.length <= 3) {
							desc.push(dayList.join('、') + '号');
						} else {
							const first = dayList.slice(0, 2).join('、');
							const last = dayList[dayList.length-1];
							desc.push(first + '...' + last + '号');
						}
					}
				}

				// 时
				if (hourList) {
					if (hourList.length <= 15) {
						desc.push(hourList.join('、') + '点');
					} else {
						const first3 = hourList.slice(0, 3).join('、');
						const last2 = hourList.slice(-2).join('、');
						desc.push(first3 + '...' + last2 + '点');
					}
				} else {
					// 每小时
				}

				// 分
				if (minList) {
					if (minList.length <= 15) {
						desc.push(minList.map(v => v.toString().padStart(2, '0')).join('、') + '分');
					} else {
						const first3 = minList.slice(0, 3).map(v => v.toString().padStart(2, '0')).join('、');
						const last2 = minList.slice(-2).map(v => v.toString().padStart(2, '0')).join('、');
						desc.push(first3 + '...' + last2 + '分');
					}
				} else {
					desc.push('每分钟');
				}

				return desc.length ? desc.join('，') + '执行' : '';
			},
			calcNextRuns(parts) {
				if (parts.length < 5) return [];
				const [minExpr, hourExpr, dayExpr, monthExpr, weekExpr] = parts;
				const weekNames = ['日','一','二','三','四','五','六'];

				// 辅助：展开字段
				const expandField = (field, min, max) => {
					if (field === '*' || field === '?') return null;
					const result = [];
					const tokens = field.split(',');
					for (const token of tokens) {
						if (token.includes('/')) {
							const [range, step] = token.split('/');
							const stepNum = parseInt(step);
							let start = min, end = max;
							if (range !== '*') {
								const parts = range.split('-');
								start = parseInt(parts[0]);
								end = parseInt(parts[1]);
							}
							for (let i = start; i <= end; i += stepNum) result.push(i);
						} else if (token.includes('-')) {
							const [s, e] = token.split('-').map(Number);
							for (let i = s; i <= e; i++) result.push(i);
						} else {
							result.push(parseInt(token));
						}
					}
					return result.sort((a, b) => a - b);
				};

				const minuteList = expandField(minExpr, 0, 59);
				const hourList = expandField(hourExpr, 0, 23);
				const dayList = expandField(dayExpr, 1, 31);
				const monthList = expandField(monthExpr, 1, 12);
				const weekList = expandField(weekExpr, 0, 6);

				const now = new Date();
				const results = [];
				const maxDays = 7; // 最多往后找7天

				for (let d = 0; d < maxDays && results.length < 5; d++) {
					const checkDate = new Date(now);
					checkDate.setDate(checkDate.getDate() + d);
					const year = checkDate.getFullYear();
					const month = checkDate.getMonth() + 1;
					const date = checkDate.getDate();
					const dayOfWeek = checkDate.getDay();

					// 检查月
					if (monthList && !monthList.includes(month)) continue;
					// 检查日
					if (dayList && !dayList.includes(date)) continue;
					// 检查周
					if (weekList && !weekList.includes(dayOfWeek)) continue;

					const hours = hourList || Array.from({length: 24}, (_, i) => i);
					const minutes = minuteList || [0];

					for (const h of hours) {
						for (const m of minutes) {
							if (results.length >= 5) break;
							const runTime = new Date(year, month - 1, date, h, m, 0);
							if (runTime <= now) continue;
							const mm = m.toString().padStart(2, '0');
							const dd = date.toString().padStart(2, '0');
							const weekday = weekNames[dayOfWeek];
							results.push(`${year}/${month.toString().padStart(2, '0')}/${dd}周${weekday} ${h.toString().padStart(2, '0')}:${mm}`);
						}
					}
				}

				return results;
			},
			closeDisableShow() {
				this.disableShow = false;
				this.disableCu = {
					id: null,
					pause: true
				};
			},
			submitClearCache() {
				this.editLoading = true;
				jobClearCache(this.editData.id).then(res => {
					this.editLoading = false;
					this.clearCacheShow = false;
					this.$message({
						message: '缓存已清除',
						type: 'success'
					});
				}).catch(err => {
					this.editLoading = false;
				});
			},
			addExclude() {
				if (this.excludeTmp != '') {
					this.editData.exclude.push(this.excludeTmp);
				}
				this.excludeTmp = '';
			},
			delExclude(index) {
				this.editData.exclude.splice(index, 1);
			},
			delSrcPath(index) {
				this.editData.srcPath.splice(index, 1);
			},
			delDstPath(index) {
				this.editData.dstPath.splice(index, 1);
			},
			submit() {
				this.$refs.jobRule.validate((valid) => {
					if (valid) {
						let postData = JSON.parse(JSON.stringify(this.editData));
						for (let i in postData) {
							if (postData[i] === '') {
								postData[i] = null;
							}
						}
						if (postData.isCron == 0 && postData.interval == null) {
							this.$message.error("选择间隔方式时，间隔必填");
							return
						}
						if (postData.isCron == 1) {
							const parts = this.cronExpr.trim().split(/\s+/);
							if (parts.length < 5) {
								this.$message.error("请输入有效的cron表达式（至少5段）");
								return
							}
							postData.minute = parts[0];
							postData.hour = parts[1];
							postData.day = parts[2];
							postData.month = parts[3];
							postData.day_of_week = parts[4];
							if (parts.length >= 6) {
								postData.second = parts[5];
							}
						}
						postData.srcPath = postData.srcPath.join(':');
						postData.dstPath = postData.dstPath.join(':');
						postData.exclude = postData.exclude.join(':');
						this.editLoading = true;
						jobPost(postData).then(res => {
							this.editLoading = false;
							this.$message({
								message: res.msg,
								type: 'success'
							});
							this.closeShow();
							this.getJobList();
						}).catch(err => {
							this.editLoading = false;
						})
					}
				})
			},
			submitDisable() {
				this.editLoading = true;
				if (this.disableIsDel) {
					jobDelete(this.disableCu).then(res => {
						this.editLoading = false;
						this.$message({
							message: res.msg,
							type: 'success'
						});
						this.getJobList();
						this.closeDisableShow();
					}).catch(err => {
						this.editLoading = false;
					})
				} else {
					jobPut(this.disableCu).then(res => {
						this.editLoading = false;
						this.$message({
							message: res.msg,
							type: 'success'
						});
						this.getJobList();
						this.closeDisableShow();
					}).catch(err => {
						this.editLoading = false;
					})
				}
			},
			submitPath(path) {
				if (this.cuIsSrc) {
					if (this.editData.srcPath.includes(path)) {
						this.$message({
							message: '该目录已存在',
							type: 'error'
						});
					} else {
						this.editData.srcPath.push(path);
					}
				} else {
					if (this.editData.dstPath.includes(path)) {
						this.$message({
							message: '该目录已存在',
							type: 'error'
						});
					} else {
						this.editData.dstPath.push(path);
					}
				}
			},
			detail(jobId) {
				if (this.drag.wasDragged) return;
				this.taskOverlayJobId = jobId;
				this.taskOverlayShow = true;
			},
			handleSizeChange(val) {
				this.params.pageSize = val;
				this.getJobList();
			},
			handleCurrentChange(val) {
				this.params.pageNum = val;
				this.getJobList();
			},
			// ===== 拖拽排序 =====
			onDragStart(e, item) {
				if (e.button && e.button !== 0) return;
				const cx = e.touches ? e.touches[0].clientX : e.clientX;
				const cy = e.touches ? e.touches[0].clientY : e.clientY;
				const d = this.drag;
				d.item = item; d.startX = cx; d.startY = cy;
				d.active = false; d.wasDragged = false;
				d.startIndex = d.curIndex = this.jobData.dataList.indexOf(item);
				d.origEl = e.currentTarget;
				d.timer = setTimeout(() => this.dragBegin(cx, cy), 500);
				const moveHandler = (e2) => this.onDragMove(e2);
				const endHandler = (e2) => { this.onDragEnd(e2); document.removeEventListener('mousemove', moveHandler); document.removeEventListener('mouseup', endHandler); document.removeEventListener('touchmove', moveHandler); document.removeEventListener('touchend', endHandler); };
				document.addEventListener('mousemove', moveHandler);
				document.addEventListener('mouseup', endHandler);
				document.addEventListener('touchmove', moveHandler, { passive: false });
				document.addEventListener('touchend', endHandler);
			},
			dragBegin(cx, cy) {
				const d = this.drag; if (!d.item) return;
				d.active = true; d.wasDragged = true;
				document.body.style.userSelect = 'none';
				// 创建浮动克隆
				const orig = d.origEl;
				const rect = orig.getBoundingClientRect();
				const clone = orig.cloneNode(true);
				clone.style.cssText = `position:fixed;left:${rect.left}px;top:${rect.top}px;width:${rect.width}px;z-index:9999;pointer-events:none;transition:none;box-shadow:0 8px 32px rgba(0,0,0,0.18);transform:scale(1.03);border-radius:22px;`;
				document.body.appendChild(clone);
				d.clone = clone;
				d.offsetY = cy - rect.top;
				orig.style.opacity = '0.25';
			},
			onDragMove(e) {
				const d = this.drag; if (!d.item) return;
				const cx = e.touches ? e.touches[0].clientX : e.clientX;
				const cy = e.touches ? e.touches[0].clientY : e.clientY;
				if (!d.active && (Math.abs(cx - d.startX) > 10 || Math.abs(cy - d.startY) > 10)) {
					clearTimeout(d.timer); d.timer = null; d.item = null; return;
				}
				if (!d.active) return;
				e.preventDefault();
				// 克隆跟随
				if (d.clone) d.clone.style.top = (cy - d.offsetY) + 'px';
				// 计算目标位置（用实时DOM位置）
				const list = this.$refs.taskList;
				const cards = Array.from(list.querySelectorAll('.task-card'));
				const curIdx = d.curIndex;
				let newIdx = curIdx;
				for (let i = 0; i < cards.length; i++) {
					if (i === curIdx) continue;
					const r = cards[i].getBoundingClientRect();
					const mid = r.top + r.height / 2;
					if (cy < mid && i < newIdx) newIdx = i;
					else if (cy > mid && i > newIdx) newIdx = i;
				}
				if (newIdx !== curIdx) {
					const list = [...this.jobData.dataList];
					const [item] = list.splice(curIdx, 1);
					list.splice(newIdx, 0, item);
					this.jobData.dataList = list;
					d.curIndex = newIdx;
				}
			},
			onDragEnd() {
				const d = this.drag;
				clearTimeout(d.timer); d.timer = null;
				if (d.clone) { d.clone.remove(); d.clone = null; }
				if (d.origEl) { d.origEl.style.opacity = ''; }
				document.body.style.userSelect = '';
				if (d.active) {
					d.active = false;
					// 保存排序到 localStorage
					const ids = this.jobData.dataList.map(j => j.id);
					localStorage.setItem('taosync_task_order', JSON.stringify(ids));
				}
				setTimeout(() => { d.wasDragged = false; }, 100);
				d.item = null; d.origEl = null;
			}
		}
	}
</script>

<style lang="scss">
	.home {
		width: 100%;
		padding: 0;
		box-sizing: border-box;

		.top-box {
			display: flex;
			align-items: center;
			margin-bottom: 16px;
		}
	}

	// 任务卡片列表
	.task-list {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.task-card {
		padding: 10px 12px;
		border-radius: 22px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
		background: #FFFFFF;
		border: 1px solid #E5E7EB;
		box-shadow: 0 1px 0 rgba(255,255,255,0.25), 0 4px 16px rgba(0,20,80,0.08);
		transition: box-shadow 0.3s cubic-bezier(0.25,0.46,0.45,0.94), transform 0.3s cubic-bezier(0.25,0.46,0.45,0.94);
		user-select: none;
		-webkit-user-select: none;
		touch-action: pan-y;
		&:hover {
			box-shadow: 0 1px 0 rgba(255,255,255,0.35), 0 8px 24px rgba(0,20,80,0.12);
		}
	}

	.task-info {
		min-width: 0;
	}

	.task-name {
		font-size: 13px;
		font-weight: 600;
		color: var(--text-primary);
		line-height: 1.3;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.task-meta {
		display: flex;
		gap: 4px;
		margin-top: 4px;
		flex-wrap: wrap;
	}

	.tag {
		display: inline-block;
		padding: 2px 6px;
		border-radius: 22px;
		font-size: 9px;
		font-weight: 600;
		white-space: nowrap;
	}
	.tag-success { background: rgba(52,199,89,0.12); color: var(--color-success); }
	.tag-danger { background: rgba(255,59,48,0.10); color: var(--color-danger); }
	.tag-default { background: var(--bg-tertiary); color: var(--text-muted); }
	.tag-running { background: rgba(0,122,255,0.12); color: var(--color-primary); animation: pulse 1.5s infinite; }
	.tag-done { background: var(--bg-tertiary); color: var(--text-muted); }
	.tag-green { background: rgb(40,210,85); color: #fff; }
	.tag-red { background: rgb(255,59,48); color: #fff; }
	.tag-yellow { background: rgb(255,180,30); color: #fff; }

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.task-card-status {
		position: absolute;
		right: 12px;
		top: 10px;
		text-align: right;
		font-size: 10px;
		.tag { font-size: 10px; padding: 2px 6px; }
	}

	.task-time {
		color: var(--text-muted);
		margin-top: 4px;
		font-size: 10px;
	}

	.task-actions {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		flex-shrink: 0;
		flex: 1;
		.el-button, .el-button--mini {
			padding: 2px 5px !important;
			font-size: 9px !important;
			min-width: 36px !important;
			min-height: 20px !important;
			border-radius: 22px !important;
			line-height: 1 !important;
		}
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
		justify-content: center;
	}

	// 编辑弹窗表单
	.job-form .el-form-item {
		margin-bottom: 8px;
	}
	.job-form .el-form-item__label {
		font-size: 12px !important;
		font-weight: 600 !important;
		color: var(--text-primary) !important;
		padding-bottom: 2px !important;
		line-height: 20px !important;
	}
	.job-form .el-form-item__content .el-input .el-input__inner {
		height: 24px !important;
		line-height: 24px !important;
		font-size: 12px !important;
	}
	.form-section {
		margin-bottom: 12px;
		padding: 12px 14px;
		border-radius: 14px;
		background: var(--bg-secondary);
		border: 1px solid var(--border-light);
	}
	.form-section-title {
		font-size: 13px;
		font-weight: 700;
		color: var(--text-primary);
		margin-bottom: 8px;
	}
	.form-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0 14px;
	}
	.form-grid-fixed {
		grid-template-columns: 1fr 1fr !important;
	}
	.form-hint {
		font-size: 11px;
		font-weight: 400;
		color: var(--text-muted);
		margin-top: 2px;
		line-height: 1.4;
	}
	.form-desc {
		font-size: 12px;
		font-weight: 400;
		color: var(--text-muted);
	}
	.form-success {
		font-size: 12px;
		font-weight: 400;
		color: #67c23a;
	}
	.path-list {
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin-bottom: 6px;
	}
	.path-item {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 3px 6px 3px 10px;
		border-radius: 22px;
		background: var(--bg-tertiary);
		border: 1px solid var(--border-light);
		min-height: 30px;
		.el-button {
			padding: 2px 8px !important;
			font-size: 11px !important;
			border-radius: 14px !important;
			line-height: 1 !important;
			min-height: auto !important;
			height: auto !important;
		}
	}
	.path-text {
		flex: 1;
		font-size: 12px;
		font-weight: 400;
		color: var(--text-primary);
		word-break: break-all;
		line-height: 1.4;
	}

	// 桌面端适配（和移动端一样）
	@media screen and (min-width: 769px) {
		.task-card {
			flex-direction: column;
			align-items: flex-start;
		}
		.task-actions {
			width: 100%;
		}
	}

	// 移动端适配
	@media screen and (max-width: 768px) {
		.task-card {
			flex-direction: column;
			align-items: flex-start;
			padding: 12px 14px;
		}

		.task-status {
			margin-left: 0;
		}

		.task-actions {
			width: 100%;

			.el-button {
				margin-left: 0 !important;
				padding: 2px 5px !important;
				font-size: 9px !important;
			}
		}

		.form-grid {
			grid-template-columns: 1fr;
		}
		.form-section {
			padding: 12px;
			border-radius: 12px;
		}
	}
	// append 栏（秒字 + 添加按钮）
	.el-input-group__append {
		background: transparent !important;
		border: none !important;
		box-shadow: none !important;
		color: var(--text-muted);
		.el-button {
			color: var(--text-muted) !important;
			border: none !important;
			background: transparent !important;
			box-shadow: none !important;
			font-size: 12px !important;
			&:hover {
				color: var(--color-primary) !important;
			}
		}
	}
</style>