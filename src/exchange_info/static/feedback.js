/* The 用戶評價 form: sends one message to /feedback and says what happened. It keeps what was typed if sending fails. */
(() => {
  "use strict";
  const form = document.getElementById("feedback-form");
  if (!form) return;

  const thanks = document.getElementById("feedback-thanks");
  const status = document.getElementById("feedback-status");
  const submit = document.getElementById("feedback-submit");
  const message = document.getElementById("feedback-message");
  const counter = document.getElementById("feedback-count");
  const clearRating = document.getElementById("feedback-clear-rating");
  const MIN_LENGTH = 5;

  // Where the visitor came from is more useful to read than "feedback": the page they were on before opening this one.
  let cameFrom = "";
  let current = (window.location.hash || "#home").slice(1);
  window.addEventListener("hashchange", () => {
    const next = (window.location.hash || "#home").slice(1);
    if (next !== current && current !== "feedback") cameFrom = current;
    current = next;
  });

  function say(text, isError = false) {
    status.textContent = text;
    status.classList.toggle("is-error", isError);
  }

  function routeName() {
    const name = (cameFrom || current || "").split(/[=?&/]/)[0];
    return name.slice(0, 120);
  }

  function schoolName() {
    try {
      return typeof activeHomeSchool === "function" ? String(activeHomeSchool() || "").slice(0, 60) : "";
    } catch (_) {
      return "";
    }
  }

  message.addEventListener("input", () => {
    counter.textContent = `${message.value.length} / ${message.maxLength}`;
  });

  form.addEventListener("change", () => {
    clearRating.hidden = !form.elements.rating.value;
  });
  clearRating.addEventListener("click", () => {
    form.querySelectorAll('input[name="rating"]').forEach((input) => { input.checked = false; });
    clearRating.hidden = true;
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = message.value.trim();
    if (text.length < MIN_LENGTH) {
      say(`請至少寫 ${MIN_LENGTH} 個字，讓我們看得懂。`, true);
      message.focus();
      return;
    }
    const data = new FormData(form);
    const rating = Number(data.get("rating")) || null;
    submit.disabled = true;
    say("送出中…");
    try {
      const response = await fetch("/feedback", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          kind: data.get("kind") || "suggestion",
          rating,
          message: text,
          contact: String(data.get("contact") || "").trim(),
          website: String(data.get("website") || ""),
          route: routeName(),
          home_school: schoolName(),
        }),
      });
      if (response.status === 429) {
        say("送出得太頻繁了，請十分鐘後再試；你寫的內容還在。", true);
        return;
      }
      if (response.status === 422) {
        const body = await response.json().catch(() => ({}));
        say(typeof body.detail === "string" ? body.detail : "內容的格式不符，請檢查後再送出。", true);
        return;
      }
      if (!response.ok) throw new Error(String(response.status));
      form.reset();
      counter.textContent = `0 / ${message.maxLength}`;
      clearRating.hidden = true;
      say("");
      form.hidden = true;
      thanks.hidden = false;
      const mascot = document.querySelector(".feedback-mascot");
      if (mascot && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        mascot.classList.remove("is-hop");
        void mascot.offsetWidth;
        mascot.classList.add("is-hop");
        mascot.addEventListener("animationend", () => mascot.classList.remove("is-hop"), { once: true });
      }
      thanks.querySelector("h2")?.setAttribute("tabindex", "-1");
      thanks.querySelector("h2")?.focus();
    } catch (_) {
      say("暫時無法送出，請稍後再試；你寫的內容還在。", true);
    } finally {
      submit.disabled = false;
    }
  });

  document.getElementById("feedback-again")?.addEventListener("click", () => {
    thanks.hidden = true;
    form.hidden = false;
    message.focus();
  });
})();
