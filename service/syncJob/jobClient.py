"""
@Author：dr34m
@Date  ：2024/7/11 12:14 
"""
import itertools
import json
import logging
import threading
import time
from collections import defaultdict

from apscheduler.schedulers.background import BackgroundScheduler
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

from common.LNG import G
from common import sse
from mapper import jobMapper
from service.alist import alistService
from service.syncJob import taskService


class CopyItem:
    def __init__(self, srcPath, dstPath, fileName, fileSize, method, jobTask):
        self.jobTask = jobTask
        self.alistClient = self.jobTask.alistClient
        self.taskId = self.jobTask.taskId
        self.srcPath = srcPath
        self.dstPath = dstPath
        self.fileName = fileName
        self.fileSize = fileSize
        self.copyType = 0 if method < 2 else 2
        self.alistTaskId = None
        self.status = 0
        self.progress = 0.0
        self.errMsg = None
        self.createTime = int(time.time())
        self.doingKey = None

    def doByThread(self):
        doThread = threading.Thread(target=self.doIt)
        doThread.start()

    def doIt(self):
        try:
            if self.jobTask.breakFlag:
                self.status = 4
            else:
                self.alistTaskId = self.alistClient.copyFile(self.srcPath, self.dstPath, self.fileName)
        except Exception as e:
            self.errMsg = str(e)
            self.status = 7
        else:
            if self.alistTaskId is None:
                self.status = 2
            elif self.status != 4:
                self.checkAndGetStatus()
        self.endIt()

    def checkAndGetStatus(self):
        """
        不断检查状态并更新
        :return:
        """
        while True:
            if self.jobTask.breakFlag:
                self.status = 4
                if self.alistTaskId is not None:
                    try:
                        self.alistClient.copyTaskCancel(self.alistTaskId)
                        self.alistClient.copyTaskDelete(self.alistTaskId)
                    except Exception as e:
                        self.status = 7
                        self.errMsg = str(e)
                break
            cuTime = time.time()
            time.sleep(0.61 if cuTime - self.jobTask.lastWatching < 3 else 2.93)
            retry404 = 0
            try:
                taskInfo = self.alistClient.taskInfo(self.alistTaskId)
            except Exception as e:
                logger = logging.getLogger()
                logger.exception(e)
                eMsg = str(e)
                if '404' in eMsg:
                    # 404可能是AList还没处理完，最多重试3次，每次间隔3秒
                    while retry404 < 3:
                        retry404 += 1
                        time.sleep(3)
                        if self.jobTask.breakFlag:
                            break
                        try:
                            taskInfo = self.alistClient.taskInfo(self.alistTaskId)
                            eMsg = None
                            break
                        except Exception as e2:
                            eMsg = str(e2)
                    if eMsg and '404' in eMsg:
                        eMsg = (G('task_may_delete'))
                    elif eMsg is None:
                        continue
                taskInfo = {
                    'state': 7,
                    'progress': None,
                    'error': eMsg
                }
            if taskInfo['state'] == self.status and taskInfo['progress'] == self.progress:
                continue
            self.status = taskInfo['state']
            self.progress = taskInfo['progress']
            self.errMsg = taskInfo['error'] if taskInfo['error'] else None
            # 删除结束的任务
            if taskInfo['state'] in [2, 4, 7]:
                try:
                    self.alistClient.copyTaskDelete(self.alistTaskId)
                    break
                except Exception:
                    break

    def endIt(self):
        if self.copyType == 2 and self.status == 2:
            try:
                self.alistClient.deleteFile(self.srcPath, [self.fileName], self.jobTask.job['scanIntervalS'])
            except Exception as e:
                self.status = 7
                self.errMsg = G('copy_success_but_delete_fail').format(str(e))
        self.jobTask.copyHook(self.srcPath, self.dstPath, self.fileName, self.fileSize, self.alistTaskId, self.status,
                              errMsg=self.errMsg, copyType=self.copyType, createTime=self.createTime)
        del self.jobTask.doing[self.doingKey]


class JobTask:
    def __init__(self, taskId, vm):
        """
        作业任务类
        :param taskId: 任务id
        :param vm: 作业上下文
        """
        self.taskId = taskId
        self.jobClient = vm
        self.job = self.jobClient.job
        self.alistClient = alistService.getClientById(self.job['alistId'])
        self.createTime = time.time()
        # 已完成（包含成功或者失败）
        self.finish = []
        # 已经提交到alist的任务
        self.doing = {}
        # 等待提交到alist的任务
        self.waiting = []
        # 上次查看详情的时间戳，低于3秒表示正在看，在看则快速检查状态，否则低速检查以节约开销
        self.lastWatching = 0.0
        # 队列序号，用作复制任务的doingKey
        self.queueNum = 0
        # sync全部任务加入队列标识
        self.scanFinish = False
        # 首个文件开始同步时间
        self.firstSync = None
        # 手动中止标识
        self.breakFlag = False
        # 源端文件缓存，用于判断文件是否变化
        self.fileCache = {}
        self.cacheByDir = {}
        self.cacheSubDirs = {}
        if self.job['method'] != 2:
            self.fileCache = jobMapper.getFileCache(self.job['id'])
            # 预处理缓存为按目录索引
            for cp, ci in self.fileCache.items():
                idx = cp.rfind('/')
                if idx < 0:
                    continue
                dirPath = cp[:idx + 1]
                fileName = cp[idx + 1:]
                if dirPath not in self.cacheByDir:
                    self.cacheByDir[dirPath] = {}
                self.cacheByDir[dirPath][fileName] = ci
                # 计算子目录：从根目录到文件所在目录的每一层都记录
                relFromRoot = dirPath
                while relFromRoot:
                    parentEnd = relFromRoot.rfind('/', 0, len(relFromRoot) - 1)
                    if parentEnd < 0:
                        break
                    parentDir = relFromRoot[:parentEnd + 1]
                    childName = relFromRoot[parentEnd + 1:]
                    if parentDir not in self.cacheSubDirs:
                        self.cacheSubDirs[parentDir] = set()
                    self.cacheSubDirs[parentDir].add(childName)
                    relFromRoot = parentDir
        # 收集本次扫描到的源端文件信息，用于同步结束后更新缓存
        self.scannedSrcFiles = []
        # 收集被删除的目录源路径
        self.deletedDirs = set()
        # 扫描阶段标志：扫描完成后设为False，期间所有操作收集到pending列表
        self.scanPhase = True
        self.currentPhase = 'scanning'  # scanning / mkdir / pre-delete / executing
        self.scanComplete = False
        self.allSrcScanned = True
        self.pendingMkdirs = []
        self.pendingMkdirSet = set()  # 用于扫描阶段去重
        self.pendingCopies = []
        self.pendingDeletes = []
        # 预扫描的源目录文件缓存，避免递归时重复调用目录列表接口
        self.preScannedSrc = {}
        # 总文件数，用于进度显示
        self.totalFiles = 0
        syncThread = threading.Thread(target=self.sync)
        syncThread.start()
        self.currentTasks = {}
        submitThread = threading.Thread(target=self.taskSubmit)
        submitThread.start()

    def getCurrent(self):
        """
        总结并返回详情（高实时性）
        :return: {
            'scanFinish': True,
            'doingTask': [{
                'srcPath': 来源目录,
                'dstPath': 目标目录,
                'fileName': 文件名,
                'fileSize': 文件大小,
                'status': 状态,
                'type': 方式，0-复制（对于目录则是创建），1-删除，2-移动,
                'progress': 进度,
                'errMsg': 错误信息,
                'createTime': 创建时间
            }],
            'createTime': int(self.createTime),
            'duration': int(self.lastWatching - self.createTime),
            'firstSync': int(self.firstSync) if self.firstSync is not None else None,
            'num': {
                'wait': 0,
                'running': 1,
                'success': 2,
                'fail': 7,
                'other': 0
            },
            'size': {
                'wait': 0,
                'running': 1,
                'success': 2,
                'fail': 7,
                'other': 0
            }
        }
        """
        self.lastWatching = time.time()
        waits = [{
            'srcPath': waitItem.srcPath,
            'dstPath': waitItem.dstPath,
            'isPath': 0,
            'fileName': waitItem.fileName,
            'fileSize': waitItem.fileSize,
            'status': waitItem.status,
            'type': waitItem.copyType,
            'errMsg': waitItem.errMsg,
            'createTime': waitItem.createTime
        } for waitItem in self.waiting]
        dos = [{
            'srcPath': doItem.srcPath,
            'dstPath': doItem.dstPath,
            'isPath': 0,
            'fileName': doItem.fileName,
            'fileSize': doItem.fileSize,
            'status': doItem.status,
            'type': doItem.copyType,
            'errMsg': doItem.errMsg,
            'createTime': doItem.createTime
        } for doItem in self.doing.values()]
        allTask = list(itertools.chain(waits, dos, self.finish))
        keyValSpace = {
            'wait': 0,
            'running': 1,
            'success': 2,
            'fail': 7,
            'other': -1
        }
        currentTasks = {}
        for val in keyValSpace.values():
            currentTasks[val] = []
        # 其他类型数组
        otk = []
        otkStatus = [3, 4, 5, 6, 8, 9]
        grouped = defaultdict(list)
        for taskItem in allTask:
            grouped[taskItem['status']].append(taskItem)
        for status, tasks in grouped.items():
            tasks.sort(key=lambda x: x['createTime'])
            if status in otkStatus:
                otk.extend(tasks)
            else:
                currentTasks[status] = tasks
        currentTasks[-1] = otk
        self.currentTasks = currentTasks
        result = {
            'scanFinish': self.scanFinish,
            'doingTask': currentTasks[1],
            'createTime': int(self.createTime),
            'duration': int(self.lastWatching - self.createTime),
            'firstSync': int(self.firstSync) if self.firstSync is not None else None,
        }
        return result

    def getCurrentByStatus(self, status):
        return self.currentTasks[status]

    def taskSubmit(self):
        """
        队列检验与提交
        :return:
        """
        lastCompletedNum = 0
        while True:
            if self.breakFlag:
                break
            time.sleep(0.5)
            # 有新任务完成时推送进度
            curCompleted = len(self.finish)
            if curCompleted != lastCompletedNum and self.firstSync is not None:
                lastCompletedNum = curCompleted
                sse.notify_job_status(self.job['id'], 1, self.taskId, phase='executing',
                                      total_files=self.pendingFileCount, completed_files=curCompleted)
            doingNums = len(self.doing.keys())
            waitingNums = len(self.waiting)
            if not self.scanFinish or doingNums != 0 or waitingNums != 0:
                while doingNums < 20:
                    if self.breakFlag:
                        break
                    if waitingNums == 0:
                        break
                    else:
                        if self.firstSync is None:
                            self.firstSync = time.time()
                        self.queueNum += 1
                        self.doing[self.queueNum] = self.waiting.pop(0)
                        self.doing[self.queueNum].doingKey = self.queueNum
                        self.doing[self.queueNum].doByThread()
                        doingNums = len(self.doing.keys())
                        waitingNums = len(self.waiting)
            else:
                # 重新检查，避免竞态：等待队列可能在读取之后才被填入
                if len(self.waiting) == 0 and len(self.doing.keys()) == 0:
                    break
        tryTime = 0
        while len(self.doing.keys()) > 0:
            tryTime += 1
            time.sleep(.5)
            if tryTime > 3:
                break
        jobMapper.addJobTaskItemMany(self.finish)
        self.updateTaskStatus()
        self.jobClient.jobDoing = False
        self.jobClient.currentJobTask = None

    def copyHook(self, srcPath, dstPath, name, size, alistTaskId=None, status=0, errMsg=None, isPath=0,
                 copyType=0, createTime=int(time.time())):
        """
        复制文件回调
        :param srcPath: 来源目录
        :param dstPath: 目标目录
        :param name: 文件名
        :param size: 文件大小
        :param alistTaskId: alist任务id
        :param status: 0-等待中，1-运行中，2-成功，3-取消中，4-已取消，5-出错（将重试），6-失败中，
                        7-已失败，8-等待重试中，9-等待重试回调执行中，10-目录扫描失败，11-目录创建失败
        :param errMsg: 错误信息
        :param isPath: 是否是目录，0-文件，1-目录
        :param copyType: 0-复制，2-移动
        :param createTime:
        """
        self.finish.append({
            'taskId': self.taskId,
            'srcPath': srcPath,
            'dstPath': dstPath,
            'isPath': isPath,
            'fileName': name,
            'fileSize': size,
            'type': copyType,
            'alistTaskId': alistTaskId,
            'status': status,
            'errMsg': errMsg,
            'createTime': createTime
        })

    def delHook(self, dstPath, name, size, status=2, errMsg=None, isPath=0, createTime=int(time.time()), srcPath=None):
        """
        删除文件回调
        :param dstPath: 目标目录
        :param name: 文件名
        :param size: 文件大小
        :param status: 2-成功、7-失败
        :param errMsg: 错误信息
        :param isPath: 是否是目录，0-文件，1-目录
        :param createTime: 创建时间
        :param srcPath: 源文件/目录完整路径，用于删除失败时保留缓存
        """
        self.finish.append({
            'taskId': self.taskId,
            'srcPath': srcPath,
            'dstPath': dstPath,
            'isPath': isPath,
            'fileName': name,
            'fileSize': size,
            'type': 1,
            'alistTaskId': None,
            'status': status,
            'errMsg': errMsg,
            'createTime': createTime
        })

    def sync(self):
        """
        同步方法：先扫描所有源目录，再按目标目录并行对比同步
        采用先扫描后执行模式：扫描阶段收集所有操作，扫描完成后统一执行
        """
        try:
            sse.notify_job_status(self.job['id'], 1, self.taskId, phase='scanning')
            self._doSync()
            if not self.breakFlag:
                self.scanComplete = True
        finally:
            self._executePendingOps()

    def _doSync(self):
        srcPathList = self.job['srcPath'].split(':')
        dstPathList = self.job['dstPath'].split(':')
        jobExclude = self.job['exclude']
        spec = None
        if jobExclude is not None:
            spec = PathSpec.from_lines(GitWildMatchPattern, jobExclude.split(':'))
        # 第一步：扫描所有源目录，收集源文件信息（只扫一次）
        allSrcItems = []  # [(srcPath, srcName, srcFiles), ...]
        for srcItem in srcPathList:
            if self.breakFlag:
                return
            srcItem = srcItem.strip()
            if not srcItem.endswith('/'):
                srcItem = srcItem + '/'
            srcName = srcItem.rstrip('/').split('/')[-1]
            try:
                srcFiles = self.listDir(srcItem, spec, srcItem)
            except Exception:
                self.breakFlag = True
                self.allSrcScanned = False
                return
            # 收集源端文件信息
            for key in srcFiles.keys():
                if not key.endswith('/'):
                    self.scannedSrcFiles.append((srcItem + key, srcFiles[key][0], srcFiles[key][1]))
            allSrcItems.append((srcItem, srcName, srcFiles))
        # 填充预扫描缓存，供递归调用使用，避免重复调用目录列表接口
        for srcItem, srcName, srcFiles in allSrcItems:
            self.preScannedSrc[srcItem] = srcFiles
        # 第二步：按规则执行同步
        syncRule = self.job.get('syncRule', 1)
        appendSrcDir = self.job.get('srcDirName', 1)
        if self.job['method'] == 2:
            # 移动模式：不扫描不对比，直接复制到目标目录后删除源文件
            for srcItem, srcName, srcFiles in allSrcItems:
                if self.breakFlag:
                    return
                for dstItem in dstPathList:
                    dstItem = dstItem.strip()
                    if not dstItem.endswith('/'):
                        dstItem = dstItem + '/'
                    if appendSrcDir:
                        finalDst = dstItem + srcName + '/'
                    else:
                        finalDst = dstItem
                    if finalDst.rstrip('/') == srcItem.rstrip('/'):
                        continue
                    self._moveToDst(srcItem, finalDst, spec, srcItem, srcFiles)
            return
        if syncRule == 1:
            # 规则1：不启动目标线程，主同步线程直接对比并复制到所有目标目录
            for srcItem, srcName, srcFiles in allSrcItems:
                if self.breakFlag:
                    return
                allDst = []
                for dstItem in dstPathList:
                    dstItem = dstItem.strip()
                    if not dstItem.endswith('/'):
                        dstItem = dstItem + '/'
                    if appendSrcDir:
                        finalDst = dstItem + srcName + '/'
                    else:
                        finalDst = dstItem
                    if finalDst.rstrip('/') != srcItem.rstrip('/'):
                        allDst.append(finalDst)
                if allDst:
                    self.syncWithHave(srcItem, allDst[0], spec, srcItem, allDst[0], srcFiles, allDst)
            return
        # 规则2/3：按目标目录启动线程并行同步
        def syncOneDst(dstItem):
            for srcItem, srcName, srcFiles in allSrcItems:
                if self.breakFlag:
                    return
                if appendSrcDir:
                    finalDst = dstItem + srcName + '/'
                    # 直接创建追加的目录，确保扫描时目录存在
                    try:
                        self.alistClient.mkdir(finalDst.rstrip('/'), self.job['scanIntervalT'])
                    except Exception:
                        pass
                else:
                    finalDst = dstItem
                if finalDst.rstrip('/') == srcItem.rstrip('/'):
                    continue
                self.mkdir(finalDst)
                self.syncWithHave(srcItem, finalDst, spec, srcItem, finalDst, srcFiles)
        dstThreads = []
        for dstItem in dstPathList:
            dstItem = dstItem.strip()
            if not dstItem.endswith('/'):
                dstItem = dstItem + '/'
            t = threading.Thread(target=syncOneDst, args=(dstItem,))
            t.start()
            dstThreads.append(t)
        for t in dstThreads:
            t.join()

    def copyFile(self, srcPath, dstPath, fileName, fileSize):
        """
        复制文件
        vm.job['method']: 0-仅新增，1-全同步，2-移动模式
        vm.job['copyHook']: 复制文件回调，（srcPath, dstPath, name, size, alistTaskId=None, status=0, errMsg=None, isPath=0）
        vm.job['delHook']: 删除文件回调，（dstPath, name, size, status=2:2-成功、7-失败, errMsg=None, isPath=0）
        :param srcPath: 源目录
        :param dstPath: 目标目录
        :param fileName: 文件名
        :param fileSize: 文件大小
        :return:
        """
        if self.breakFlag:
            return
        copyItem = CopyItem(srcPath, dstPath, fileName, fileSize, self.job['method'], self)
        if self.scanPhase:
            self.pendingCopies.append(copyItem)
        else:
            self.waiting.append(copyItem)

    def mkdir(self, path):
        """创建目录，扫描阶段收集（去重），执行阶段立即执行"""
        cleaned = path.rstrip('/')
        if self.scanPhase:
            if cleaned not in self.pendingMkdirSet:
                self.pendingMkdirSet.add(cleaned)
                self.pendingMkdirs.append(cleaned)
            return
        try:
            self.alistClient.mkdir(cleaned, self.job['scanIntervalT'])
        except Exception:
            pass

    def delFile(self, path, fileName, size, srcPath=None, isOverwrite=False):
        """
        删除文件（或目录）
        :param path: 目标所在路径
        :param fileName: 文件名（或目录名）
        :param size: 大小（文件）或空对象（目录）
        :param srcPath: 源文件/目录完整路径，用于删除失败时保留缓存
        :param isOverwrite: 是否是覆盖前删除
        :return:
        """
        if self.breakFlag:
            return
        if self.scanPhase:
            self.pendingDeletes.append((path, fileName, size, srcPath, isOverwrite))
            return
        self._doDelete(path, fileName, size, srcPath)

    def _doDelete(self, path, fileName, size, srcPath=None):
        """实际执行删除操作"""
        isPath = fileName.endswith('/')
        status = 2
        errMsg = None
        createTime = int(time.time())
        try:
            self.alistClient.deleteFile(path, [fileName if not isPath else fileName[:-1]], self.job['scanIntervalT'])
        except Exception as e:
            errMsg = str(e)
            # 990019：115网盘删除操作尚未完成，重试3次，每次间隔3秒
            if '990019' in errMsg:
                for i in range(3):
                    if self.breakFlag:
                        break
                    time.sleep(3)
                    try:
                        self.alistClient.deleteFile(path, [fileName if not isPath else fileName[:-1]], self.job['scanIntervalT'])
                        errMsg = None
                        break
                    except Exception as e2:
                        errMsg = str(e2)
            if errMsg:
                status = 7
        self.delHook(path, fileName, None if isPath else size, status, errMsg, isPath, createTime, srcPath)

    def listDir(self, path, spec, rootPath, isSrc=True):
        """
        列出目录
        self.job['useCacheT']: 扫描目标目录时，是否使用缓存，0-不使用，1-使用
        self.job['scanIntervalT']: 目标目录扫描间隔，单位秒
        self.job['useCacheS']: 扫描源目录时，是否使用缓存，0-不使用，1-使用
        self.job['scanIntervalS']: 源目录扫描间隔，单位秒
        :param path:
        :param spec:
        :param rootPath:
        :param isSrc:
        :return:
        """
        useCache = self.job[f"useCache{'S' if isSrc else 'T'}"]
        scanInterval = self.job[f"scanInterval{'S' if isSrc else 'T'}"]
        perPage = self.job.get('perPage', 200)
        try:
            return self.alistClient.fileListApi(path, useCache, scanInterval, spec, rootPath, perPage)
        except Exception as e:
            logger = logging.getLogger()
            errMsg = G('scan_error').format(G('src' if isSrc else 'dst'), str(e))
            logger.error(errMsg)
            logger.exception(e)
            self.copyHook(path if isSrc else None, None if isSrc else path, None, None, status=7, errMsg=errMsg,
                          isPath=1)
            self.allSrcScanned = False
            self.breakFlag = True
            raise e

    def _moveToDst(self, srcPath, dstPath, spec, srcRootPath, srcFiles):
        """移动模式：直接复制到目标目录"""
        if self.breakFlag:
            return
        needMkdir = True
        for key in srcFiles.keys():
            if self.breakFlag:
                return
            if not key.endswith('/'):
                if needMkdir:
                    self.mkdir(dstPath)
                    needMkdir = False
                self.copyFile(srcPath, dstPath, key, srcFiles[key][0])
            else:
                # 递归扫描子目录，获取子目录文件列表再递归
                subSrcPath = srcPath + key
                cached = self.preScannedSrc.get(subSrcPath)
                if cached is not None:
                    childFiles = cached
                else:
                    try:
                        childFiles = self.listDir(subSrcPath, spec, srcRootPath)
                    except Exception:
                        if self.breakFlag:
                            return
                        continue
                    self.preScannedSrc[subSrcPath] = childFiles
                self._moveToDst(subSrcPath, dstPath + key, spec, srcRootPath, childFiles)

    def syncWithHave(self, srcPath, dstPath, spec, srcRootPath, dstRootPath, srcFiles=None, allDst=None):
        """
        扫描并同步-根据同步规则对比
        :param srcPath: 来源路径，以/结尾
        :param dstPath: 目标路径，以/结尾
        :param spec: 排除项规则
        :param srcRootPath: 来源目录根目录，以/结尾
        :param dstRootPath: 目标目录根目录，以/结尾
        :param srcFiles: 外部传入的源文件列表，为None时自行扫描
        :param allDst: 规则1时所有目标目录列表，为None时用dstPath
        """
        if self.breakFlag:
            return
        if srcFiles is None:
            # 优先使用预扫描缓存，避免重复调用目录列表接口
            cached = self.preScannedSrc.get(srcPath)
            if cached is not None:
                srcFiles = cached
            else:
                try:
                    srcFiles = self.listDir(srcPath, spec, srcRootPath)
                except Exception:
                    return
                self.preScannedSrc[srcPath] = srcFiles
            # 收集源端文件信息（用于同步后更新缓存）
            for key in srcFiles.keys():
                if not key.endswith('/'):
                    self.scannedSrcFiles.append((srcPath + key, srcFiles[key][0], srcFiles[key][1]))
        syncRule = self.job.get('syncRule', 1)
        if syncRule == 1:
            # 规则1：数据库缓存对比，不扫描目标目录
            self._syncByCache(srcPath, dstPath, spec, srcRootPath, dstRootPath, srcFiles, allDst)
        else:
            # 规则2/3：扫描目标目录，直接对比
            self._syncByTarget(srcPath, dstPath, spec, srcRootPath, dstRootPath, srcFiles, syncRule)
        # 对比完成后推送扫描进度（此时 pending_files 包含当前目录的操作）
        sse.notify_job_status(self.job['id'], 1, self.taskId, phase='scanning',
                              total_files=len(self.scannedSrcFiles),
                              pending_files=len(self.pendingMkdirs) + len(self.pendingCopies) + len(self.pendingDeletes))

    def _syncByCache(self, srcPath, dstPath, spec, srcRootPath, dstRootPath, srcFiles, allDst=None):
        """规则1：数据库缓存对比"""
        # 从预处理索引获取当前目录的缓存
        cachedHere = self.cacheByDir.get(srcPath, {})
        cachedDirs = self.cacheSubDirs.get(srcPath, set())
        # 双向对比：处理 srcFiles 中的每个条目
        needMkdir = True  # 本目录是否需要先mkdir
        dstList = allDst if allDst else [dstPath]
        for key in srcFiles.keys():
            if self.breakFlag:
                return
            if not key.endswith('/'):
                cached = cachedHere.get(key)
                if cached is not None and cached == srcFiles[key]:
                    continue
                if needMkdir:
                    for d in dstList:
                        self.mkdir(d)
                    needMkdir = False
                if self.job.get('overwriteDelete', 0):
                    for d in dstList:
                        self.delFile(d, key, srcFiles[key][0], srcPath + key, isOverwrite=True)
                for d in dstList:
                    self.copyFile(srcPath, d, key, srcFiles[key][0])
            else:
                subDstList = [d + key for d in dstList] if allDst else None
                self.syncWithHave(srcPath + key, dstPath + key, spec, srcRootPath, dstRootPath, None, subDstList)
        # 检测删除（仅全同步模式）
        if self.job['method'] == 1:
            for fileName, cachedInfo in cachedHere.items():
                if fileName not in srcFiles:
                    for d in dstList:
                        try:
                            self.delFile(d, fileName, cachedInfo[0], srcPath + fileName)
                        except Exception:
                            pass
            srcDirs = {k.rstrip('/') for k in srcFiles if k.endswith('/')}
            for dirName in cachedDirs:
                if dirName.rstrip('/') not in srcDirs:
                    self.deletedDirs.add(srcPath + dirName)
                    for d in dstList:
                        try:
                            self.delFile(d, dirName, None, srcPath + dirName)
                        except Exception:
                            pass

    def _syncByTarget(self, srcPath, dstPath, spec, srcRootPath, dstRootPath, srcFiles, syncRule):
        """规则2/3：扫描目标目录对比。syncRule=2 对比大小+名称，syncRule=3 对比大小+名称+时间"""
        try:
            useCache = self.job['useCacheT']
            scanInterval = self.job['scanIntervalT']
            perPage = self.job.get('perPage', 200)
            dstFiles = self.alistClient.fileListApi(dstPath, useCache, scanInterval, spec, dstRootPath, perPage)
        except Exception:
            self.breakFlag = True
            self.allSrcScanned = False
            return
        needMkdir = True
        for key in srcFiles.keys():
            if self.breakFlag:
                return
            if not key.endswith('/'):
                if key not in dstFiles:
                    # 目标没有，复制
                    if needMkdir:
                        self.mkdir(dstPath)
                        needMkdir = False
                    self.copyFile(srcPath, dstPath, key, srcFiles[key][0])
                elif syncRule == 2:
                    # 规则2：只对比大小
                    if dstFiles[key][0] != srcFiles[key][0]:
                        if self.job.get('overwriteDelete', 0):
                            self.delFile(dstPath, key, srcFiles[key][0], srcPath + key, isOverwrite=True)
                        if needMkdir:
                            self.mkdir(dstPath)
                            needMkdir = False
                        self.copyFile(srcPath, dstPath, key, srcFiles[key][0])
                else:
                    # 规则3：对比大小+时间
                    if dstFiles[key] != srcFiles[key]:
                        if self.job.get('overwriteDelete', 0):
                            self.delFile(dstPath, key, srcFiles[key][0], srcPath + key, isOverwrite=True)
                        if needMkdir:
                            self.mkdir(dstPath)
                            needMkdir = False
                        self.copyFile(srcPath, dstPath, key, srcFiles[key][0])
            else:
                if key not in dstFiles:
                    self.syncWithOutHave(srcPath + key, dstPath + key, spec, srcRootPath, dstRootPath)
                else:
                    subSrcPath = srcPath + key
                    if subSrcPath not in self.preScannedSrc:
                        self.preScannedSrc[subSrcPath] = None
                    self.syncWithHave(subSrcPath, dstPath + key, spec, srcRootPath, dstRootPath)
        # 检测删除（仅全同步模式）
        if self.job['method'] == 1:
            for dstKey in dstFiles.keys():
                if dstKey not in srcFiles:
                    if dstKey.endswith('/'):
                        self.deletedDirs.add(srcPath + dstKey)
                        self.delFile(dstPath, dstKey, None, srcPath + dstKey)
                    else:
                        self.delFile(dstPath, dstKey, dstFiles[dstKey][0], srcPath + dstKey)

    def syncWithOutHave(self, srcPath, dstPath, spec, srcRootPath, dstRootPath):
        """
        扫描并同步-目标目录为空
        """
        if self.breakFlag:
            return
        self.mkdir(dstPath)
        # 优先使用预扫描缓存，避免重复调用目录列表接口
        cached = self.preScannedSrc.get(srcPath)
        if cached is not None:
            srcFiles = cached
        else:
            try:
                srcFiles = self.listDir(srcPath, spec, srcRootPath)
            except Exception:
                return
            self.preScannedSrc[srcPath] = srcFiles
        # 收集源端文件信息
        for key in srcFiles.keys():
            if not key.endswith('/'):
                relPath = srcPath + key
                self.scannedSrcFiles.append((relPath, srcFiles[key][0], srcFiles[key][1]))
        for key in srcFiles.keys():
            if self.breakFlag:
                break
            if key.endswith('/'):
                self.syncWithOutHave(srcPath + key, dstPath + key, spec, srcRootPath, dstRootPath)
            else:
                self.copyFile(srcPath, dstPath, key, srcFiles[key][0])

    def _markDirFilesFailed(self, srcPath, dstPath, spec, srcRootPath, errMsg):
        """目录创建失败，递归标记所有文件为失败"""
        if self.breakFlag:
            return
        # 优先使用预扫描缓存，避免重复调用目录列表接口
        cached = self.preScannedSrc.get(srcPath)
        if cached is not None:
            srcFiles = cached
        else:
            try:
                srcFiles = self.listDir(srcPath, spec, srcRootPath)
            except Exception:
                if self.breakFlag:
                    return
                return
            self.preScannedSrc[srcPath] = srcFiles
        for key in srcFiles.keys():
            if self.breakFlag:
                return
            if not key.endswith('/'):
                self.copyHook(srcPath, dstPath, key, srcFiles[key][0], status=7, errMsg=errMsg)
            else:
                self._markDirFilesFailed(srcPath + key, dstPath + key, spec, srcRootPath, errMsg)

    def _executePendingOps(self):
        """扫描完成后，统一执行所有待执行的操作"""
        self.scanPhase = False
        # 记录总文件数
        self.totalFiles = len(self.scannedSrcFiles)
        # 统计覆盖前删除数量
        self.overwriteDeleteCount = sum(1 for args in self.pendingDeletes if len(args) >= 5 and args[4])
        # mkdir 和 pre-delete 阶段进度跟踪
        self.mkdirTotal = len(self.pendingMkdirs)
        self.mkdirDone = 0
        self.preDeleteTotal = self.overwriteDeleteCount
        self.preDeleteDone = 0
        # 待执行文件数（只计算复制和全同步删除，不计算覆盖前删除）
        normalDeleteCount = len(self.pendingDeletes) - self.overwriteDeleteCount
        self.pendingFileCount = len(self.pendingCopies) + normalDeleteCount
        # 通知执行阶段开始（只有真正有待执行操作时才通知）
        hasOps = bool(self.pendingCopies or self.pendingDeletes)
        # 1. 执行所有mkdir（扫描阶段已去重）
        self.currentPhase = 'mkdir'
        mkdirTotal = self.mkdirTotal
        if mkdirTotal > 0 and not self.breakFlag:
            sse.notify_job_status(self.job['id'], 1, self.taskId, phase='mkdir',
                                  total_files=mkdirTotal, completed_files=0)
        for path in self.pendingMkdirs:
            if self.breakFlag:
                break
            try:
                self.alistClient.mkdir(path, self.job['scanIntervalT'])
            except Exception:
                pass
            self.mkdirDone += 1
            if self.mkdirDone % 10 == 0 or self.mkdirDone == mkdirTotal:
                sse.notify_job_status(self.job['id'], 1, self.taskId, phase='mkdir',
                                      total_files=mkdirTotal, completed_files=self.mkdirDone)
        self.pendingMkdirs.clear()
        self.pendingMkdirSet.clear()
        # 2. 执行所有删除操作（同目录批量删除）
        hasOverwriteDelete = False
        # 按目录分组
        deleteGroups = {}  # path -> [(fileName, size, srcPath, isOverwrite), ...]
        for args in self.pendingDeletes:
            path = args[0]
            fileName = args[1]
            size = args[2]
            srcPath = args[3]
            isOverwrite = args[4] if len(args) >= 5 else False
            if isOverwrite:
                hasOverwriteDelete = True
            if path not in deleteGroups:
                deleteGroups[path] = []
            deleteGroups[path].append((fileName, size, srcPath, isOverwrite))
        # 有覆盖前删除时推送 pre-delete 阶段
        self.currentPhase = 'pre-delete'
        if hasOverwriteDelete and not self.breakFlag:
            sse.notify_job_status(self.job['id'], 1, self.taskId, phase='pre-delete',
                                  total_files=self.overwriteDeleteCount, completed_files=0)
        # 批量删除
        # 批量删除
        for path, items in deleteGroups.items():
            if self.breakFlag:
                break
            names = []
            for item in items:
                fileName = item[0]
                isPath = fileName.endswith('/')
                names.append(fileName if not isPath else fileName[:-1])
            try:
                self.alistClient.checkWait(path, self.job['scanIntervalT'])
                self.alistClient.post('/api/fs/remove', data={'names': names, 'dir': path})
            except Exception as e:
                # 批量删除失败，逐个重试
                errMsg = str(e)
                if '990019' in errMsg:
                    for i in range(3):
                        if self.breakFlag:
                            break
                        time.sleep(3)
                        try:
                            self.alistClient.post('/api/fs/remove', data={'names': names, 'dir': path})
                            errMsg = None
                            break
                        except Exception as e2:
                            errMsg = str(e2)
                if errMsg:
                    # 逐个记录失败（仅非覆盖前删除）
                    for item in items:
                        fileName, size, srcPath, isOverwrite = item
                        if not isOverwrite:
                            self.delHook(path, fileName, size, 7, errMsg, fileName.endswith('/'), int(time.time()), srcPath)
            # 删除成功，记录到 finish（仅非覆盖前删除，覆盖前删除不影响缓存）
            for item in items:
                fileName, size, srcPath, isOverwrite = item
                if not isOverwrite:
                    self.finish.append({
                        'taskId': self.taskId,
                        'srcPath': srcPath,
                        'dstPath': path,
                        'isPath': 1 if fileName.endswith('/') else 0,
                        'fileName': fileName,
                        'fileSize': size,
                        'type': 1,
                        'alistTaskId': None,
                        'status': 2,
                        'errMsg': None,
                        'createTime': int(time.time())
                    })
            # 推送删除进度
            self.preDeleteDone += len(items)
            if hasOverwriteDelete and not self.breakFlag:
                sse.notify_job_status(self.job['id'], 1, self.taskId, phase='pre-delete',
                                      total_files=self.overwriteDeleteCount, completed_files=self.preDeleteDone)
        self.pendingDeletes.clear()
        # 删除后等待指定时间（仅覆盖前删除时等待，用于异步删除的网盘如115）
        deleteDelay = self.job.get('deleteDelay', 0)
        if hasOverwriteDelete and deleteDelay and deleteDelay > 0 and not self.breakFlag:
            time.sleep(deleteDelay)
        # 3. 进入执行阶段
        self.currentPhase = 'executing'
        if not self.breakFlag and self.pendingFileCount > 0:
            sse.notify_job_status(self.job['id'], 1, self.taskId, phase='executing',
                                  total_files=self.pendingFileCount, completed_files=0)
        elif not self.breakFlag:
            sse.notify_job_status(self.job['id'], 2, self.taskId, all_num=0)
        # 3. 再提交所有复制任务到队列
        for copyItem in self.pendingCopies:
            self.waiting.append(copyItem)
        self.pendingCopies.clear()
        # 4. 标记扫描完成之前，如果没有待执行的操作，主动写入缓存
        # 解决规则2/3扫描后文件相同不写缓存的问题
        if not self.breakFlag and self.job['method'] != 2 and not hasOps and self.scannedSrcFiles:
            jobMapper.addFileCacheMany(self.job['id'], self.scannedSrcFiles)
        # 5. 标记扫描完成
        self.scanFinish = True

    def updateTaskStatus(self):
        """
        所有任务完成后，最终更新任务状态
        """
        self.getCurrent()
        failOrOtherNum = len(self.currentTasks[7]) + len(self.currentTasks[-1])
        if self.breakFlag and not self.allSrcScanned:
            status = 8  # 扫描失败
        elif self.breakFlag:
            status = 7  # 人为中止
        else:
            status = 2 if failOrOtherNum == 0 else 3
        # 移动模式不写缓存
        if self.job['method'] != 2 and self.scanComplete:
            # 构建扫描结果的查找表（路径 → (大小, 修改时间)），用于获取真实修改时间
            scannedLookup = {item[0]: (item[1], item[2]) for item in self.scannedSrcFiles}
            # 多目标目录时，同一个源文件的所有目标操作都成功才更新缓存
            # 先按源文件分组，收集每个源文件的所有任务状态
            srcFileStatus = {}  # relPath/srcPath -> [status1, status2, ...]
            srcFileInfo = {}    # relPath/srcPath -> (fileSize, fileModified, copyType, fileName)
            for task in self.finish:
                copyType = task.get('type', 0)
                srcPath = task.get('srcPath')
                if not srcPath:
                    continue
                if copyType == 0:
                    fileName = task.get('fileName')
                    if not fileName:
                        continue
                    key = srcPath + fileName
                else:
                    key = srcPath
                if key not in srcFileStatus:
                    srcFileStatus[key] = []
                srcFileStatus[key].append(task.get('status', 7))
                # 保存文件信息（取成功的那条）
                if key not in srcFileInfo and task.get('status') == 2:
                    srcFileInfo[key] = task
            # 只有所有目标操作都成功才更新缓存
            for key, statuses in srcFileStatus.items():
                if all(s == 2 for s in statuses):
                    task = srcFileInfo.get(key)
                    if not task:
                        continue
                    copyType = task.get('type', 0)
                    try:
                        if copyType == 0:
                            # 复制/创建成功：写入缓存（用扫描到的真实修改时间）
                            scannedInfo = scannedLookup.get(key)
                            fileSize = scannedInfo[0] if scannedInfo else task.get('fileSize', 0)
                            fileModified = scannedInfo[1] if scannedInfo else 0
                            jobMapper.addFileCacheOne(self.job['id'], key, fileSize, fileModified)
                        elif copyType in (1, 2):
                            # 删除/移动成功：从缓存中移除
                            jobMapper.deleteFileCacheOne(self.job['id'], key)
                    except Exception as e:
                        logging.getLogger().warning(f"更新文件缓存失败: {e}")
        # 删除被删除目录下所有文件的缓存记录
        for dirPath in self.deletedDirs:
            try:
                jobMapper.deleteFileCacheByDir(self.job['id'], dirPath)
            except Exception as e:
                logging.getLogger().warning(f"删除目录缓存失败: {e}")
        # 删除失败的任务，把源路径加回缓存（下次重试删除）
        for task in self.currentTasks.get(7, []):
            if task.get('type') != 1 or not task.get('srcPath'):
                continue
            try:
                if task.get('isPath'):
                    # 目录：直接存目录路径，让规则1下次检测到并重试删除
                    jobMapper.addFileCacheOne(self.job['id'], task['srcPath'], 0, 0)
                else:
                    # 文件：直接写回
                    jobMapper.addFileCacheOne(self.job['id'], task['srcPath'], task.get('fileSize', 0), 0)
            except Exception as e:
                logging.getLogger().warning(f"加回删除失败缓存失败: {e}")
        taskService.updateJobTaskStatus(self.taskId, status, taskList=self.currentTasks, createTime=self.createTime)
        allNum = len(self.currentTasks.get(2, [])) + len(self.currentTasks.get(7, [])) + len(self.currentTasks.get(-1, []))
        sse.notify_job_status(self.job['id'], status, self.taskId, all_num=allNum)


class JobClient:
    def __init__(self, job, isInit=False):
        """
        初始化job
        :param job: {id(新增时不需要), enable, srcPath, dstPath, alistId, useCacheT, scanIntervalT, useCacheS, scanIntervalS, method, interval, exclude, cron相关}
        """
        addJobId = 0
        if 'enable' not in job:
            job['enable'] = 1
        if 'method' not in job:
            job['method'] = 0
        if 'id' not in job:
            addJobId = jobMapper.addJob(job)
            job = jobMapper.getJobById(addJobId)
        self.jobId = job['id']
        self.job = job
        self.scheduled = None
        self.scheduledJob = None
        self.jobDoing = False
        # 正在执行中的作业信息；仅在内存中，不入库，高速读写；执行完毕后批量入库，如果遇到异常终止，不会补偿入库
        # 单项结构 {
        #   'taskId':   所属任务id
        #   'alistTaskId': alist任务id
        #   'srcPath':  来源路径
        #   'dstPath':  目标路径
        #   'fileName': 文件名或者文件目录名
        #   'fileSize': 文件大小
        #   'status':   状态 0-等待中，1-运行中，2-成功，3-取消中，4-已取消，5-出错（将重试），
        #               6-失败中，7-已失败，8-等待重试中，9-等待重试回调执行中
        #   'progress': 进度
        #   'errMsg':   失败原因
        # }
        self.currentJobTask = None
        try:
            self.doByTime()
        except Exception as e:
            if isInit or addJobId != 0:
                # 仅在初始化和新增任务时删除错误的任务
                logger = logging.getLogger()
                logger.error(G('del_job_course_error').format(json.dumps(self.job)))
                jobMapper.deleteJob(self.jobId)
            raise e

    def doJob(self, force=False):
        """
        执行作业
        :param force: 是否强制执行（忽略禁用状态）
        :return:
        """
        while self.jobDoing:
            if self.job['enable'] == 0 and not force:
                return
            time.sleep(10)
        self.jobDoing = True
        taskId = None
        try:
            taskId = jobMapper.addJobTask({
                'jobId': self.jobId,
                'runTime': int(time.time())
            })
            if self.job['enable'] == 0 and not force:
                raise Exception("abort")
            self.currentJobTask = JobTask(taskId, self)
        except Exception as e:
            self.jobDoing = False
            logger = logging.getLogger()
            errMsg = G('do_job_err').format(str(e))
            logger.error(errMsg)
            if taskId is not None:
                taskService.updateJobTaskStatus(taskId, 6, errMsg)
                sse.notify_job_status(self.jobId, 6, taskId)
            logger.exception(e)

    def doManual(self):
        """
        手动执行作业
        :return:
        """
        if self.jobDoing:
            raise Exception(G('job_running'))
        doJobThread = threading.Thread(target=self.doJob, args=(True,))
        doJobThread.start()

    def doByTime(self):
        params = {
            'func': self.doJob,
            'misfire_grace_time': 15 * 60,
            'trigger': 'interval' if self.job['isCron'] == 0 else 'cron'
        }
        if self.job['isCron'] == 0:
            interval = self.job['interval']
            if interval is not None and str(interval).strip() != '':
                params['minutes'] = interval
            else:
                raise Exception(G('interval_lost'))
        elif self.job['isCron'] == 1:
            flag = 0
            for item in ['year', 'month', 'day', 'week', 'day_of_week', 'hour', 'minute', 'second', 'start_date',
                         'end_date']:
                if item in self.job and self.job[item] is not None and self.job[item] != '':
                    flag += 1
                    params[item] = self.job[item]
            if flag == 0:
                raise Exception(G('cron_lost'))
        else:
            return
        self.scheduled = BackgroundScheduler()
        self.scheduledJob = self.scheduled.add_job(**params)
        self.scheduled.start()
        if self.job['enable'] == 0:
            self.scheduledJob.pause()

    def resumeJob(self):
        """
        恢复作业
        :return:
        """
        if self.scheduledJob is None:
            raise Exception(G('cannot_resume_lost_job'))
        else:
            jobMapper.updateJobEnable(self.jobId, 1)
            self.job['enable'] = 1
            self.scheduledJob.resume()

    def updateJob(self, newJob):
        """
        更新作业配置（不影响正在执行的任务）
        :param newJob: 新的作业配置
        """
        # 定时任务配置字段
        cronFields = ['isCron', 'interval', 'year', 'month', 'day', 'week', 'day_of_week', 'hour', 'minute', 'second', 'start_date', 'end_date', 'enable']

        # 保存旧的定时任务配置
        oldCronConfig = {field: self.job.get(field) for field in cronFields}

        # 更新配置
        self.job = newJob

        # 检查定时任务配置是否有变化
        newCronConfig = {field: newJob.get(field) for field in cronFields}
        cronChanged = oldCronConfig != newCronConfig

        # 如果定时任务配置有变化，重建定时任务
        if cronChanged and self.scheduled is not None:
            # 停止旧的定时任务
            try:
                self.scheduled.shutdown(wait=False)
            except Exception as e:
                logger = logging.getLogger()
                logger.warning(G('stop_fail').format(str(e)))
                logger.exception(e)
            self.scheduled = None
            self.scheduledJob = None

            # 重建定时任务
            self.doByTime()
        elif cronChanged and self.scheduled is None and newJob.get('isCron') != 2:
            # 从手动执行变为定时执行，创建定时任务
            self.doByTime()
        elif not cronChanged and self.scheduledJob is not None:
            # 定时任务配置没有变化，但enable字段可能变化
            if oldCronConfig.get('enable') == 0 and newJob.get('enable') == 1:
                # 从禁用变为启用，恢复定时任务
                self.scheduledJob.resume()
            elif oldCronConfig.get('enable') == 1 and newJob.get('enable') == 0:
                # 从启用变为禁用，暂停定时任务
                self.scheduledJob.pause()

    def abortJob(self):
        """
        中止作业
        :return:
        """
        if self.currentJobTask:
            self.currentJobTask.breakFlag = True

    def stopJob(self, remove=False):
        """
        停止作业（适用于修改enable）
        :param remove: 是否删除作业，否一般用于禁用作业
        :return:
        """
        self.job['enable'] = 0
        if remove:
            # 删除作业时中止正在执行的任务
            if self.currentJobTask:
                self.currentJobTask.breakFlag = True
        if remove:
            if self.scheduled is not None:
                try:
                    self.scheduled.shutdown(wait=False)
                except Exception as e:
                    logger = logging.getLogger()
                    logger.warning(G('stop_fail').format(str(e)))
                    logger.exception(e)
                self.scheduled = None
        else:
            if self.scheduledJob is not None:
                try:
                    self.scheduledJob.pause()
                except Exception as e:
                    logger = logging.getLogger()
                    logger.warning(G('disable_fail').format(str(e)))
                    logger.exception(e)
        if remove:
            self.jobDoing = False
            jobMapper.updateJobEnable(self.jobId, 0)
            jobMapper.updateJobTaskStatusByStatusAndJobId(self.jobId)
        else:
            jobMapper.updateJobEnable(self.jobId, 0)
