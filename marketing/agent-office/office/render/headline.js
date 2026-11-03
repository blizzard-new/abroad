/* Headlines, shared by the picture template (carousel.html) and the video template (video.html): the key word on a coral
 * block, a headline broken into lines that fit, set as big as the page allows. Loaded as /template/headline.js. */
window.Headline = (() => {
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  // Spans [at, end) of the emphasised words in a text (each word once, the first place it appears, no overlaps).
  function spansOf(text, words) {
    const hits = [];
    for (const word of words) {
      const at = word ? text.indexOf(word) : -1;
      if (at >= 0 && !hits.some((h) => at < h.end && at + word.length > h.at)) hits.push({ at, end: at + word.length });
    }
    return hits.sort((a, b) => a.at - b.at);
  }
  // Text with the given spans wrapped; everything is escaped.
  function markSpans(text, hits) {
    let out = "", cursor = 0;
    for (const h of hits) {
      out += esc(text.slice(cursor, h.at)) + `<mark class="em">${esc(text.slice(h.at, h.end))}</mark>`;
      cursor = h.end;
    }
    return out + esc(text.slice(cursor));
  }
  const marked = (text, words) => markSpans(String(text ?? ""), spansOf(String(text ?? ""), words));
  // A headline's lines with its emphasised words marked, even where a word runs over a line break (each line gets its piece).
  function titleHTML(lines, words) {
    const hits = spansOf(lines.join(""), words);
    let offset = 0;
    return lines.map((line) => {
      const start = offset;
      offset += line.length;
      const here = hits.map((h) => ({ at: Math.max(h.at, start) - start, end: Math.min(h.end, offset) - start })).filter((h) => h.end > h.at);
      return `<span class="seg">${markSpans(line, here)}</span>`;
    }).join("");
  }
  // Breaks a headline into lines for the width there is: an emphasised word stays whole when it fits on a line, a line never
  // starts with a closing mark, the lines come out about even (no last line of one lonely character), and nothing is left
  // out or reordered.
  function autoLines(text, perLine, words) {
    const total = [...text].length;
    if (total <= Math.max(3, perLine)) return [text];
    const pack = (limit) => {
      const chars = [...text];
      const spans = spansOf(text, words)
        .map((h) => ({ at: [...text.slice(0, h.at)].length, end: [...text.slice(0, h.end)].length }))
        .filter((h) => h.end - h.at <= limit);
      const atoms = [];
      for (let i = 0; i < chars.length;) {
        const span = spans.find((h) => h.at === i);
        if (span) { atoms.push(chars.slice(span.at, span.end).join("")); i = span.end; } else { atoms.push(chars[i]); i += 1; }
      }
      const closing = /^[，。、；：？！）」』…～~]$/;
      const lines = [];
      let line = "";
      for (const atom of atoms) {
        if (line && [...line].length + [...atom].length > limit) {
          if (closing.test(atom)) { const kept = [...line]; const carried = kept.pop(); lines.push(kept.join("")); line = carried; } else { lines.push(line); line = ""; }
        }
        line += atom;
      }
      if (line) lines.push(line);
      return lines;
    };
    perLine = Math.max(3, perLine);
    const lines = pack(perLine);
    // Full lines read best; only when the last line would be left with a character or two are the lines made about even.
    if (lines.length > 1 && [...lines[lines.length - 1]].length <= 2) {
      const even = Math.max(3, Math.ceil(total / lines.length));
      if (even < perLine) {
        const evened = pack(even);
        if (evened.length === lines.length) return evened;
      }
    }
    return lines;
  }
  // Sets a headline as big as it can be: its own line breaks when the design gave some, otherwise the lines that fit, at most
  // `maxLines` of them and no taller than `room`; the type only gets smaller when it has to.
  function layoutTitle(el, lines, words, { maxLines, room, min }) {
    const text = lines.join("");
    const width = el.clientWidth;
    let size = parseFloat(getComputedStyle(el).fontSize);
    // A short headline that fits on one line a little smaller reads better as one line than as a line and a stray character.
    const oneLine = Math.floor(width / [...text].length);
    if (lines.length === 1 && maxLines > 1 && oneLine >= size * 0.9 && oneLine < size) size = oneLine;
    // The designer's own lines that are only a little too wide for this size fit by making the type a touch smaller (at most 15%),
    // which keeps where she broke the phrases better than breaking them again.
    if (lines.length > 1) {
      const widest = Math.max(...lines.map((line) => [...line].length));
      const fitting = Math.floor(width / (widest + 0.25));  // a key-word block adds a little to its line
      if (fitting >= size * 0.85 && fitting < size) size = fitting;
    }
    let designed = lines.length > 1;  // the designer's own breaks, kept while they fit
    for (;;) {
      el.style.fontSize = `${size}px`;
      const perLine = Math.floor(width / size);
      // Her own breaks while they fit; when a line is too long only that line is split again, so where she parted the phrases stays.
      const use = lines.length === 1 ? autoLines(text, perLine, words) : designed ? lines : lines.flatMap((line) => autoLines(line, perLine, words));
      el.innerHTML = titleHTML(use, words);
      const wide = [...el.querySelectorAll(".seg")].some((seg) => seg.scrollWidth > width + 1);
      const limit = typeof room === "function" ? room(size) : room;
      const fits = !wide && use.length <= maxLines && el.scrollHeight <= limit;
      if (fits || size <= min) break;
      // Lines that are too long at this size (a designer's "交換一學期要準備" on one row) are broken again by the template at the
      // same size before the type is made any smaller.
      if (designed) { designed = false; continue; }
      size -= 4;
    }
  }

  return { esc, spansOf, markSpans, marked, titleHTML, autoLines, layoutTitle };
})();
