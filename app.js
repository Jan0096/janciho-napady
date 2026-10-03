// Janciho nápady – nahrávanie, prepis a hodnotenie nápadov.

const SDK_URL = "https://cdn.jsdelivr.net/npm/@anthropic-ai/sdk/+esm";
const MODEL = "claude-opus-5-5";
const KEY_STORAGE = "napady.apiKey";
const IDEAS_STORAGE = "napady.ideas";
const CATEGORIES = ["konkurencia", "udrzatelnost", "kvalita"];

const $ = (id) => document.getElementById(id);

// ---------- Pomocné funkcie pre localStorage ----------
function load(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw === null ? fallback : JSON.parse(raw);
  } catch {
    return fallback;
  }
}
function save(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* prehliadač ukladanie nepovolil – appka funguje aj tak */
  }
}

function setStatus(el, text, kind = "") {
  el.textContent = text;
  el.className = "status" + (kind ? " " + kind : "");
}

// ---------- Nastavenia: API kľúč ----------
const apiKeyInput = $("apiKey");
apiKeyInput.value = load(KEY_STORAGE, "");
if (!apiKeyInput.value) $("settings").open = true;

$("saveKey").addEventListener("click", () => {
  save(KEY_STORAGE, apiKeyInput.value.trim());
  $("saveKey").textContent = "Uložené ✓";
  setTimeout(() => ($("saveKey").textContent = "Uložiť kľúč"), 1500);
});

// ---------- 1. Nahrávanie hlasu a prepis (Web Speech API) ----------
const recordBtn = $("recordBtn");
const recStatus = $("recStatus");
const transcript = $("transcript");

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isRecording = false;
let baseText = ""; // text, ktorý bol v poli pred začatím nahrávania
let finalText = ""; // finálne rozpoznané vety z aktuálneho nahrávania

if (!SpeechRecognition) {
  recordBtn.disabled = true;
  setStatus(recStatus, "Tento prehliadač nepodporuje rozpoznávanie reči. Použi Google Chrome alebo Microsoft Edge.", "error");
} else {
  recognition = new SpeechRecognition();
  recognition.lang = "sk-SK";
  recognition.continuous = true;
  recognition.interimResults = true;

  recognition.onresult = (event) => {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const text = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += text.trim() + " ";
      else interim += text;
    }
    transcript.value = (baseText + finalText + interim).trimStart();
  };

  recognition.onerror = (event) => {
    if (event.error === "no-speech") return; // ticho – necháme bežať ďalej
    const messages = {
      "not-allowed": "Prístup k mikrofónu bol zamietnutý. Povoľ mikrofón v prehliadači (ikona zámku vedľa adresy).",
      "audio-capture": "Nenašiel sa žiadny mikrofón.",
      network: "Chyba siete – rozpoznávanie reči potrebuje internet.",
    };
    setStatus(recStatus, messages[event.error] || "Chyba rozpoznávania: " + event.error, "error");
    stopRecording();
  };

  // Chrome po chvíli ticha nahrávanie sám ukončí – ak stále nahrávame, spustíme ho znova.
  recognition.onend = () => {
    if (isRecording) {
      baseText = transcript.value ? transcript.value.trimEnd() + " " : "";
      finalText = "";
      try { recognition.start(); } catch { stopRecording(); }
    }
  };

  recordBtn.addEventListener("click", () => (isRecording ? stopRecording() : startRecording()));
}

function startRecording() {
  baseText = transcript.value ? transcript.value.trimEnd() + " " : "";
  finalText = "";
  isRecording = true;
  try {
    recognition.start();
  } catch {
    /* už beží */
  }
  recordBtn.textContent = "⏹ Zastaviť nahrávanie";
  recordBtn.classList.add("recording");
  setStatus(recStatus, "🔴 Nahrávam… hovor po slovensky.");
}

function stopRecording() {
  isRecording = false;
  if (recognition) recognition.stop();
  recordBtn.textContent = "🎤 Nahrať nápad";
  recordBtn.classList.remove("recording");
  if (!recStatus.classList.contains("error")) setStatus(recStatus, "Nahrávanie zastavené. Text môžeš upraviť.", "ok");
}

// ---------- 3. Posuvníky skóre ----------
for (const key of CATEGORIES) {
  $(key).addEventListener("input", () => ($("out-" + key).textContent = $(key).value));
}

function setScore(key, value, reason) {
  const v = Math.min(10, Math.max(1, Math.round(Number(value) || 5)));
  $(key).value = v;
  $("out-" + key).textContent = v;
  $("reason-" + key).textContent = reason || "";
}

// ---------- 4. Navrhni skóre (Claude API) ----------
const suggestBtn = $("suggestBtn");
const aiStatus = $("aiStatus");
const summaryBox = $("summary");

let anthropicModule = null;
async function getClient(apiKey) {
  if (!anthropicModule) anthropicModule = await import(SDK_URL);
  const Anthropic = anthropicModule.default;
  // Appka beží priamo v prehliadači bez servera, preto treba povoliť volanie z prehliadača.
  return new Anthropic({ apiKey, dangerouslyAllowBrowser: true });
}

const scoreProperty = {
  type: "object",
  properties: {
    skore: { type: "integer", description: "Skóre 1 až 10" },
    odovodnenie: { type: "string", description: "1–2 vety po slovensky" },
  },
  required: ["skore", "odovodnenie"],
  additionalProperties: false,
};

const scoreTool = {
  name: "uloz_hodnotenie",
  description: "Uloží navrhované skóre nápadu v troch kategóriách s krátkym odôvodnením.",
  strict: true,
  input_schema: {
    type: "object",
    properties: {
      konkurencia: scoreProperty,
      udrzatelnost: scoreProperty,
      kvalita: scoreProperty,
      zhrnutie: { type: "string", description: "Krátke celkové zhrnutie po slovensky (max 2 vety)" },
    },
    required: ["konkurencia", "udrzatelnost", "kvalita", "zhrnutie"],
    additionalProperties: false,
  },
};

const SYSTEM_PROMPT = `Si skúsený hodnotiteľ podnikateľských a projektových nápadov. Odpovedáš po slovensky.
Ohodnoť nápad v troch kategóriách na stupnici 1–10:
- Konkurencia: 10 = takmer žiadna konkurencia / jasná výhoda, 1 = preplnený trh bez odlíšenia.
- Udržateľnosť: dlhodobá životaschopnosť – finančná, prevádzková aj environmentálna.
- Kvalita nápadu: originalita, užitočnosť a realizovateľnosť.
Zohľadni aj slovné hodnotenie autora, ale maj vlastný názor. Výsledok vždy vráť zavolaním nástroja uloz_hodnotenie.`;

suggestBtn.addEventListener("click", async () => {
  const idea = transcript.value.trim();
  const opinion = $("opinion").value.trim();
  const apiKey = apiKeyInput.value.trim() || load(KEY_STORAGE, "");

  if (!idea) return setStatus(aiStatus, "Najprv nahraj alebo napíš nápad.", "error");
  if (!apiKey) {
    $("settings").open = true;
    apiKeyInput.focus();
    return setStatus(aiStatus, "Chýba API kľúč – vlož ho do Nastavení hore.", "error");
  }

  suggestBtn.disabled = true;
  setStatus(aiStatus, "⏳ Claude premýšľa…");

  try {
    const client = await getClient(apiKey);
    const response = await client.beta.messages.create({
      model: MODEL,
      max_tokens: 16000,
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",
      system: SYSTEM_PROMPT,
      tools: [scoreTool],
      tool_choice: { type: "auto" },
      messages: [
        {
          role: "user",
          content: `NÁPAD:\n${idea}\n\nMOJE SLOVNÉ HODNOTENIE:\n${opinion || "(bez hodnotenia)"}`,
        },
      ],
    });

    if (response.stop_reason === "refusal") {
      throw new Error("Claude odmietol tento nápad ohodnotiť.");
    }
    const toolUse = response.content.find((b) => b.type === "tool_use" && b.name === "uloz_hodnotenie");
    if (!toolUse) throw new Error("Claude nevrátil hodnotenie. Skús to znova.");

    const r = toolUse.input;
    for (const key of CATEGORIES) setScore(key, r[key]?.skore, r[key]?.odovodnenie);
    summaryBox.textContent = r.zhrnutie || "";
    summaryBox.hidden = !r.zhrnutie;
    setStatus(aiStatus, "Hotovo ✓ Skóre môžeš ešte posunúť ručne.", "ok");
  } catch (err) {
    setStatus(aiStatus, friendlyError(err), "error");
  } finally {
    suggestBtn.disabled = false;
  }
});

function friendlyError(err) {
  const status = err?.status;
  if (status === 401) return "Neplatný API kľúč. Skontroluj ho v Nastaveniach.";
  if (status === 400 && /credit|billing/i.test(err.message)) return "Na účte nie je kredit. Dobi kredit v Anthropic Console (Billing).";
  if (status === 429) return "Príliš veľa požiadaviek – skús o chvíľu znova.";
  if (status >= 500) return "Služba Anthropic má momentálne problém – skús neskôr.";
  if (err instanceof TypeError || /fetch|network/i.test(err?.message || "")) {
    return "Nepodarilo sa spojiť so serverom. Si pripojený na internet?";
  }
  return "Chyba: " + (err?.message || err);
}

// ---------- Ukladanie nápadov ----------
let ideas = load(IDEAS_STORAGE, []);

$("saveIdeaBtn").addEventListener("click", () => {
  const text = transcript.value.trim();
  if (!text) return setStatus(aiStatus, "Nie je čo uložiť – nápad je prázdny.", "error");
  ideas.unshift({
    id: Date.now(),
    date: new Date().toLocaleString("sk-SK"),
    text,
    opinion: $("opinion").value.trim(),
    scores: Object.fromEntries(CATEGORIES.map((k) => [k, Number($(k).value)])),
    reasons: Object.fromEntries(CATEGORIES.map((k) => [k, $("reason-" + k).textContent])),
    summary: summaryBox.hidden ? "" : summaryBox.textContent,
  });
  save(IDEAS_STORAGE, ideas);
  renderIdeas();
  setStatus(aiStatus, "Nápad uložený ✓", "ok");
});

const LABELS = { konkurencia: "Konkurencia", udrzatelnost: "Udržateľnosť", kvalita: "Kvalita" };

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderIdeas() {
  const list = $("ideaList");
  list.replaceChildren();
  $("emptyList").hidden = ideas.length > 0;

  for (const idea of ideas) {
    const li = el("li");
    li.append(el("div", "meta", idea.date));
    li.append(el("p", "text", idea.text));
    if (idea.opinion) li.append(el("p", "meta", "Moje hodnotenie: " + idea.opinion));

    const badges = el("div", "badges");
    for (const k of CATEGORIES) badges.append(el("span", "badge", `${LABELS[k]}: ${idea.scores[k]}`));
    li.append(badges);

    const actions = el("div", "actions");
    const openBtn = el("button", "secondary", "Otvoriť");
    openBtn.type = "button";
    openBtn.addEventListener("click", () => openIdea(idea));
    const delBtn = el("button", "secondary", "Zmazať");
    delBtn.type = "button";
    delBtn.addEventListener("click", () => {
      if (!confirm("Naozaj zmazať tento nápad?")) return;
      ideas = ideas.filter((i) => i.id !== idea.id);
      save(IDEAS_STORAGE, ideas);
      renderIdeas();
    });
    actions.append(openBtn, delBtn);
    li.append(actions);
    list.append(li);
  }
}

function openIdea(idea) {
  transcript.value = idea.text;
  $("opinion").value = idea.opinion || "";
  for (const k of CATEGORIES) setScore(k, idea.scores[k], idea.reasons?.[k]);
  summaryBox.textContent = idea.summary || "";
  summaryBox.hidden = !idea.summary;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

renderIdeas();
