/* ResumeRadar front end. Plain JS, no framework.
   Everything that comes from the uploaded resume is inserted with textContent, never innerHTML. */
(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const SVG_NS = "http://www.w3.org/2000/svg";

  // el("div", {class: "x", text: "hi"}, child, child)
  function el(tag, props = {}, ...kids) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (v == null || v === false) continue;
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;
      else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) {
      if (kid == null || kid === false) continue;
      node.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    }
    return node;
  }
  function svg(tag, attrs = {}, ...kids) {
    const n = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    kids.forEach((k) => n.append(k));
    return n;
  }

  const upload = $("#upload"), dropPrompt = $("#dropPrompt"), fileChip = $("#fileChip");
  const fileInput = $("#file"), runBtn = $("#run"), runHint = $("#runHint"), errorBox = $("#error");
  const results = $("#results"), viewHome = $("#viewHome"), viewResults = $("#viewResults");
  let currentFile = null;

  function showView(name) {
    viewHome.hidden = name !== "home";
    viewResults.hidden = name !== "results";
    window.scrollTo({ top: 0, behavior: "auto" });
  }
  function showError(msg) {
    errorBox.hidden = !msg;
    errorBox.textContent = msg || "";
  }

  // ------------------------------------------------------------- file picking
  function setFile(file) {
    currentFile = file;
    dropPrompt.hidden = !!file;
    fileChip.hidden = !file;
    if (file) {
      $("#fileName").textContent = file.name;
      $("#fileSize").textContent = file.size > 102400 ? `${Math.round(file.size / 1024)} KB` : `${(file.size / 1024).toFixed(1)} KB`;
    }
    runBtn.disabled = !file;
    runHint.hidden = !!file;
    showError("");
  }

  $("#browse").addEventListener("click", () => fileInput.click());
  $("#changeFile").addEventListener("click", () => fileInput.click());
  $("#removeFile").addEventListener("click", () => { fileInput.value = ""; setFile(null); });
  fileInput.addEventListener("change", () => fileInput.files[0] && setFile(fileInput.files[0]));
  ["dragenter", "dragover"].forEach((ev) => upload.addEventListener(ev, (e) => { e.preventDefault(); upload.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => upload.addEventListener(ev, (e) => { e.preventDefault(); upload.classList.remove("over"); }));
  upload.addEventListener("drop", (e) => e.dataTransfer.files[0] && setFile(e.dataTransfer.files[0]));

  const SAMPLE_NAMES = { strong: "strong_resume.pdf", weak: "weak_resume.docx" };
  document.querySelectorAll("[data-sample]").forEach((btn) => btn.addEventListener("click", async () => {
    const key = btn.dataset.sample;
    try {
      const res = await fetch(`/api/sample/${key}`);
      if (!res.ok) throw new Error();
      setFile(new File([await res.blob()], SAMPLE_NAMES[key]));
    } catch {
      showError("Could not load the sample file. Is the server still running?");
    }
  }));
  $("#jdSample").addEventListener("click", async () => {
    try {
      const res = await fetch("/api/sample/job");
      if (!res.ok) throw new Error();
      $("#jd").value = await res.text();
    } catch {
      showError("Could not load the sample job description.");
    }
  });

  // --------------------------------------------------------------------- run
  runBtn.addEventListener("click", async () => {
    if (!currentFile) return;
    showError("");
    runBtn.disabled = true;
    showView("results");
    results.replaceChildren(el("div", { class: "busy" },
      el("div", { class: "spinner" }),
      el("p", { text: "Reading your resume" }),
      el("span", { text: "Checking contact details, sections, keywords and formatting." })));
    try {
      const body = new FormData();
      body.append("file", currentFile);
      body.append("job_description", $("#jd").value || "");
      const res = await fetch("/api/analyze", { method: "POST", body });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `The server returned an error (${res.status}).`);
      render(data.job_id, data.result);
    } catch (err) {
      results.replaceChildren();
      showView("home");
      showError(err.message || "Something went wrong. Try again.");
    } finally {
      runBtn.disabled = false;
    }
  });

  // --------------------------------------------------------------- rendering
  const tone = (score) => (score >= 85 ? "good" : score >= 70 ? "ok" : score >= 50 ? "warn" : "bad");
  const STATUS_ICON = { pass: "✓", warn: "!", fail: "✕" };
  const num = (n) => (Number.isInteger(n) ? String(n) : n.toFixed(1));

  function gauge(score) {
    const R = 54, C = 2 * Math.PI * R;
    const ring = svg("circle", { class: `ring-fg ${tone(score)}`, cx: 70, cy: 70, r: R, fill: "none",
      "stroke-width": 13, "stroke-linecap": "round", "stroke-dasharray": C, "stroke-dashoffset": C,
      transform: "rotate(-90 70 70)" });
    const label = svg("text", { x: 70, y: 76, "text-anchor": "middle", class: "ring-num" });
    label.textContent = String(score);
    const sub = svg("text", { x: 70, y: 96, "text-anchor": "middle", class: "ring-sub" });
    sub.textContent = "out of 100";
    const g = svg("svg", { viewBox: "0 0 140 140", class: "gauge", role: "img", "aria-label": `ATS score ${score} out of 100` },
      svg("circle", { class: "ring-bg", cx: 70, cy: 70, r: R, fill: "none", "stroke-width": 13 }), ring, label, sub);
    requestAnimationFrame(() => requestAnimationFrame(() => ring.setAttribute("stroke-dashoffset", C * (1 - score / 100))));
    return g;
  }

  const chips = (list, cls) => el("div", { class: "chips" }, list.map((t) => el("span", { class: `chip ${cls}`, text: t })));

  function suggestionCard(s, i) {
    return el("article", { class: `fix ${s.priority}` },
      el("div", { class: "fix-head" },
        el("span", { class: "fix-no", text: String(i + 1) }),
        el("h4", { text: s.title }),
        el("span", { class: `prio ${s.priority}`, text: s.priority }),
        el("span", { class: "gain", text: `+${num(s.gain)} pts` })),
      el("p", { class: "found" }, el("b", { text: "What we found: " }), s.problem),
      el("p", { class: "howto" }, el("b", { text: "How to fix it: " }), s.fix),
      s.examples.length
        ? (s.id === "jd_match"
          ? el("div", { class: "fix-chips" }, el("b", { text: "Missing keywords:" }), chips(s.examples, "miss"))
          : el("ul", { class: "examples" }, s.examples.map((x) => el("li", { text: x }))))
        : null);
  }

  function categoryBlock(cat) {
    const pct = cat.max ? Math.round((cat.score / cat.max) * 100) : 0;
    return el("details", { class: "cat" },
      el("summary", {},
        el("span", { class: "cat-name", text: cat.label }),
        el("span", { class: "cat-bar" }, el("i", { class: tone(pct), style: `width:${pct}%` })),
        el("span", { class: "cat-score", text: `${num(cat.score)} / ${cat.max}` })),
      el("ul", { class: "checks" }, cat.checks.map((c) =>
        el("li", { class: c.status },
          el("span", { class: "st", text: STATUS_ICON[c.status] }),
          el("div", {}, el("strong", { text: c.label }), el("span", { text: c.detail })),
          el("span", { class: "pts", text: `${num(c.points)}/${c.max}` })))));
  }

  function keywordsPanel(r) {
    const k = r.keywords;
    const wrap = el("div", { class: "kw" });
    if (k.mode === "job") {
      wrap.append(
        el("p", { class: "kw-lead" },
          el("b", { text: `${k.match_percent}% keyword match` }),
          k.similarity != null ? ` (overall text similarity ${k.similarity}%)` : ""),
        el("h4", { text: "Missing from your resume" }),
        k.missing.length ? chips(k.missing, "miss") : el("p", { class: "hint", text: "Nothing missing. Great match." }),
        el("h4", { text: "Already in your resume" }),
        k.found.length ? chips(k.found, "have") : el("p", { class: "hint", text: "None of the job's keywords were found." }));
    } else {
      wrap.append(el("p", { class: "kw-lead", text: "Skills we found in your resume" }));
      const cats = Object.entries(k.skills_by_category);
      if (!cats.length) wrap.append(el("p", { class: "hint", text: "No known skills were found." }));
      cats.forEach(([cat, list]) => wrap.append(el("h4", { text: cat }), chips(list, "have")));
      wrap.append(el("p", { class: "hint", text: "Go back and paste a job description to see which keywords you are missing for that job." }));
    }
    return wrap;
  }

  function render(jobId, r) {
    const gap = Math.max(0, r.potential_score - r.score);
    const top = r.suggestions.slice(0, 6), more = r.suggestions.slice(6);
    results.replaceChildren(
      el("div", { class: "score-hero" },
        gauge(r.score),
        el("div", { class: "score-text" },
          el("span", { class: `grade ${tone(r.score)}`, text: r.grade }),
          el("h2", { text: `Your ATS score is ${r.score}` }),
          el("p", { text: r.blurb }),
          gap ? el("p", { class: "potential" }, "Make the fixes below and you could reach about ", el("b", { text: String(r.potential_score) }), ".") : null,
          el("p", { class: "meta", text: `${r.file.name}, ${r.file.words} words, ${r.file.pages} page${r.file.pages === 1 ? "" : "s"}${r.file.pages_estimated ? " (estimated)" : ""}` }))),
      el("div", { class: "downloads" },
        el("a", { class: "btn main", href: `/api/plan/${jobId}` }, "Download action plan"),
        el("a", { class: "btn", href: `/api/report/${jobId}` }, "Full report (JSON)")),
      r.notes.length ? el("div", { class: "notes" }, r.notes.map((n) => el("p", { text: n }))) : null,

      el("h3", { class: "section-title", text: top.length ? "Fix these first" : "Nothing to fix" }),
      top.length
        ? el("div", { class: "fixes" }, top.map(suggestionCard))
        : el("p", { class: "all-good", text: "Every check passed. Your resume is in great shape." }),
      more.length ? el("details", { class: "more-fixes" },
        el("summary", { text: `${more.length} smaller improvement${more.length === 1 ? "" : "s"}` }),
        el("div", { class: "fixes" }, more.map((s, i) => suggestionCard(s, i + top.length)))) : null,

      el("h3", { class: "section-title", text: "Score breakdown" }),
      el("div", { class: "cats" }, r.categories.map(categoryBlock)),

      el("h3", { class: "section-title", text: r.keywords.mode === "job" ? "Keywords for this job" : "Your skills" }),
      keywordsPanel(r),

      el("div", { class: "again" }, el("button", { type: "button", id: "again", class: "btn", text: "Check another resume" })));
    $("#again").addEventListener("click", () => showView("home"));
  }
})();
