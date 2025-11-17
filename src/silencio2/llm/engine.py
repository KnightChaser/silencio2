# src/silencio2/llm/engine.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Any

try:
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
except ImportError as e:
    raise RuntimeError(
        "vLLM and transformers must be installed to use silencio2.llm.\n"
        "Example:\n"
        "  uv pip install vllm --torch-backend=auto transformers"
    ) from e

Role = Literal["system", "user", "assistant"]

@dataclass
class ChatMessage:
    role: Role
    content: str

@dataclass
class Qwen3Config:
    """
    Configuration for the local Qwen3 model.

    Adjust fields as needed for your hardware / deployment.
    """
    model_name: str = "Qwen/Qwen3-4B-Instruct-2507"
    max_model_len: int = 32768
    temperature: float = 0.3        # lower for more deterministic badges
    top_p: float = 0.9
    max_tokens: int = 1024          # enough for badge lines

@dataclass
class Qwen3ChatEngine:
    """
    Thin wrapper around vLLM + Qwen3 for silencio2.

    It exposes a single `chat` method that takes a list of ChatMessage and
    returns the assistant text reply.
    """
    config: Qwen3Config = field(default_factory=Qwen3Config)
    _llm: LLM | None = field(init=False, default=None)
    _tokenizer: Any | None = field(init=False, default=None)

    def __post_init__(self):
        self._llm = LLM(
            model=self.config.model_name,
            trust_remote_code=True,
            max_model_len=self.config.max_model_len,
        )
        self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)

    def _build_prompt(self, messages: List[ChatMessage]) -> str:
        """
        Build a chat prompt string using the model's chat template.

        Args:
            messages (List[ChatMessage]): List of chat messages.

        Returns:
            str: Formatted prompt string.
        """
        if self._tokenizer is None:
            raise RuntimeError("Tokenizer not initialized.")

        hf_messages = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]

        prompt = self._tokenizer.apply_chat_template(
            hf_messages,
            # tokenizer=self._tokenizer,

            # NOTE:
            # Make sure we get a string, not token IDs -- vLLM expects a string prompt.
            tokenize=False,
            add_generation_prompt=True,
        )
        return prompt

    def chat(
        self,
        messages: List[ChatMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Generate a chat response from the model.

        Args:
            messages (List[ChatMessage]): List of chat messages.
            temperature (float | None): Sampling temperature. If None, uses config value.
            max_tokens (int | None): Maximum tokens to generate. If None, uses config value.

        Returns:
            str: Generated assistant response.
        """
        if self._llm is None:
            raise RuntimeError("LLM not initialized.")

        sampling_params = SamplingParams(
            temperature=temperature if temperature is not None else self.config.temperature,
            top_p=self.config.top_p,
            max_tokens=max_tokens if max_tokens is not None else self.config.max_tokens,
        )

        prompt = self._build_prompt(messages)
        outputs = self._llm.generate(
            [prompt],
            sampling_params=sampling_params,
            use_tqdm=False, # WARNING: disable vLLM's own progress bar to avoid ZeroDivisionError
        )

        output = outputs[0]
        text = output.outputs[0].text.strip()
        return text
