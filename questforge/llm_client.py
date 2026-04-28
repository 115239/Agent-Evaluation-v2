"""DeepSeek OpenAI 兼容 LLM 客户端。

设计要点：
- 延迟导入 openai：USE_LLM=False 时不触发依赖
- 强制 JSON 输出：失败 N 次回退到空 dict，上层走 offline fallback
- 参考 datasets/test_agent_2/0311构建.py 的调用风格
"""
from __future__ import annotations

import json
import logging
import random
import re
import time
from typing import Any

from . import config

log = logging.getLogger("questforge.llm")


class LLMClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        use_llm: bool | None = None,
    ) -> None:
        self.base_url = base_url or config.LLM_BASE_URL
        self.api_key = api_key or config.LLM_API_KEY
        self.model = model or config.LLM_MODEL
        self.use_llm = config.USE_LLM if use_llm is None else use_llm
        self._client = None

    # ---------- 初始化 ----------
    def _ensure_client(self):
        if self._client is not None:
            return self._client
        if not self.use_llm:
            return None
        if not self.api_key:
            log.warning("LLM_API_KEY 未配置，自动切换到 offline 模式")
            self.use_llm = False
            return None
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            log.warning("openai SDK 不可用（%s），切到 offline 模式", e)
            self.use_llm = False
            return None
        self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        return self._client

    # ---------- 主入口 ----------
    def chat_text(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """普通文本对话，返回 content。失败则返回空串。"""
        client = self._ensure_client()
        if client is None:
            return ""

        temperature = config.LLM_TEMPERATURE if temperature is None else temperature
        max_tokens = config.LLM_MAX_TOKENS if max_tokens is None else max_tokens

        for attempt in range(config.LLM_MAX_RETRY + 1):
            try:
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                )
                return (resp.choices[0].message.content or "").strip()
            except Exception as e:  # pragma: no cover
                log.warning("LLM 调用失败（第 %d/%d 次）：%s", attempt + 1, config.LLM_MAX_RETRY, e)
                time.sleep(config.LLM_RETRY_SLEEP + random.uniform(0, 0.5))
        return ""

    def chat_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """要求 LLM 输出 JSON，解析失败返回 {}"""
        raw = self.chat_text(
            system + "\n\n请仅输出合法 JSON，不含任何解释、注释或 markdown 代码围栏。",
            user,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not raw:
            return {}
        return _safe_parse_json(raw)


# ========== 工具函数 ==========
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _safe_parse_json(text: str) -> dict[str, Any]:
    """容错解析 LLM 可能带上的 markdown 围栏/前后废话。"""
    text = _CODE_FENCE_RE.sub("", text.strip())
    # 粗略找最外层 JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as e:
            log.warning("LLM 返回无法解析为 JSON：%s | raw=%s", e, text[:200])
    return {}


_SINGLETON: LLMClient | None = None


def get_default_client() -> LLMClient:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = LLMClient()
    return _SINGLETON
