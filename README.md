# RSS 企业微信机器人通知系统

## 项目描述
从指定RSS源获取新闻，并通过腾讯云翻译自动翻译内容，然后推送到企业微信机器人群聊的自动化系统。

## 功能特点
- 支持多个RSS源订阅
- 自动翻译英文内容为中文
- 实时推送到企业微信机器人
- 防重复推送机制

## 环境准备
1. Python 3.8+
2. 安装依赖: `pip install -r requirements.txt`

## 配置说明
在 `config/config.yaml` 中配置:
- RSS源
- 腾讯云翻译API凭证
- 企业微信机器人Webhook

## 使用方法
```
bash
pip install -r requirements.txt
```

- 创建虚拟环境（推荐）
### 在项目根目录
- python -m venv venv
### Windows激活虚拟环境
venv\Scripts\activate
### Mac/Linux
source venv/bin/activate

- python src/main.py


## 部署
使用CODING CI/CD持续集成平台定期执行脚本。