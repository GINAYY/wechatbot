from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.tmt.v20180321 import tmt_client, models
import logging

logger = logging.getLogger(__name__)


class TencentTranslator:
    def __init__(self, secret_id: str, secret_key: str, region: str = 'ap-beijing'):
        try:
            cred = credential.Credential(secret_id, secret_key)
            httpProfile = HttpProfile()
            httpProfile.endpoint = "tmt.tencentcloudapi.com"

            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile

            self.client = tmt_client.TmtClient(cred, region, clientProfile)
            logger.info("翻译客户端初始化成功")

        except Exception as e:
            logger.error(f"翻译客户端初始化失败: {e}")
            raise

    def translate_text(self, text: str, source_lang: str = 'auto', target_lang: str = 'zh') -> str:
        """翻译文本"""
        if not text.strip():
            return text

        try:
            req = models.TextTranslateRequest()
            req.SourceText = text
            req.Source = source_lang
            req.Target = target_lang
            req.ProjectId = 0

            resp = self.client.TextTranslate(req)
            return resp.TargetText

        except Exception as e:
            logger.error(f"翻译失败: {e}")
            return text  # 翻译失败时返回原文