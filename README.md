# AI 视频工作流

这是一个本地文件驱动的 AI 视频生成工作台。

当前技术栈：

- 前端：Vue 3 + Vite + Element Plus
- 后端：FastAPI
- 存储：仅本地文件，不使用数据库

## 快速入口

- 使用说明：[docs/operation-guide.md](docs/operation-guide.md)
- 本地存储规范：[docs/local-storage-spec.md](docs/local-storage-spec.md)
- 后端说明：[code/backEnd/README.md](code/backEnd/README.md)
- 前端说明：[code/frontEnd/README.md](code/frontEnd/README.md)

## 启动

直接使用根目录脚本：

- `start.bat`
- `restart.bat`
- `stop.bat`

默认地址：

- 前端：`http://127.0.0.1:8080`
- 后端：`http://127.0.0.1:8000`

## 当前核心能力

- 系列管理
- 剧集管理
- 原始剧本录入
- AI 拆解剧本
- 可读视图编辑场景与分镜
- 角色创建、参考图上传、角色圣经拼图生成
- 场景创建、场景参考拼图生成
- 分镜板管理
- 两种生产模式
  - `分镜生产`
  - `场景直出`
- 镜头包 / 场景包组装
- 快照落盘
- Seedance 提交草稿生成
- 单任务提交与刷新
- 批量镜头任务提交与刷新
- 远端任务查询与取消

## 当前推荐工作流

1. 创建系列
2. 创建剧集并录入原始剧本
3. AI 拆解剧本
4. 修正可读视图中的场景和分镜
5. 创建角色并生成角色圣经拼图
6. 创建场景并生成场景参考拼图
7. 创建分镜板并选择生产模式
8. 生成镜头包 / 场景包
9. 生成快照
10. 生成 Seedance 提交草稿
11. 提交任务并刷新远端状态

详细操作见：

- [docs/operation-guide.md](docs/operation-guide.md)

## 目录说明

```text
output/              所有本地业务数据与生成结果
code/frontEnd/       前端项目
code/backEnd/        后端项目
docs/                项目文档
```
