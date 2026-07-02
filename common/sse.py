"""
SSE（Server-Sent Events）管理器
用于任务状态变化时主动推送给前端
"""
import json
import time
import threading
import logging

# 存储所有连接的客户端 {client_id: {queue, handler}}
_clients = {}
_lock = threading.Lock()
_client_counter = 0


def _next_client_id():
    global _client_counter
    _client_counter += 1
    return _client_counter


def register(handler):
    """注册一个 SSE 客户端，返回 client_id 和一个队列"""
    import queue
    q = queue.Queue()
    client_id = _next_client_id()
    with _lock:
        _clients[client_id] = {'queue': q, 'handler': handler}
    return client_id, q


def unregister(client_id):
    """注销一个 SSE 客户端"""
    with _lock:
        _clients.pop(client_id, None)


def broadcast(event_type, data):
    """
    向所有连接的客户端广播消息
    :param event_type: 事件类型，如 'task_status'
    :param data: dict 数据
    """
    msg = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    dead_clients = []
    with _lock:
        for client_id, info in _clients.items():
            try:
                info['queue'].put_nowait(msg)
            except Exception:
                dead_clients.append(client_id)
        for cid in dead_clients:
            _clients.pop(cid, None)


def notify_job_status(job_id, status, task_id=None, phase=None, all_num=None, total_files=None, completed_files=None, pending_files=None):
    """
    通知任务状态变化
    :param job_id: 作业ID
    :param status: 任务状态
    :param task_id: 任务记录ID（可选）
    :param phase: 执行阶段（可选）：scanning=扫描中, executing=执行中
    :param all_num: 总任务数（可选），用于前端判断"无需同步"
    :param total_files: 总文件数（可选），扫描阶段结束后推送
    :param completed_files: 已完成文件数（可选），执行阶段推送
    :param pending_files: 待执行文件数（可选）
    """
    data = {
        'jobId': job_id,
        'taskId': task_id,
        'status': status,
        'time': int(time.time() * 1000)
    }
    if phase:
        data['phase'] = phase
    if all_num is not None:
        data['allNum'] = all_num
    if total_files is not None:
        data['totalFiles'] = total_files
    if completed_files is not None:
        data['completedFiles'] = completed_files
    if pending_files is not None:
        data['pendingFiles'] = pending_files
    broadcast('task_status', data)
