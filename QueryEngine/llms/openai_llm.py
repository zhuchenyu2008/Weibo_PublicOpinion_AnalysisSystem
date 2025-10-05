"""
OpenAI LLM实现
使用OpenAI API进行文本生成
"""

import os
import sys
from typing import Optional, Dict, Any
from openai import OpenAI
from .base import BaseLLM

# 添加utils目录到Python路径并导入重试模块
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    utils_dir = os.path.join(root_dir, 'utils')
    if utils_dir not in sys.path:
        sys.path.append(utils_dir)
    from retry_helper import with_retry, with_graceful_retry, LLM_RETRY_CONFIG
except ImportError:
    # 如果无法导入重试模块，使用空装饰器避免报错
    def with_retry(config):
        def decorator(func):
            return func
        return decorator
    LLM_RETRY_CONFIG = None


class OpenAILLM(BaseLLM):
    """OpenAI LLM实现类"""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, api_base: Optional[str] = None):
        """
        初始化OpenAI客户端

        Args:
            api_key: OpenAI API密钥，如果不提供则从环境变量读取
            model_name: 模型名称，默认使用gpt-4o-mini
        """
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API Key未找到！请设置OPENAI_API_KEY环境变量或在初始化时提供")

        base_url = api_base or os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1"

        super().__init__(api_key, model_name, base_url)

        # 初始化OpenAI客户端
        client_kwargs = {"api_key": self.api_key}
        if self.api_base:
            client_kwargs["base_url"] = self.api_base
        self.client = OpenAI(**client_kwargs)
        self.default_model = model_name or self.get_default_model()
    
    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return "gpt-4o-mini"
    
    @with_retry(LLM_RETRY_CONFIG)
    def invoke(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """
        调用OpenAI API生成回复
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户输入
            **kwargs: 其他参数，如temperature、max_tokens等
            
        Returns:
            OpenAI生成的回复文本
        """
        try:
            # 构建消息
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 设置默认参数
            params = {
                "model": self.default_model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 8192)  # 提高到30000以支持一万字报告
            }
            
            # 调用API
            response = self.client.chat.completions.create(**params)
            
            # 提取回复内容
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                return self.validate_response(content)
            else:
                return ""
                
        except Exception as e:
            print(f"OpenAI API调用错误: {str(e)}")
            raise e
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取当前模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "provider": "OpenAI",
            "model": self.default_model,
            "api_base": self.api_base
        }
