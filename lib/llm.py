import os
import requests


class LLMError(Exception):
    pass


class OpenAICompatibleLLM:
    def __init__(self, config: dict):
        from openclaw_config import detect_openclaw_llm

        llm = config.get('llm', {})
        self.base_url = os.getenv(llm.get('base_url_env', 'DTFLOW_LLM_BASE_URL'), '').rstrip('/')
        self.api_key = os.getenv(llm.get('api_key_env', 'DTFLOW_LLM_API_KEY'), '')
        self.model = os.getenv(llm.get('model_env', 'DTFLOW_LLM_MODEL'), '')

        # Fallback: 自动从 OpenClaw 配置读取
        if not all([self.base_url, self.api_key, self.model]):
            oc = detect_openclaw_llm()
            if not self.base_url:
                self.base_url = oc.get('base_url', '')
            if not self.api_key:
                self.api_key = oc.get('api_key', '')
            if not self.model:
                self.model = oc.get('model', '')

    def validate(self):
        missing = []
        if not self.base_url:
            missing.append('base_url')
        if not self.api_key:
            missing.append('api_key')
        if not self.model:
            missing.append('model')
        if missing:
            raise LLMError(f'LLM 配置缺失: {", ".join(missing)}')

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 8192, temperature: float = 0.4):
        self.validate()
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': False,
        }
        response = requests.post(
            f'{self.base_url}/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=360,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get('choices')
        if not choices or not isinstance(choices, list):
            raise LLMError(f'LLM 返回数据中 choices 为空或不存在: {data!r}')
        return choices[0]['message']['content']
