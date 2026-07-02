# TaoSync - 文件同步工具

基于 Alist API 的文件同步工具，支持多源多目标目录、多种同步模式、定时任务、实时进度监控。

## 功能特点

- **多种同步模式**
  - 仅新增：只复制目标没有的文件
  - 全同步：复制变化文件 + 删除目标多余文件
  - 移动模式：复制后删除源文件

- **灵活的目录配置**
  - 支持多个源目录
  - 支持多个目标目录
  - 支持子目录过滤

- **智能过滤规则**
  - 文件名通配符过滤（支持 Gitignore 语法）
  - 文件大小过滤
  - 文件时间过滤

- **实时进度监控**
  - SSE 实时推送进度
  - 阶段化进度显示（扫描/创建目录/删除/同步）

- **定时任务**
  - 支持 Cron 表达式定时执行
  - 支持手动触发

- **通知功能**
  - 支持 ntfy 推送通知
  - 同步完成/失败通知

## 快速开始

### 使用 Docker（推荐）

```bash
# 创建数据目录
mkdir -p /path/to/data

# 运行容器
docker run -d \
  --name taosync \
  -p 8023:8023 \
  -v /path/to/data:/app/data \
  --restart unless-stopped \
  wuanqicll-del/taosync-new:latest
```

### 使用 Docker Compose

创建 `docker-compose.yml`：

```yaml
services:
  taosync:
    image: wuanqicll-del/taosync-new:latest
    container_name: taosync
    ports:
      - "8023:8023"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

启动服务：

```bash
docker-compose up -d
```

## 访问 WebUI

打开浏览器访问：`http://你的IP:8023`

默认登录信息：
- 用户名：`admin`
- 密码：`admin`

**首次登录后请立即修改密码！**

## 配置说明

### Alist 配置

在 WebUI 中添加 Alist 服务器：
- 服务器地址：你的 Alist 服务地址
- 令牌：Alist 的访问令牌

### 同步任务配置

1. **源目录配置**
   - 选择 Alist 服务器
   - 选择源目录路径
   - 可添加多个源目录

2. **目标目录配置**
   - 选择目标目录路径
   - 可添加多个目标目录

3. **同步模式**
   - 仅新增：只复制新文件
   - 全同步：同步所有变化
   - 移动模式：复制后删除源文件

4. **过滤规则**
   - 文件名过滤：支持通配符（如 `*.mp4`、`*.mkv`）
   - 文件大小过滤：最小/最大文件大小
   - 文件时间过滤：只同步指定时间后的文件

5. **定时执行**
   - 支持 Cron 表达式
   - 示例：`0 2 * * *`（每天凌晨2点执行）

## 技术栈

- **后端**
  - Python 3.11
  - Tornado Web 框架
  - SQLite 数据库
  - APScheduler 定时任务

- **前端**
  - Vue.js 2
  - Element UI
  - Vuex 状态管理
  - Vue Router 路由管理

- **部署**
  - Docker 容器化
  - 多架构支持（AMD64/ARM64）

## 目录结构

```
taosync/
├── common/          # 公共工具类
├── controller/      # API 控制器
├── frontend/        # 前端源码
├── mapper/          # 数据库映射
├── service/         # 业务逻辑
│   ├── alist/       # Alist API 服务
│   ├── notify/      # 通知服务
│   ├── syncJob/     # 同步任务服务
│   └── system/      # 系统服务
├── main.py          # 主入口
├── Dockerfile       # Docker 构建文件
└── requirements.txt # Python 依赖
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `PORT` | 服务端口 | `8023` |
| `DATA_DIR` | 数据目录 | `/app/data` |

## 常见问题

### 1. 如何更新版本？

```bash
# 拉取最新镜像
docker pull wuanqicll-del/taosync-new:latest

# 重启容器
docker-compose down
docker-compose up -d
```

### 2. 如何备份数据？

数据存储在 `/app/data` 目录下的 SQLite 数据库中，备份该目录即可。

### 3. 支持哪些 Alist 版本？

支持 Alist V2 和 V3 版本。

## 许可证

MIT License

## 项目地址

- GitHub：https://github.com/wuanqicll-del/taosync-new
- DockerHub：https://hub.docker.com/r/wuanqicll-del/taosync-new
