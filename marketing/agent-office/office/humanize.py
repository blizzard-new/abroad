"""Does it read like a person wrote it?

A language model leaves tells in Chinese copy: stock openers and closers, "不僅…更…" and "在…的時代" frames, a pile of
em dashes, "不是…而是…" in every other sentence. Readers feel them even when they cannot name them, and a brand account that
sounds like a press release loses the "real student" voice it is going for.

This is a plain rule check, not an AI detector: it catches a short list of tells that are almost never what a Taiwanese
student would write, so a hit is worth a rewrite. The same list is read to the writers (guide()) so they avoid the tells
up front, and to the reviewer (check()) so the ones that slip through are sent back.
"""

from __future__ import annotations

import re

# Openers, closers and buzzwords a model reaches for far more often than a student does.
STOCK_PHRASES = (
    "讓我們", "總而言之", "綜上所述", "總的來說", "總結來說", "簡而言之", "一言以蔽之",
    "值得一提的是", "值得注意的是", "需要注意的是", "不可否認", "毋庸置疑", "毫無疑問", "眾所周知",
    "在當今社會", "在當今時代", "與此同時", "深入探討", "全面解析", "深度解析", "賦能",
    "希望這篇", "希望對你有幫助",
)

# Sentence frames, with how to name them to the writer.
FRAMES = (
    (re.compile(r"不僅(?:僅)?[^。！？!?\n]{0,30}?(?:更|還|而且)"), "「不僅…更…」"),
    (re.compile(r"不只是[^。！？!?\n]{0,30}?(?:更是|還是)"), "「不只是…更是…」"),
    (re.compile(r"在[^。！？!?\n]{0,12}的(?:時代|浪潮|背景下)"), "「在…的時代」"),
    (re.compile(r"隨著[^。！？!?\n]{0,15}的(?:發展|普及|進步)"), "「隨著…的發展」"),
)

# One "不是A，而是B" is how people talk; three in a post is how a model argues.
CONTRAST = re.compile(r"不是[^。！？!?\n]{1,20}?而是")
CONTRAST_LIMIT = 1

DASH = re.compile(r"[—―─]+")
THREADS_DASHES = 1  # a Threads post is short
PAGES_DASHES = 2  # a carousel or a video script is several pages of copy


def check(text: str, *, max_dashes: int = THREADS_DASHES) -> list[str]:
    """What in this copy reads like a model wrote it, each as one instruction the author can act on."""
    found = [phrase for phrase in STOCK_PHRASES if phrase in text]
    found += [name for pattern, name in FRAMES if pattern.search(text)]
    issues = []
    if found:
        listed = "、".join(f"「{name.strip('「」')}」" for name in found[:4]) + ("等" if len(found) > 4 else "")
        issues.append(f"像 AI 寫的口頭禪或套句：{listed}。換成真人會講的話，或直接刪掉")
    contrasts = len(CONTRAST.findall(text))
    if contrasts > CONTRAST_LIMIT:
        issues.append(f"「不是…而是…」用了 {contrasts} 次，太像 AI 的對仗句，只留最需要的一個")
    dashes = len(DASH.findall(text))
    if dashes > max_dashes:
        issues.append(f"破折號用了 {dashes} 個（最多 {max_dashes} 個），要停頓就用逗號或分成兩句")
    return issues


def guide() -> str:
    """The same rules in words for the writers, so most drafts never need sending back."""
    return (
        "像真人寫的\n"
        f"- 不要用 AI 常見的口頭禪：{'、'.join(STOCK_PHRASES)}。\n"
        "- 不要用「不僅…更…」「不只是…更是…」「在…的時代」「隨著…的發展」這類套句；「不是…而是…」整篇最多一次。\n"
        f"- 破折號（——）整篇最多 {THREADS_DASHES} 個（輪播與影片腳本合計最多 {PAGES_DASHES} 個），要停頓就用逗號或分成兩句。\n"
        "- 句子有長有短，可以有口語、語助詞和一點不完美；不要每一段都工整地排比、每一句都像標語。"
    )
