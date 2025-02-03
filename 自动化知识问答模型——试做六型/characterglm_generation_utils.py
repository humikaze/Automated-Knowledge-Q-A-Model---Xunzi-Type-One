import torch
from typing import TypedDict, Literal, List, Optional, Tuple, Iterator
import sys
import os
import warnings
from contextlib import redirect_stdout, redirect_stderr

# 禁用所有警告信息
warnings.filterwarnings("ignore")

# 重定向标准输出和错误输出到 null 设备（完全静默）
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

#### data types #########
# 下面的数据类型定义与CharacterGLM API一致，但与modeling_chatglm.py的chat方法不一致
# 参考 https://open.bigmodel.cn/dev/api#characterglm
RoleType = Literal["user", "assistant"]


class Msg(TypedDict):
    role: RoleType
    content: str


class SessionMeta(TypedDict):
    user_name: str
    bot_name: str
    bot_info: str
    user_info: Optional[str]


HistoryType = List[Msg]


class CharacterGLMGenerationUtils:
    @staticmethod
    def convert_chatglm_history_to_characterglm_history(user_query: str, history: List[Tuple[str, str]]) -> HistoryType:
        characterglm_history: HistoryType = []
        for i, (query, response) in enumerate(history):
            if i == 0 and query == '':
                # first empty query is an placeholder
                pass
            else:
                characterglm_history.append({
                    "role": "user",
                    "content": query
                })
            characterglm_history.append({
                "role": "assistant",
                "content": response
            })

        characterglm_history.append({
            "role": "user",
            "content": user_query
        })
        return characterglm_history

    @staticmethod
    def build_inputs(session_meta: SessionMeta, history: HistoryType) -> str:
        """
        注意：这里假设history最后一条消息是用户query
        """
        texts = []
        texts.append(
            f"以下是一段{session_meta['bot_name']}和{session_meta['user_name']}之间的对话。")
        if session_meta.get("bot_info"):
            texts.append(f"关于{session_meta['bot_name']}的信息：{session_meta['bot_info']}")
        if session_meta.get("user_info"):
            texts.append(
                f"关于{session_meta['user_name']}的信息：{session_meta['user_info']}")

        assert history and history[-1]['role'] == 'user'
        for msg in history:
            name = session_meta['user_name'] if msg['role'] == 'user' else session_meta['bot_name']
            texts.append(f"[{name}]" + msg['content'].strip())

        texts = [text.replace('\n', ' ') for text in texts]
        texts.append(f"[{session_meta['bot_name']}]")
        return '\n'.join(texts)


class CharacterGLMAPI:
    @staticmethod
    def build_api_arguments(session_meta: SessionMeta, history: HistoryType) -> dict:
        return {
            "model": "characterglm",
            "meta": session_meta,
            "prompt": history
        }

    @classmethod
    def async_invoke(cls, session_meta: SessionMeta, history: HistoryType):
        """
        注意：
        1. 先设置zhipuai.api_key
        2. 建议传入`return_type='text'`，否则返回结果是json字符串

        参考：
            https://open.bigmodel.cn/dev/api#characterglm
        """
        import zhipuai
        kwargs = cls.build_api_arguments(session_meta, history)
        return zhipuai.model_api.async_invoke(**kwargs, return_type='text')

    @classmethod
    def invoke(cls, session_meta: SessionMeta, history: HistoryType):
        """
        注意：
        1. 先设置zhipuai.api_key
        2. 建议传入`return_type='text'`，否则返回结果是json字符串
        3. 需要再次调用`zhipuai.model_api.query_async_invoke_result`才能获取生成结果

        参考：
            https://open.bigmodel.cn/dev/api#characterglm
        """
        import zhipuai
        kwargs = cls.build_api_arguments(session_meta, history)
        return zhipuai.model_api.invoke(**kwargs, return_type='text')

    @classmethod
    def generate(cls, session_meta: SessionMeta, history: HistoryType) -> str:
        result = cls.invoke(session_meta, history)
        if not result['success']:
            raise RuntimeError(result)
        return result['data']['choices'][0]['content']

    @classmethod
    def stream_generate(cls, session_meta: SessionMeta, history: HistoryType) -> Iterator[str]:
        # 伪流式生成
        return iter(cls.generate(session_meta, history))
