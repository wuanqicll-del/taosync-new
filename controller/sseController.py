"""
SSE 控制器 - 提供 SSE 端点，认证通过后保持连接
"""
import json
import asyncio
import logging

from tornado.web import RequestHandler
from tornado.iostream import StreamClosedError

from common import sse
from common.LNG import G
from service.system import userService

cookieName = 'tao_sync'


class SSEHandler(RequestHandler):
    """SSE 事件流端点"""

    async def get(self):
        # 鉴权
        user_cookie = self.get_signed_cookie(cookieName)
        if not user_cookie:
            self.set_status(401)
            self.write('Unauthorized')
            return

        try:
            cUser = json.loads(user_cookie)
            trueUser = userService.getUser(cUser['id'], None)
            if ('passwd' not in cUser
                    or 'userName' not in cUser
                    or trueUser['passwd'] != cUser['passwd']
                    or trueUser['userName'] != cUser['userName']):
                self.set_status(401)
                self.write('Unauthorized')
                return
        except Exception:
            self.set_status(401)
            self.write('Unauthorized')
            return

        # 设置 SSE 响应头
        self.set_header('Content-Type', 'text/event-stream')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Connection', 'keep-alive')
        self.set_header('X-Accel-Buffering', 'no')
        self.set_header('Access-Control-Allow-Origin', '*')

        # 注册客户端
        client_id, q = sse.register(self)

        try:
            # 先发一个连接成功事件
            self.write(f"event: connected\ndata: {{}}\n\n")
            await self.flush()

            # 持续等待队列消息
            while True:
                try:
                    msg = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: q.get(timeout=30))
                    self.write(msg)
                    await self.flush()
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    try:
                        self.write(": heartbeat\n\n")
                        await self.flush()
                    except StreamClosedError:
                        break
                except StreamClosedError:
                    break
        except Exception as e:
            logging.getLogger().debug(f"SSE connection closed: {e}")
        finally:
            sse.unregister(client_id)
