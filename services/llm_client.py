import requests
import json
import time
from config import settings
from utils.logger import logger

class LLMClient:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = settings.AI_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def analyze(self, prompt):
        """
        调用 DeepSeek API 进行分析
        
        Args:
            prompt (str): 构建好的提示词
            
        Returns:
            dict: 解析后的 JSON 结果
        """
        if not self.api_key or "sk-your-key-here" in self.api_key:
            logger.warning("未配置有效的 DeepSeek API Key，无法进行 AI 分析。")
            return None

        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1, # 低温以保证 JSON 格式稳定
            "stream": False
        }

        try:
            logger.info("正在调用 DeepSeek API ...")
            start_time = time.time()
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            logger.info(f"AI 响应成功 (耗时 {time.time() - start_time:.2f}s)")
            
            # 尝试解析 JSON
            try:
                # 有时候模型会包裹 markdown 代码块，需要去除
                clean_content = content.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean_content)
                return result
            except json.JSONDecodeError:
                logger.error("AI 返回的内容不是有效的 JSON")
                logger.debug(f"Raw content: {content}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API 请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return None
