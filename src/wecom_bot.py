import requests
import json
import logging

logger = logging.getLogger(__name__)


class WeChatWorkBot:
    def __init__(self, webhook_url):
        if not webhook_url:
            logger.error("Webhook URL不能为空")
            raise ValueError("Webhook URL不能为空")

        self.webhook_url = webhook_url
        logger.info("企业微信机器人初始化成功")

    def truncate_text(self, text, max_length=4000):  # 增加最大长度限制
        """截断文本"""
        if not text:
            return ""
        return text[:max_length] + '...' if len(text) > max_length else text

    def send_text_notice_card(self, main_title, sub_title_text, source_name=None, url=None):
        """发送文本通知模版卡片"""
        try:
            main_title = main_title or "无标题新闻"
            sub_title_text = sub_title_text or "暂无详细内容"

            payload = {
                "msgtype": "template_card",
                "template_card": {
                    "card_type": "text_notice",
                    "main_title": {
                        "title": main_title,
                        "desc": source_name
                    },
                    "sub_title_text": self.truncate_text(sub_title_text, 4000),  # 正文内容
                    "card_action": {
                        "type": 1,
                        "url": url or self.webhook_url
                    }
                }
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            result = response.json()

            if result.get('errcode') == 0:
                logger.info(f"消息发送成功：{main_title}")
            else:
                logger.error(f"消息发送失败：{result}")

            return result

        except requests.Timeout:
            logger.error("发送消息超时")
            raise
        except requests.RequestException as e:
            logger.error(f"发送消息网络错误: {e}")
            raise
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            raise