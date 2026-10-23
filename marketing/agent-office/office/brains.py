"""The AI each desk thinks with.

Every brain answers the same call: a task, the day's context and a pydantic schema in, a validated object out.

- claude-code: Claude Code in print mode (`claude -p --output-format json --json-schema …`), on your Claude login.
- codex:       Codex non-interactive mode (`codex exec - --output-schema …`), on your ChatGPT login; also makes
               cover illustrations with its built-in image generation.
- antigravity: Antigravity's CLI in headless mode. Its flags still move between releases, so the command is
               configurable (OFFICE_ANTIGRAVITY_COMMAND) and the answer is read leniently from stdout.
- api:         the Claude API through the Anthropic SDK (needs ANTHROPIC_API_KEY or an `ant auth login` profile).

The CLIs run in an empty temporary folder with no write access (except Codex while it saves an image), so they can
think and search but not touch the office's files.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .brand import VOICE_GUIDE
from .config import Settings

Model = TypeVar("Model", bound=BaseModel)

FALLBACK_BETA = "server-side-fallback-2026-07-01"
LABELS = {
    "claude-code": "Claude Code",
    "codex": "Codex",
    "antigravity": "Antigravity",
    "api": "Claude API",
    "offline": "離線範本",
}
# What each role is for, as shown in the office. A role is a desk, except Ivy, who researches and then plans; the
# chief is the desk you talk to, which passes your requests on to everyone else.
ROLES = {
    "chief": "總管",
    "research": "查資料",
    "strategist": "企劃",
    "threads": "Threads 文案",
    "designer": "IG 文案",
    "video": "影片腳本",
    "reviewer": "審稿",
    "community": "留言回覆",
    "publisher": "發文前檢查",
    "analyst": "數據解讀",
}


class BrainError(RuntimeError):
    pass


def has_claude_api_credentials() -> bool:
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_PROFILE"):
        return True
    config_home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return (config_home / "anthropic").is_dir()


def resolve(spec: str, role: str) -> str:
    """Brain key for one role from OFFICE_BRAINS ("codex" or "threads=claude-code,reviewer=codex")."""
    default = "auto"
    chosen = None
    for part in (p.strip() for p in spec.split(",") if p.strip()):
        if "=" in part:
            name, _, brain = part.partition("=")
            if name.strip() == role:
                chosen = brain.strip()
            elif name.strip() == "*":
                default = brain.strip()
        else:
            default = part
    key = chosen or default
    if key == "auto":
        return "api" if has_claude_api_credentials() else "offline"
    if key not in LABELS:
        raise ValueError(f"OFFICE_BRAINS 裡的「{key}」不是可用的大腦（{'、'.join(LABELS)}）")
    return key


def chain(settings: Settings, role: str) -> list[str]:
    keys = [resolve(settings.brains, role)]
    for key in settings.brain_fallback:
        if key not in keys and key in LABELS:
            keys.append(key)
    return keys


def strict_schema(schema: type[BaseModel]) -> dict:
    """OpenAI-style strict schema for Codex: every property required, no extra keys, no defaults."""

    def walk(node):
        if isinstance(node, dict):
            node = {k: walk(v) for k, v in node.items() if k != "default"}
            if node.get("type") == "object" and "properties" in node:
                node["required"] = list(node["properties"])
                node["additionalProperties"] = False
            return node
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(schema.model_json_schema())


def parse_json_text(text: str) -> dict:
    """The first JSON object in free text (fenced or not)."""
    start = text.find("{")
    while start != -1:
        depth, in_string, escape = 0, False, False
        for index in range(start, len(text)):
            ch = text[index]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            elif ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : index + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    raise BrainError("回覆裡找不到 JSON")


def _validate(schema: type[Model], data) -> Model:
    try:
        return schema.model_validate(data)
    except ValidationError as error:
        raise BrainError(f"回覆格式不符：{error.errors()[0]['msg']}") from error


class Brain:
    key = ""
    command: list[str] = []
    can_browse = False  # whether it can search the web on its own

    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.brain_timeout

    @property
    def label(self) -> str:
        return LABELS[self.key]

    def available(self) -> bool:
        return bool(self.command) and shutil.which(self.command[0]) is not None

    def ask(self, schema: type[Model], task: str, context: str, effort: str = "medium", *, web: bool = False) -> Model:
        raise NotImplementedError

    def run(self, args: list[str], *, stdin: str | None, cwd: Path, env: dict | None = None, timeout: int | None = None) -> str:
        executable = shutil.which(self.command[0])
        if not executable:
            raise BrainError(f"找不到 {self.command[0]}，請先安裝並登入 {self.label}")
        try:
            result = subprocess.run(
                [executable, *self.command[1:], *args],
                input=stdin,
                stdin=None if stdin is not None else subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd,
                env=env,
                timeout=timeout or self.timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise BrainError(f"{self.label} 超過 {timeout or self.timeout} 秒沒有回應") from error
        if result.returncode != 0 and not result.stdout.strip():
            tail = (result.stderr or "").strip().splitlines()[-1:] or [f"結束代碼 {result.returncode}"]
            raise BrainError(f"{self.label} 執行失敗：{tail[0][:200]}")
        return result.stdout


class ClaudeCodeBrain(Brain):
    key = "claude-code"
    can_browse = True

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.command = shlex.split(settings.claude_code_command)

    def ask(self, schema, task, context, effort="medium", *, web=False):
        args = [
            "-p",
            "--output-format", "json",
            "--json-schema", json.dumps(schema.model_json_schema(), ensure_ascii=False),
            "--system-prompt", VOICE_GUIDE,
            "--permission-mode", "dontAsk",
        ]
        if web:
            args += ["--allowedTools", "WebSearch,WebFetch"]
        if self.settings.claude_code_model:
            args += ["--model", self.settings.claude_code_model]
        # An API key in the environment would make Claude Code bill the API instead of your Claude plan.
        env = {k: v for k, v in os.environ.items() if k not in {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"}}
        with tempfile.TemporaryDirectory(prefix="office-claude-") as folder:
            out = self.run(args, stdin=f"{task}\n\n{context}", cwd=Path(folder), env=env)
        try:
            data = json.loads(out.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError) as error:
            raise BrainError("Claude Code 的輸出不是 JSON") from error
        if data.get("is_error"):
            raise BrainError(f"Claude Code：{str(data.get('result'))[:200]}")
        if data.get("structured_output") is not None:
            return _validate(schema, data["structured_output"])
        return _validate(schema, parse_json_text(str(data.get("result", ""))))


class CodexBrain(Brain):
    key = "codex"

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.command = shlex.split(settings.codex_command)

    def _base_args(self, effort: str | None = None) -> list[str]:
        args = ["--skip-git-repo-check", "--ephemeral"]
        if self.settings.codex_model:
            args += ["-m", self.settings.codex_model]
        if effort:
            args += ["-c", f'model_reasoning_effort="{effort}"']
        return args

    def ask(self, schema, task, context, effort="medium", *, web=False):
        with tempfile.TemporaryDirectory(prefix="office-codex-") as folder:
            root = Path(folder)
            (root / "schema.json").write_text(json.dumps(strict_schema(schema), ensure_ascii=False), encoding="utf-8")
            args = ["exec", "-", *self._base_args(effort), "--sandbox", "read-only", "--output-schema", "schema.json", "-o", "answer.json"]
            stdout = self.run(args, stdin=f"{VOICE_GUIDE}\n\n{task}\n\n{context}", cwd=root)
            answer = root / "answer.json"
            text = answer.read_text(encoding="utf-8") if answer.is_file() else stdout
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = parse_json_text(text)
        return _validate(schema, data)

    def image(self, description: str, out_path: Path, size: str = "1024x1536") -> Path:
        """One illustration from Codex's built-in image generation ($imagegen), saved to out_path (.png/.jpg/.webp)."""
        started = time.time()
        task = (
            f"$imagegen 產生一張 {size} 的直式插圖：{description}\n"
            "風格：柔和 3D 插畫、淺藍與蜜桃色、乾淨明亮，上方留白。畫面裡不能出現任何文字、字母或數字。\n"
            "完成後把圖片檔複製到目前資料夾，檔名 art.png，最後只回覆檔名。"
        )
        with tempfile.TemporaryDirectory(prefix="office-codex-art-") as folder:
            root = Path(folder)
            self.run(["exec", "-", *self._base_args(), "--sandbox", "workspace-write"], stdin=task, cwd=root, timeout=self.timeout)
            found = _newest_image([root], since=0) or _newest_image([_codex_home() / "generated_images"], since=started)
            if not found:
                raise BrainError("Codex 沒有產出圖片")
            out_path = out_path.with_suffix(found.suffix.lower())
            out_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(found, out_path)
        return out_path


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


IMAGE_MAGIC = {b"\x89PNG": ".png", b"\xff\xd8\xff": ".jpg", b"RIFF": ".webp"}


def _newest_image(folders: list[Path], since: float) -> Path | None:
    candidates = []
    for folder in folders:
        if not folder.is_dir():
            continue
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and path.stat().st_mtime >= since:
                head = path.read_bytes()[:4]
                if any(head.startswith(magic) for magic in IMAGE_MAGIC):
                    candidates.append(path)
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


class AntigravityBrain(Brain):
    key = "antigravity"
    can_browse = True

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.command = shlex.split(settings.antigravity_command)

    def ask(self, schema, task, context, effort="medium", *, web=False):
        prompt = (
            f"{VOICE_GUIDE}\n\n{task}\n\n{context}\n\n"
            "最後只輸出一個符合下面 JSON Schema 的 JSON 物件，不要任何其他文字，也不要修改任何檔案：\n"
            f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )
        with tempfile.TemporaryDirectory(prefix="office-antigravity-") as folder:
            out = self.run([prompt], stdin=None, cwd=Path(folder))
        return _validate(schema, parse_json_text(out))


class ApiBrain(Brain):
    key = "api"

    def __init__(self, settings: Settings, client=None):
        super().__init__(settings)
        self._client = client

    def available(self) -> bool:
        return self._client is not None or has_claude_api_credentials()

    @property
    def client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic()
        return self._client

    def ask(self, schema, task, context, effort="medium", *, web=False):
        import anthropic

        try:
            response = self.client.beta.messages.parse(
                model=self.settings.model,
                max_tokens=16000,
                betas=[FALLBACK_BETA],
                fallbacks="default",
                # The voice guide is identical on every call, so it is cached; the day's facts go in the message.
                system=[{"type": "text", "text": VOICE_GUIDE, "cache_control": {"type": "ephemeral"}}],
                output_config={"effort": effort},
                output_format=schema,
                messages=[{"role": "user", "content": f"{task}\n\n{context}"}],
            )
        except anthropic.APIStatusError as error:
            raise BrainError(f"Claude API 錯誤 {error.status_code}：{error.message}") from error
        except anthropic.APIConnectionError as error:
            raise BrainError("連不上 Claude API") from error
        if response.stop_reason == "refusal":
            raise BrainError("Claude 拒絕了這個請求")
        if response.stop_reason == "max_tokens" or response.parsed_output is None:
            raise BrainError("Claude 的回覆不完整")
        return response.parsed_output


BRAINS = {"claude-code": ClaudeCodeBrain, "codex": CodexBrain, "antigravity": AntigravityBrain, "api": ApiBrain}


def build(key: str, settings: Settings) -> Brain | None:
    """A brain instance, or None for the offline templates."""
    return BRAINS[key](settings) if key in BRAINS else None
