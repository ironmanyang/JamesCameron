# AI 视频工作流

本项目是一个纯本地文件驱动的 AI 视频生成工作台。

当前技术栈：

- 前端：Vue 3 + Vite + Element Plus
- 后端：FastAPI
- 存储：仅本地文件，不使用数据库

## 快速入口

- 使用说明：[docs/operation-guide.md](docs/operation-guide.md)
- 本地存储规范：[docs/local-storage-spec.md](docs/local-storage-spec.md)

## 启动

直接使用根目录脚本：

- `start.bat`
- `restart.bat`
- `stop.bat`

默认地址：

- 前端：`http://127.0.0.1:8080`
- 后端：`http://127.0.0.1:8000`

## 当前已实现

- 系列管理
- 剧集管理
- 剧本拆解
- 角色创建与参考图上传
- 角色圣经拼图生成
- 场景创建
- 场景参考拼图生成
- 分镜卡创建
- 镜头包组装
- 任务草稿落盘

## 目录说明

```text
output/              所有生成内容与本地数据
code/frontEnd/       前端项目
code/backEnd/        后端项目
docs/                项目文档
```
