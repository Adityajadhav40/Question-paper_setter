const departmentEl = document.getElementById("department");
const subjectEl = document.getElementById("subject");
const topicEl = document.getElementById("topic");
const subtopicEl = document.getElementById("subtopic");
const difficultyEl = document.getElementById("difficulty");
const marksEl = document.getElementById("marks");
const variantCountEl = document.getElementById("variantCount");
const examTypeEl = document.getElementById("examType");
const semesterEl = document.getElementById("semester");
const paperTitleEl = document.getElementById("paperTitle");
const createdByEl = document.getElementById("createdBy");
const patternUsedEl = document.getElementById("patternUsed");
const typeCheckboxes = document.querySelectorAll("input[name='questionType']");
const statusMessageEl = document.getElementById("statusMessage");
const heroStatsEl = document.getElementById("heroStats");
const summaryGridEl = document.getElementById("summaryGrid");
const paperMetaEl = document.getElementById("paperMeta");
const papersContainerEl = document.getElementById("papersContainer");
const analysisGridEl = document.getElementById("analysisGrid");
const datasetPillEl = document.getElementById("datasetPill");
const mlEnabledTextEl = document.getElementById("mlEnabledText");
const mlModelTextEl = document.getElementById("mlModelText");
const openAiStatusTextEl = document.getElementById("openAiStatusText");
const subjectSearchEl = document.getElementById("subjectSearch");
const topicSearchEl = document.getElementById("topicSearch");
const subtopicSearchEl = document.getElementById("subtopicSearch");
const chatLogEl = document.getElementById("chatLog");
const chatInputEl = document.getElementById("chatInput");
const chatSendBtn = document.getElementById("chatSendBtn");
const chatClearBtn = document.getElementById("chatClearBtn");
const themeToggleEl = document.getElementById("themeToggle");
const commandPaletteBtnEl = document.getElementById("commandPaletteBtn");
const commandBackdropEl = document.getElementById("commandBackdrop");
const commandInputEl = document.getElementById("commandInput");
const commandListEl = document.getElementById("commandList");
const toastStackEl = document.getElementById("toastStack");
const floatingGenerateBtnEl = document.getElementById("floatingGenerateBtn");
const difficultyChartCanvas = document.getElementById("difficultyChart");
const typeChartCanvas = document.getElementById("typeChart");

const addQuestionBtn = document.getElementById("addQuestionBtn");
const loadQuestionsBtn = document.getElementById("loadQuestionsBtn");
const importFileBtn = document.getElementById("importFileBtn");
const importFileEl = document.getElementById("importFile");
const uploadNotesBtn = document.getElementById("uploadNotesBtn");
const uploadNotesAiBtn = document.getElementById("uploadNotesAiBtn");
const notesLibraryBtn = document.getElementById("notesLibraryBtn");
const notesFileEl = document.getElementById("notesFile");
const registerBtn = document.getElementById("registerBtn");
const loginBtn = document.getElementById("loginBtn");
const saveBlueprintBtn = document.getElementById("saveBlueprintBtn");
const loadBlueprintsBtn = document.getElementById("loadBlueprintsBtn");
const similarityBtn = document.getElementById("similarityBtn");
const alternativesBtn = document.getElementById("alternativesBtn");
const reviewQueueBtn = document.getElementById("reviewQueueBtn");
const comparePapersBtn = document.getElementById("comparePapersBtn");
const generateBtn = document.getElementById("generateBtn");
const pdfBtn = document.getElementById("pdfBtn");
const analysisBtn = document.getElementById("analysisBtn");
const historyBtn = document.getElementById("historyBtn");
const tabButtons = document.querySelectorAll(".nav-tab");
const tabPanels = document.querySelectorAll(".tab-panel");

let latestPaperBundle = null;
let filterData = {};
let summaryData = {};
let currentUser = null;
let selectedBlueprint = null;
let lastAnalysisCards = [];
let difficultyChart = null;
let typeChart = null;
const commandItems = [
    { label: "Open Generate", action: () => switchTab("generate") },
    { label: "Open Manage", action: () => switchTab("manage") },
    { label: "Open Intelligence", action: () => switchTab("intelligence") },
    { label: "Load Analytics", action: () => loadAnalysis() },
    { label: "Load Saved Papers", action: () => loadHistory() },
    { label: "Preview Question Bank", action: () => loadQuestionPreview() },
    { label: "Load Review Queue", action: () => loadReviewQueue() },
];

function setStatus(message, type = "") {
    statusMessageEl.textContent = message;
    statusMessageEl.className = `status ${type}`.trim();
    if (message) {
        showToast(message, type || "info");
    }
}

function setButtonLoading(button, isLoading, loadingText = "Loading...") {
    if (!button) {
        return;
    }
    if (isLoading) {
        button.dataset.originalText = button.textContent;
        button.textContent = loadingText;
        button.classList.add("loading");
    } else {
        button.textContent = button.dataset.originalText || button.textContent;
        button.classList.remove("loading");
    }
}

function getSelectedQuestionTypes() {
    return Array.from(typeCheckboxes).filter((checkbox) => checkbox.checked).map((checkbox) => checkbox.value);
}

function createStatCard(value, label) {
    return `<div class="stat-card"><strong>${value}</strong><span>${label}</span></div>`;
}

function createMiniCard(value, label) {
    return `<div class="mini-card"><strong>${value}</strong><span>${label}</span></div>`;
}

function renderSummaryCards() {
    heroStatsEl.innerHTML = [
        createStatCard(summaryData.question_count || 0, "Questions in PostgreSQL"),
        createStatCard(summaryData.department_count || 0, "Departments"),
        createStatCard(summaryData.subject_count || 0, "Subjects"),
        createStatCard(summaryData.paper_count || 0, "Generated Papers"),
    ].join("");

    summaryGridEl.innerHTML = [
        createMiniCard(summaryData.verified_count || 0, "Verified Questions"),
        createMiniCard(summaryData.unverified_count || 0, "Pending Review"),
        createMiniCard("JSON / CSV", "Bulk Import"),
        createMiniCard("PDF", "Export Ready"),
    ].join("");

    datasetPillEl.textContent = `${summaryData.question_count || 0} questions available for generation`;
}

function switchTab(tabName) {
    tabButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.tab === tabName);
    });
    tabPanels.forEach((panel) => {
        const shouldShow = panel.dataset.panel === tabName || !panel.dataset.panel;
        panel.classList.toggle("hidden", !shouldShow);
    });
}

function addChatMessage(role, text) {
    const bubble = document.createElement("div");
    bubble.className = `chat-msg ${role}`;
    bubble.textContent = text;
    chatLogEl.appendChild(bubble);
    chatLogEl.scrollTop = chatLogEl.scrollHeight;
}

function clearChat() {
    chatLogEl.innerHTML = "";
    addChatMessage("bot", "AI assistant ready. Ask about the project, engineering concepts, or anything you want help with.");
}

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastStackEl.appendChild(toast);
    setTimeout(() => toast.remove(), 2600);
}

function openCommandPalette() {
    commandBackdropEl.classList.add("open");
    renderCommandList(commandItems);
    commandInputEl.value = "";
    setTimeout(() => commandInputEl.focus(), 0);
}

function closeCommandPalette() {
    commandBackdropEl.classList.remove("open");
}

function renderCommandList(items) {
    commandListEl.innerHTML = items.map((item, index) => `
        <div class="command-item" data-command-index="${index}">${item.label}</div>
    `).join("");
    commandListEl.querySelectorAll(".command-item").forEach((item) => {
        item.addEventListener("click", () => {
            const command = items[Number(item.dataset.commandIndex)];
            closeCommandPalette();
            command.action();
        });
    });
}

function populateExamTemplates() {
    const templates = filterData.exam_templates || {};
    examTypeEl.innerHTML = Object.keys(templates)
        .concat("Custom")
        .filter((value, index, array) => array.indexOf(value) === index)
        .map((value) => `<option value="${value}">${value}</option>`)
        .join("");
}

function populateSemesters() {
    semesterEl.innerHTML = ['<option value="">Any</option>']
        .concat((filterData.semesters || []).map((semester) => `<option value="${semester}">${semester}</option>`))
        .join("");
}

function populateDepartments() {
    const departments = Object.keys(filterData.departments || {});
    departmentEl.innerHTML = departments.map((department) => `<option value="${department}">${department}</option>`).join("");
    populateSubjects();
}

function populateSubjects() {
    const subjects = Object.keys((filterData.departments || {})[departmentEl.value] || {});
    subjectEl.innerHTML = subjects.map((subject) => `<option value="${subject}">${subject}</option>`).join("");
    populateTopics();
}

function populateTopics() {
    const topics = Object.keys((((filterData.departments || {})[departmentEl.value] || {})[subjectEl.value]) || {});
    topicEl.innerHTML = ['<option value="All Topics">All Topics</option>']
        .concat(topics.map((topic) => `<option value="${topic}">${topic}</option>`))
        .join("");
    populateSubtopics();
}

function populateSubtopics() {
    const topicMap = (((filterData.departments || {})[departmentEl.value] || {})[subjectEl.value]) || {};
    const subtopics = topicEl.value === "All Topics" ? [] : (topicMap[topicEl.value] || []);
    subtopicEl.innerHTML = ['<option value="All Subtopics">All Subtopics</option>']
        .concat(subtopics.map((subtopic) => `<option value="${subtopic}">${subtopic}</option>`))
        .join("");
}

function applyTemplateDefaults() {
    const template = (filterData.exam_templates || {})[examTypeEl.value];
    if (!template) {
        return;
    }
    marksEl.value = template.marks;
    variantCountEl.value = template.variants;
    patternUsedEl.value = template.pattern;
}

function renderMetaCard(label, value) {
    return `<div class="meta-card"><strong>${label}</strong><div>${value}</div></div>`;
}

function renderVariant(variant) {
    return `
        <article class="paper-card">
            <div class="paper-head">
                <div>
                    <h3>Variant ${variant.variant_number}</h3>
                    <span class="mono">${variant.total_marks} marks • ${variant.question_count} questions</span>
                </div>
                <div class="badge-row">
                    ${Object.entries(variant.type_distribution).map(([key, value]) => `<span class="badge">${key}: ${value}</span>`).join("")}
                </div>
            </div>
            <div class="question-list">
                ${variant.questions.map((item, index) => `
                    <details class="question-card">
                        <summary><strong>Q${index + 1}. ${item.question}</strong></summary>
                        <div class="badge-row">
                            <span class="badge">${item.type}</span>
                            <span class="badge">${item.difficulty}</span>
                            <span class="badge">${item.marks} marks</span>
                            <span class="badge">${item.topic} / ${item.subtopic}</span>
                            <span class="badge">Bloom: ${item.bloom_level || "NA"}</span>
                        </div>
                        <p><strong>Answer Key:</strong> ${item.answer || "Not available"}</p>
                    </details>
                `).join("")}
            </div>
        </article>
    `;
}

function renderPaperBundle(bundle) {
    latestPaperBundle = bundle;
    const metaCards = [
        renderMetaCard("Title", bundle.title),
        renderMetaCard("Department", bundle.department),
        renderMetaCard("Subject", bundle.subject),
        renderMetaCard("Topic", bundle.topic),
        renderMetaCard("Subtopic", bundle.subtopic),
        renderMetaCard("Exam Type", bundle.exam_type),
        renderMetaCard("Difficulty", bundle.requested_difficulty),
        renderMetaCard("Pattern", bundle.pattern_used),
    ];

    if (bundle.resolution_notes?.length) {
        metaCards.push(renderMetaCard("Generation Notes", bundle.resolution_notes.join(" ")));
    }

    paperMetaEl.innerHTML = metaCards.join("");
    papersContainerEl.innerHTML = bundle.variants?.length
        ? bundle.variants.map(renderVariant).join("")
        : `<div class="empty-state">No paper variants available yet.</div>`;
}

function renderDistributionBlock(title, data) {
    const items = Object.entries(data || {}).map(([key, value]) => `<li><strong>${key}</strong>: ${value}</li>`).join("");
    return `<div class="analysis-card"><h3>${title}</h3><ul class="clean-list">${items || "<li>No data</li>"}</ul></div>`;
}

function extractAnalysisEntries(card) {
    return `${card.title} ${JSON.stringify(card.data || {})}`.toLowerCase();
}

function updateAnalysisGrid(html) {
    analysisGridEl.innerHTML = html || `<div class="empty-state">No matching analytics data for the current search.</div>`;
}

function renderCharts(data) {
    if (!window.Chart || !difficultyChartCanvas || !typeChartCanvas) {
        return;
    }

    if (difficultyChart) {
        difficultyChart.destroy();
    }
    if (typeChart) {
        typeChart.destroy();
    }

    difficultyChart = new Chart(difficultyChartCanvas, {
        type: "pie",
        data: {
            labels: Object.keys(data.difficulty_distribution || {}),
            datasets: [
                {
                    data: Object.values(data.difficulty_distribution || {}),
                    backgroundColor: ["#1f6b4f", "#c79d4a", "#6287f8", "#d96b6b"],
                },
            ],
        },
        options: { responsive: true, maintainAspectRatio: false },
    });

    typeChart = new Chart(typeChartCanvas, {
        type: "bar",
        data: {
            labels: Object.keys(data.type_distribution || {}),
            datasets: [
                {
                    data: Object.values(data.type_distribution || {}),
                    backgroundColor: ["#1f6b4f", "#6287f8", "#c79d4a"],
                    borderRadius: 10,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
        },
    });
}

function applyAnalysisFilters() {
    if (!lastAnalysisCards.length) {
        return;
    }
    const subjectTerm = subjectSearchEl.value.trim().toLowerCase();
    const topicTerm = topicSearchEl.value.trim().toLowerCase();
    const subtopicTerm = subtopicSearchEl.value.trim().toLowerCase();

    const filtered = lastAnalysisCards.filter((card) => {
        const haystack = extractAnalysisEntries(card);
        if (subjectTerm && !haystack.includes(subjectTerm)) return false;
        if (topicTerm && !haystack.includes(topicTerm)) return false;
        if (subtopicTerm && !haystack.includes(subtopicTerm)) return false;
        return true;
    });

    updateAnalysisGrid(filtered.map((card) => card.html).join(""));
}

function renderAnalysis(data) {
    lastAnalysisCards = [
        { title: "Departments", data: data.department_distribution, html: renderDistributionBlock("Departments", data.department_distribution) },
        { title: "Subjects", data: data.subject_distribution, html: renderDistributionBlock("Subjects", data.subject_distribution) },
        { title: "Topics", data: data.topic_distribution, html: renderDistributionBlock("Topics", data.topic_distribution) },
        { title: "Subtopics", data: data.subtopic_distribution, html: renderDistributionBlock("Subtopics", data.subtopic_distribution) },
        { title: "Difficulty Mix", data: data.difficulty_distribution, html: renderDistributionBlock("Difficulty Mix", data.difficulty_distribution) },
        { title: "Question Types", data: data.type_distribution, html: renderDistributionBlock("Question Types", data.type_distribution) },
        { title: "Bloom Levels", data: data.bloom_distribution, html: renderDistributionBlock("Bloom Levels", data.bloom_distribution) },
        { title: "Verification", data: data.verified_distribution, html: renderDistributionBlock("Verification", data.verified_distribution) },
        { title: "Exam Templates Used", data: data.paper_distribution, html: renderDistributionBlock("Exam Templates Used", data.paper_distribution) },
    ];
    renderCharts(data);
    applyAnalysisFilters();
}

function renderHistory(payload) {
    lastAnalysisCards = (payload.papers || []).map((paper) => ({
        title: paper.subject,
        data: paper,
        html: `
        <div class="analysis-card">
            <h3>${paper.title} - Variant ${paper.variant_number}</h3>
            <p>${paper.department} • ${paper.subject} • ${paper.exam_type}</p>
            <p class="mono">${paper.total_marks} marks • ${paper.pattern_used}</p>
            <ul class="clean-list">
                ${paper.questions.slice(0, 6).map((item) => `<li>Q${item.sequence_number}: ${item.question} (${item.marks} marks)</li>`).join("")}
            </ul>
        </div>
    `,
    }));
    applyAnalysisFilters();
}

function renderQuestionPreview(payload) {
    lastAnalysisCards = (payload.questions || []).slice(0, 50).map((question) => ({
        title: question.subject,
        data: question,
        html: `
        <div class="analysis-card">
            <h3>${question.subject}</h3>
            <p>${question.topic} • ${question.subtopic}</p>
            <p>${question.question}</p>
            <div class="badge-row">
                <span class="badge">${question.type}</span>
                <span class="badge">${question.difficulty}</span>
                <span class="badge">${question.quality_score}</span>
                <span class="badge">${question.source_name || "Unknown source"}</span>
            </div>
        </div>
    `,
    }));
    applyAnalysisFilters();
}

function renderNotesLibrary(payload) {
    lastAnalysisCards = (payload.notes || []).map((note) => ({
        title: note.subject,
        data: note,
        html: `
        <div class="analysis-card">
            <h3>${note.title}</h3>
            <p>${note.department} • ${note.subject}</p>
            <p>${note.topic} / ${note.subtopic}</p>
            <div class="badge-row">
                <span class="badge">${note.file_name}</span>
                <span class="badge">${note.file_type.toUpperCase()}</span>
                <span class="badge">${note.generated_question_count} generated questions</span>
            </div>
        </div>
    `,
    }));
    applyAnalysisFilters();
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || data.message || "Request failed.");
    }
    return data;
}

async function loadBootData() {
    const [filters, summary, mlInfo] = await Promise.all([
        fetchJson("/filters"),
        fetchJson("/dashboard-summary"),
        fetchJson("/ml-info"),
    ]);

    filterData = filters;
    summaryData = summary;
    populateExamTemplates();
    populateSemesters();
    populateDepartments();
    renderSummaryCards();
    mlEnabledTextEl.textContent = mlInfo.enabled ? "ML Enabled" : "ML Fallback";
    mlModelTextEl.textContent = mlInfo.usage[0];
    openAiStatusTextEl.textContent = mlInfo.openai_chat_enabled
        ? "OpenAI enabled for AI Notes and AI Assistant"
        : "OpenAI not configured. AI Notes and AI Assistant run in guidance mode.";
    clearChat();
}

async function generatePaper() {
    setStatus("Generating paper variants...");
    setButtonLoading(generateBtn, true, "Generating...");
    papersContainerEl.innerHTML = `<div class="skeleton-grid"><div class="skeleton-card"></div><div class="skeleton-card"></div><div class="skeleton-card"></div></div>`;
    const payload = {
        department: departmentEl.value,
        subject: subjectEl.value,
        topic: topicEl.value,
        subtopic: subtopicEl.value,
        difficulty: difficultyEl.value,
        total_marks: Number(marksEl.value),
        question_types: getSelectedQuestionTypes(),
        variant_count: Number(variantCountEl.value),
        semester: semesterEl.value ? Number(semesterEl.value) : null,
        exam_type: examTypeEl.value,
        created_by: currentUser?.full_name || createdByEl.value,
        paper_title: paperTitleEl.value,
        pattern_used: patternUsedEl.value,
        blueprint: selectedBlueprint,
    };

    try {
        const data = await fetchJson("/generate-paper", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        renderPaperBundle(data.paper_bundle);
        const note = data.paper_bundle?.resolution_notes?.[0];
        setStatus(note ? `Paper variants generated successfully. ${note}` : "Paper variants generated successfully.", "success");
        summaryData.paper_count = (summaryData.paper_count || 0) + payload.variant_count;
        renderSummaryCards();
    } catch (error) {
        papersContainerEl.innerHTML = `<div class="empty-state">Paper generation failed. Please adjust the filters and try again.</div>`;
        setStatus(error.message, "error");
    } finally {
        setButtonLoading(generateBtn, false);
    }
}

async function loadAnalysis() {
    setStatus("Loading analytics...");
    analysisGridEl.innerHTML = `<div class="skeleton-grid"><div class="skeleton-card"></div><div class="skeleton-card"></div><div class="skeleton-card"></div></div>`;
    try {
        renderAnalysis(await fetchJson("/analysis"));
        setStatus("Analytics loaded successfully.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function loadHistory() {
    setStatus("Loading saved papers...");
    try {
        renderHistory(await fetchJson("/generated-papers"));
        setStatus("Saved papers loaded successfully.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function loadQuestionPreview() {
    setStatus("Loading question bank preview...");
    try {
        renderQuestionPreview(await fetchJson("/questions?limit=60"));
        setStatus("Question preview loaded successfully.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function addQuestion() {
    setStatus("Adding question...");
    const payload = {
        department: document.getElementById("adminDepartment").value,
        subject: document.getElementById("adminSubject").value,
        topic: document.getElementById("adminTopic").value,
        subtopic: document.getElementById("adminSubtopic").value,
        question: document.getElementById("adminQuestion").value,
        answer: document.getElementById("adminAnswer").value,
        difficulty: document.getElementById("adminDifficulty").value,
        marks: Number(document.getElementById("adminMarks").value),
        type: document.getElementById("adminType").value,
        bloom_level: document.getElementById("adminBloom").value,
        semester: Number(document.getElementById("adminSemester").value),
        is_verified: document.getElementById("adminVerified").value === "true",
        quality_score: 82,
        course_outcome: "CO-1",
        source_name: "Manual Admin Entry",
    };

    try {
        await fetchJson("/add-question", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        setStatus("Question added successfully.", "success");
        summaryData.question_count = (summaryData.question_count || 0) + 1;
        renderSummaryCards();
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function importFile() {
    if (!importFileEl.files.length) {
        setStatus("Choose a JSON or CSV file first.", "error");
        return;
    }

    setStatus("Importing dataset file...");
    const formData = new FormData();
    formData.append("file", importFileEl.files[0]);

    try {
        const response = await fetch("/import-file", { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Import failed.");
        }
        setStatus(`Import completed. Inserted ${data.inserted}, skipped ${data.skipped}.`, "success");
        summaryData.question_count = (summaryData.question_count || 0) + data.inserted;
        renderSummaryCards();
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function uploadNotes() {
    if (!notesFileEl.files.length) {
        setStatus("Choose a notes file first.", "error");
        return;
    }

    setStatus("Uploading notes and generating questions...");
    const formData = new FormData();
    formData.append("file", notesFileEl.files[0]);
    formData.append("title", document.getElementById("notesTitle").value);
    formData.append("department", document.getElementById("notesDepartment").value);
    formData.append("subject", document.getElementById("notesSubject").value);
    formData.append("topic", document.getElementById("notesTopic").value);
    formData.append("subtopic", document.getElementById("notesSubtopic").value);

    try {
        const response = await fetch("/upload-notes", { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Upload failed.");
        }
        analysisGridEl.innerHTML = (data.preview_questions || []).map((question) => `
            <div class="analysis-card">
                <h3>${question.subject}</h3>
                <p>${question.question}</p>
                <div class="badge-row">
                    <span class="badge">${question.type}</span>
                    <span class="badge">${question.difficulty}</span>
                    <span class="badge">${question.marks} marks</span>
                    <span class="badge">From uploaded notes</span>
                </div>
            </div>
        `).join("");
        setStatus(`Notes processed successfully. Inserted ${data.inserted_questions} new questions.`, "success");
        summaryData.question_count = (summaryData.question_count || 0) + data.inserted_questions;
        renderSummaryCards();
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function uploadNotesAi() {
    if (!notesFileEl.files.length) {
        setStatus("Choose a notes file first.", "error");
        return;
    }

    setStatus("Uploading notes for AI generation...");
    setButtonLoading(uploadNotesAiBtn, true, "AI Working...");
    const formData = new FormData();
    formData.append("file", notesFileEl.files[0]);
    formData.append("title", document.getElementById("notesTitle").value);
    formData.append("department", document.getElementById("notesDepartment").value);
    formData.append("subject", document.getElementById("notesSubject").value);
    formData.append("topic", document.getElementById("notesTopic").value);
    formData.append("subtopic", document.getElementById("notesSubtopic").value);

    try {
        const response = await fetch("/upload-notes-ai", { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "AI note generation failed.");
        }
        setStatus(
            data.used_fallback
                ? `OpenAI was limited, so local AI fallback inserted ${data.inserted_questions} questions.`
                : `AI note generation inserted ${data.inserted_questions} questions.`,
            "success"
        );
    } catch (error) {
        setStatus(error.message, "error");
    } finally {
        setButtonLoading(uploadNotesAiBtn, false);
    }
}

async function loadNotesLibrary() {
    setStatus("Loading uploaded notes...");
    try {
        renderNotesLibrary(await fetchJson("/notes-library"));
        setStatus("Uploaded notes loaded successfully.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function registerFaculty() {
    setStatus("Registering faculty user...");
    try {
        const data = await fetchJson("/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                full_name: document.getElementById("authFullName").value,
                username: document.getElementById("authUsername").value,
                password: document.getElementById("authPassword").value,
                role: document.getElementById("authRole").value,
                department: departmentEl.value || null,
            }),
        });
        setStatus(data.message, "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function loginFaculty() {
    setStatus("Logging in...");
    try {
        const data = await fetchJson("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: document.getElementById("authUsername").value,
                password: document.getElementById("authPassword").value,
            }),
        });
        currentUser = data.user;
        document.getElementById("authState").textContent = `Current user: ${currentUser.full_name} (${currentUser.role})`;
        createdByEl.value = currentUser.full_name;
        setStatus("Login successful.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function saveBlueprint() {
    setStatus("Saving blueprint...");
    const blueprint = {
        MCQ: Number(document.getElementById("blueprintMcq").value),
        Short: Number(document.getElementById("blueprintShort").value),
        Long: Number(document.getElementById("blueprintLong").value),
    };
    try {
        await fetchJson("/blueprints", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: document.getElementById("blueprintName").value,
                exam_type: document.getElementById("blueprintExamType").value,
                blueprint,
                created_by: currentUser?.full_name || createdByEl.value,
            }),
        });
        selectedBlueprint = blueprint;
        patternUsedEl.value = `Blueprint: ${document.getElementById("blueprintName").value}`;
        setStatus("Blueprint saved and selected.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function loadBlueprints() {
    setStatus("Loading blueprints...");
    try {
        const data = await fetchJson("/blueprints");
        lastAnalysisCards = (data.blueprints || []).map((item) => ({
            title: item.name,
            data: item,
            html: `
            <div class="analysis-card">
                <h3>${item.name}</h3>
                <p>${item.exam_type}</p>
                <div class="badge-row">
                    ${Object.entries(item.blueprint).map(([key, value]) => `<span class="badge">${key}: ${value}</span>`).join("")}
                </div>
            </div>
        `,
        }));
        applyAnalysisFilters();
        if (data.blueprints?.length) {
            selectedBlueprint = data.blueprints[0].blueprint;
        }
        setStatus("Blueprints loaded.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function loadSimilarity() {
    const questionId = Number(document.getElementById("similarityQuestionId").value);
    if (!questionId) {
        setStatus("Enter a question ID first.", "error");
        return;
    }
    setStatus("Finding similar questions...");
    try {
        const data = await fetchJson(`/questions/${questionId}/similar`);
        lastAnalysisCards = (data.matches || []).map((item) => ({
            title: item.question.subject,
            data: item.question,
            html: `
            <div class="analysis-card">
                <h3>Similarity ${Math.round(item.similarity * 100)}%</h3>
                <p>${item.question.question}</p>
                <div class="badge-row">
                    <span class="badge">${item.question.subject}</span>
                    <span class="badge">${item.question.topic}</span>
                    <span class="badge">${item.question.type}</span>
                </div>
            </div>
        `,
        }));
        applyAnalysisFilters();
        setStatus("Similar questions loaded.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function loadAlternatives() {
    const questionId = Number(document.getElementById("similarityQuestionId").value);
    if (!questionId) {
        setStatus("Enter a question ID first.", "error");
        return;
    }
    setStatus("Loading alternatives...");
    try {
        const data = await fetchJson(`/questions/${questionId}/alternatives`);
        renderQuestionPreview({ questions: data.alternatives || [] });
        setStatus("Alternative questions loaded.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function loadReviewQueue() {
    setStatus("Loading review queue...");
    try {
        renderQuestionPreview(await fetchJson("/review-queue"));
        setStatus("Review queue loaded.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function comparePapers() {
    const paperA = Number(document.getElementById("comparePaperA").value);
    const paperB = Number(document.getElementById("comparePaperB").value);
    if (!paperA || !paperB) {
        setStatus("Enter both paper IDs first.", "error");
        return;
    }
    setStatus("Comparing papers...");
    try {
        const data = await fetchJson(`/compare-papers?paper_a_id=${paperA}&paper_b_id=${paperB}`);
        lastAnalysisCards = [{
            title: "Paper Comparison",
            data,
            html: `
            <div class="analysis-card">
                <h3>Paper Comparison</h3>
                <ul class="clean-list">
                    <li><strong>Paper A</strong>: ${data.paper_a.title} (Variant ${data.paper_a.variant_number})</li>
                    <li><strong>Paper B</strong>: ${data.paper_b.title} (Variant ${data.paper_b.variant_number})</li>
                    <li><strong>Shared Questions</strong>: ${data.shared_question_count}</li>
                    <li><strong>Similarity</strong>: ${data.paper_similarity_percent}%</li>
                </ul>
            </div>
        `}];
        applyAnalysisFilters();
        setStatus("Paper comparison completed.", "success");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function sendChatMessage() {
    const message = chatInputEl.value.trim();
    if (!message) {
        return;
    }
    addChatMessage("user", message);
    chatInputEl.value = "";
    const typingRow = document.createElement("div");
    typingRow.className = "chat-row bot";
    typingRow.innerHTML = `<div class="typing"><span></span><span></span><span></span></div>`;
    chatLogEl.appendChild(typingRow);
    chatLogEl.scrollTop = chatLogEl.scrollHeight;
    try {
        setButtonLoading(chatSendBtn, true, "Sending...");
        const data = await fetchJson("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });
        typingRow.remove();
        addChatMessage("bot", data.reply);
    } catch (error) {
        typingRow.remove();
        if (String(error.message).includes("429")) {
            addChatMessage("bot", "Rate limit reached. Local assistant mode is active for now. Please wait a moment and try again later.");
        } else {
            addChatMessage("bot", `Sorry, chat failed: ${error.message}`);
        }
    } finally {
        setButtonLoading(chatSendBtn, false);
    }
}

function downloadPdf() {
    if (!latestPaperBundle) {
        setStatus("Generate a paper bundle before downloading PDF.", "error");
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const pageHeight = doc.internal.pageSize.height;
    let y = 18;

    doc.setFontSize(18);
    doc.text(latestPaperBundle.title, 14, y);
    y += 8;
    doc.setFontSize(11);
    doc.text(`${latestPaperBundle.department} | ${latestPaperBundle.subject} | ${latestPaperBundle.exam_type}`, 14, y);
    y += 7;
    doc.text(`Pattern: ${latestPaperBundle.pattern_used}`, 14, y);
    y += 8;
    doc.text(latestPaperBundle.instructions, 14, y, { maxWidth: 180 });
    y += 12;

    latestPaperBundle.variants.forEach((variant) => {
        if (y > pageHeight - 30) {
            doc.addPage();
            y = 18;
        }
        doc.setFontSize(14);
        doc.text(`Variant ${variant.variant_number}`, 14, y);
        y += 8;
        doc.setFontSize(10);
        variant.questions.forEach((item, index) => {
            const lines = doc.splitTextToSize(
                `Q${index + 1}. ${item.question} (${item.marks} marks, ${item.type}, ${item.difficulty})`,
                180
            );
            if (y + lines.length * 6 > pageHeight - 24) {
                doc.addPage();
                y = 18;
            }
            doc.text(lines, 14, y);
            y += lines.length * 6 + 2;
            const answerLines = doc.splitTextToSize(`Answer: ${item.answer || "Not available"}`, 176);
            doc.text(answerLines, 18, y);
            y += answerLines.length * 5 + 4;
        });
        y += 4;
    });

    doc.save(`${latestPaperBundle.subject.replace(/\s+/g, "_")}_paper_bundle.pdf`);
    setStatus("PDF downloaded successfully.", "success");
}

departmentEl.addEventListener("change", populateSubjects);
subjectEl.addEventListener("change", populateTopics);
topicEl.addEventListener("change", populateSubtopics);
examTypeEl.addEventListener("change", applyTemplateDefaults);
tabButtons.forEach((button) => button.addEventListener("click", () => switchTab(button.dataset.tab)));
generateBtn.addEventListener("click", generatePaper);
analysisBtn.addEventListener("click", loadAnalysis);
historyBtn.addEventListener("click", loadHistory);
loadQuestionsBtn.addEventListener("click", loadQuestionPreview);
addQuestionBtn.addEventListener("click", addQuestion);
importFileBtn.addEventListener("click", importFile);
uploadNotesBtn.addEventListener("click", uploadNotes);
uploadNotesAiBtn.addEventListener("click", uploadNotesAi);
notesLibraryBtn.addEventListener("click", loadNotesLibrary);
registerBtn.addEventListener("click", registerFaculty);
loginBtn.addEventListener("click", loginFaculty);
saveBlueprintBtn.addEventListener("click", saveBlueprint);
loadBlueprintsBtn.addEventListener("click", loadBlueprints);
similarityBtn.addEventListener("click", loadSimilarity);
alternativesBtn.addEventListener("click", loadAlternatives);
reviewQueueBtn.addEventListener("click", loadReviewQueue);
comparePapersBtn.addEventListener("click", comparePapers);
pdfBtn.addEventListener("click", downloadPdf);
chatSendBtn.addEventListener("click", sendChatMessage);
chatClearBtn.addEventListener("click", clearChat);
themeToggleEl.addEventListener("click", () => {
    document.body.classList.toggle("dark");
    localStorage.setItem("smart-qpg-theme", document.body.classList.contains("dark") ? "dark" : "light");
});
commandPaletteBtnEl.addEventListener("click", openCommandPalette);
floatingGenerateBtnEl.addEventListener("click", () => switchTab("generate"));
commandBackdropEl.addEventListener("click", (event) => {
    if (event.target === commandBackdropEl) {
        closeCommandPalette();
    }
});
commandInputEl.addEventListener("input", () => {
    const term = commandInputEl.value.trim().toLowerCase();
    const filtered = commandItems.filter((item) => item.label.toLowerCase().includes(term));
    renderCommandList(filtered);
});
document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        openCommandPalette();
    }
    if (event.key === "Escape") {
        closeCommandPalette();
    }
});
subjectSearchEl.addEventListener("input", applyAnalysisFilters);
topicSearchEl.addEventListener("input", applyAnalysisFilters);
subtopicSearchEl.addEventListener("input", applyAnalysisFilters);

if (localStorage.getItem("smart-qpg-theme") === "dark") {
    document.body.classList.add("dark");
}

loadBootData()
    .then(() => loadAnalysis())
    .catch((error) => setStatus(error.message, "error"));
