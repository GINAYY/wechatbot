import yaml
import time
import logging
import sys
import os
from typing import List, Dict
from datetime import datetime, timedelta

from rss_parser import RSSParser
from translator import TencentTranslator
from wecom_bot import WeChatWorkBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class RSSNotificationBot:
    def __init__(self, config_path=None):
        try:
            # 自动查找配置文件
            if config_path is None:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                possible_paths = [
                    os.path.join(current_dir, '..', 'config', 'config.local.yaml'),  # 优先加载本地配置
                    os.path.join(current_dir, 'config', 'config.local.yaml'),
                    os.path.join(current_dir, '..', 'config', 'config.yaml'),
                    os.path.join(current_dir, 'config', 'config.yaml'),
                    'config/config.local.yaml',
                    'config/config.yaml'
                ]

                for path in possible_paths:
                    if os.path.exists(path):
                        config_path = path
                        break

                if config_path is None:
                    raise FileNotFoundError("无法找到配置文件")

            logger.info(f"使用配置文件: {config_path}")

            # 加载配置
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            logger.info("配置加载成功")

            # 验证配置
            if not self.config.get('rss_sources'):
                raise ValueError("配置文件中缺少 RSS 源配置")

            if not self.config.get('tencent_translate'):
                raise ValueError("配置文件中缺少腾讯翻译配置")

            if not self.config.get('wecom_bot'):
                raise ValueError("配置文件中缺少企业微信机器人配置")

            # 初始化翻译器和机器人
            self.translator = TencentTranslator(
                self.config['tencent_translate']['secret_id'],
                self.config['tencent_translate']['secret_key'],
                self.config['tencent_translate']['region']
            )
            self.wecom_bot = WeChatWorkBot(
                self.config['wecom_bot']['webhook_url']
            )

            # 初始化状态追踪
            self.processed_entries = set()
            self.last_source_update = {}
            self.last_message_time = datetime.now()

            logger.info("RSS机器人初始化完成")

        except FileNotFoundError as e:
            logger.error(f"配置文件不存在: {e}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise

    def is_recent_entry(self, entry, max_hours=24):
        """检查条目是否为近期条目"""
        try:
            return True  # 暂时返回True，因为时间解析有问题
        except Exception as e:
            logger.warning(f"时间解析失败，默认为近期条目: {e}")
            return True

    def process_single_source(self, rss_url: str, source_name: str):
        """处理单个RSS源"""
        try:
            rss_parser = RSSParser(rss_url)
            entries = rss_parser.parse_feed()

            if not entries:
                logger.warning(f"RSS源 {source_name} 没有获取到任何条目")
                return

            logger.info(f"获取到 {len(entries)} 条新闻")

            # 按发布时间排序（如果可能的话）
            entries.reverse()  # 假设entries是按时间倒序的

            for entry in entries:
                # 检查是否需要等待发送下一条消息
                current_time = datetime.now()
                if (current_time - self.last_message_time).total_seconds() < 60:  # 每分钟最多发送一条
                    time_to_wait = 60 - (current_time - self.last_message_time).total_seconds()
                    if time_to_wait > 0:
                        time.sleep(time_to_wait)

                try:
                    if not self.is_recent_entry(entry):
                        continue

                    entry_hash = hash(entry['title'] + entry['link'])
                    if entry_hash in self.processed_entries:
                        continue

                    # 翻译处理
                    try:
                        translated_title = self.translator.translate_text(entry['title'])
                        time.sleep(0.5)  # 在两次翻译请求之间添加延迟
                        translated_summary = self.translator.translate_text(entry['summary'])
                    except Exception as e:
                        logger.error(f"翻译失败: {e}")
                        translated_title = entry['title']
                        translated_summary = entry['summary']

                    # 发送消息
                    try:
                        self.wecom_bot.send_text_notice_card(
                            main_title=translated_title,
                            sub_title_text=translated_summary,
                            source_name=source_name,
                            url=entry['link']
                        )
                        logger.info(f"消息发送成功: {translated_title}")
                        self.last_message_time = datetime.now()
                    except Exception as e:
                        logger.error(f"发送消息失败: {e}")
                        continue

                    self.processed_entries.add(entry_hash)

                except Exception as e:
                    logger.error(f"处理单条新闻失败: {e}")
                    continue

            # 清理过多的处理记录
            if len(self.processed_entries) > 1000:
                logger.info("清理历史记录")
                self.processed_entries.clear()

        except Exception as e:
            logger.error(f"处理RSS源失败: {e}")
            raise

    def process_rss_sources(self):
        """处理所有RSS源"""
        current_time = datetime.now()
        for source in self.config['rss_sources']:
            source_name = source['name']

            # 每10分钟检查一次RSS源
            if (source_name not in self.last_source_update or
                    current_time - self.last_source_update.get(source_name, datetime.min) >= timedelta(minutes=10)):

                try:
                    logger.info(f"开始处理RSS源: {source_name}")
                    self.process_single_source(source['url'], source_name)
                    self.last_source_update[source_name] = current_time
                    logger.info(f"RSS源处理完成: {source_name}")
                except Exception as e:
                    logger.error(f"处理RSS源 {source_name} 失败: {str(e)}")

    def run(self, interval=600):  # 10分钟检查一次RSS源
        """持续运行RSS监控"""
        logger.info("RSS监控机器人启动")
        while True:
            try:
                self.process_rss_sources()
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("收到退出信号，程序终止")
                break
            except Exception as e:
                logger.error(f"运行出错: {e}")
                time.sleep(interval)

        logger.info("RSS监控机器人已停止")


def main():
    try:
        logger.info("开始启动 RSS 监控机器人...")
        bot = RSSNotificationBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("收到停止信号，程序终止")
    except Exception as e:
        logger.error(f"程序出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
