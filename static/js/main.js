/* ═══════════════════════════════════════════════════════════════
   PneumoScan — Main JavaScript
   ═══════════════════════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {

    /* ──────────── Theme Toggle ──────────── */
    const themeToggle = document.getElementById("themeToggle");
    const root = document.documentElement;

    // Load saved preference or default to light
    const savedTheme = localStorage.getItem("pneumoscan-theme");
    if (savedTheme === "dark") {
        root.classList.add("dark");
    } else {
        root.classList.remove("dark");
    }

    themeToggle?.addEventListener("click", () => {
        root.classList.toggle("dark");
        const isDark = root.classList.contains("dark");
        localStorage.setItem("pneumoscan-theme", isDark ? "dark" : "light");
    });


    /* ──────────── Floating Particles ──────────── */
    (() => {
        const container = document.getElementById("particles");
        if (!container) return;
        for (let i = 0; i < 18; i++) {
            const p = document.createElement("div");
            p.className = "particle";
            const size = Math.random() * 6 + 3;
            p.style.width = size + "px";
            p.style.height = size + "px";
            p.style.left = Math.random() * 100 + "%";
            p.style.animationDuration = Math.random() * 15 + 15 + "s";
            p.style.animationDelay = Math.random() * 20 + "s";
            container.appendChild(p);
        }
    })();


    /* ──────────── Live Clock ──────────── */
    const clockEl = document.getElementById("liveTime");
    function updateClock() {
        if (!clockEl) return;
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString("en-US", {
            hour: "2-digit", minute: "2-digit", second: "2-digit"
        });
    }
    updateClock();
    setInterval(updateClock, 1000);


    /* ──────────── Upload / Drag-and-Drop ──────────── */
    const form = document.getElementById("scanForm");
    const dropZone = document.getElementById("dropZone");
    const xrayInput = document.getElementById("xrayInput");
    const previewImg = document.getElementById("previewImg");
    const dropContent = document.getElementById("dropContent");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const clearBtn = document.getElementById("clearBtn");
    const loadingState = document.getElementById("loadingState");
    const resultCard = document.getElementById("resultCard");
    const errorCard = document.getElementById("errorCard");

    let selectedFile = null;
    let lastResult = null;

    // Click to browse
    dropZone?.addEventListener("click", () => xrayInput?.click());

    // File selected via input
    xrayInput?.addEventListener("change", (e) => {
        if (e.target.files.length) previewFile(e.target.files[0]);
    });

    // Drag events
    ["dragenter", "dragover"].forEach(evt =>
        dropZone?.addEventListener(evt, (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); })
    );
    ["dragleave", "drop"].forEach(evt =>
        dropZone?.addEventListener(evt, (e) => { e.preventDefault(); dropZone.classList.remove("drag-over"); })
    );
    dropZone?.addEventListener("drop", (e) => {
        if (e.dataTransfer.files.length) previewFile(e.dataTransfer.files[0]);
    });

    function previewFile(file) {
        selectedFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewImg.classList.remove("hidden");
            dropContent.classList.add("hidden");
        };
        reader.readAsDataURL(file);
    }

    // Clear
    clearBtn?.addEventListener("click", () => {
        selectedFile = null;
        xrayInput.value = "";
        previewImg.src = "";
        previewImg.classList.add("hidden");
        dropContent.classList.remove("hidden");
        resultCard?.classList.add("hidden");
        errorCard?.classList.add("hidden");
        form.reset();
    });


    /* ──────────── Form Submit → Predict ──────────── */
    form?.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!selectedFile) {
            showError("Please select a chest X-ray image first.");
            return;
        }

        const fd = new FormData(form);
        fd.set("xray", selectedFile);

        analyzeBtn.disabled = true;
        loadingState?.classList.remove("hidden");
        resultCard?.classList.add("hidden");
        errorCard?.classList.add("hidden");

        try {
            const res = await fetch("/predict", { method: "POST", body: fd });
            const data = await res.json();

            if (data.error) {
                showError(data.error);
            } else if (data.prediction === "Invalid Image") {
                showError(data.message);
            } else {
                lastResult = data;
                showResult(data);
            }
        } catch (err) {
            showError("Network error. Please try again.");
        } finally {
            analyzeBtn.disabled = false;
            loadingState?.classList.add("hidden");
        }
    });


    /* ──────────── Show Result ──────────── */
    function showResult(data) {
        resultCard?.classList.remove("hidden");

        const label = document.getElementById("resultLabel");
        const badge = document.getElementById("resultBadge");
        const bar = document.getElementById("confidenceBar");
        const confText = document.getElementById("confidenceText");
        const normalProb = document.getElementById("normalProb");
        const pneumoniaProb = document.getElementById("pneumoniaProb");

        label.textContent = data.prediction;
        confText.textContent = data.confidence + "%";
        normalProb.textContent = data.normal_prob + "%";
        pneumoniaProb.textContent = data.pneumonia_prob + "%";

        const isPneumonia = data.prediction === "PNEUMONIA";

        label.className = isPneumonia
            ? "text-2xl sm:text-3xl font-black text-red-500"
            : "text-2xl sm:text-3xl font-black text-emerald-500";

        confText.className = isPneumonia
            ? "text-xl font-black tabular-nums text-red-500"
            : "text-xl font-black tabular-nums text-emerald-500";

        badge.textContent = data.prediction;
        badge.className = isPneumonia
            ? "px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest bg-red-50 dark:bg-red-500/10 text-red-500 border border-red-200/50 dark:border-red-500/20"
            : "px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest bg-emerald-50 dark:bg-emerald-500/10 text-emerald-500 border border-emerald-200/50 dark:border-emerald-500/20";

        bar.className = isPneumonia
            ? "h-full rounded-full transition-all duration-1000 ease-out bg-gradient-to-r from-red-400 to-red-500"
            : "h-full rounded-full transition-all duration-1000 ease-out bg-gradient-to-r from-emerald-400 to-emerald-500";

        setTimeout(() => { bar.style.width = data.confidence + "%"; }, 100);

        // Update charts
        if (typeof updateCharts === "function") {
            updateCharts(data.confidence, 92);
        }
    }

    function showError(msg) {
        errorCard?.classList.remove("hidden");
        document.getElementById("errorText").textContent = msg;
    }


    /* ──────────── Download Report ──────────── */
    document.getElementById("downloadBtn")?.addEventListener("click", async () => {
        if (!lastResult) return;
        try {
            const res = await fetch("/download-report", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(lastResult),
            });
            if (!res.ok) throw new Error("Download failed");
            const blob = await res.blob();
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = "PneumoScan_Report.pdf";
            a.click();
            URL.revokeObjectURL(a.href);
        } catch {
            showError("Failed to download report. Please try again.");
        }
    });


    /* ──────────── INLINE CHAT ──────────── */
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatMessages = document.getElementById("chatMessages");
    const chatSuggestions = document.getElementById("chatSuggestions");

    // Suggestion chips
    chatSuggestions?.querySelectorAll(".chat-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            chatInput.value = chip.textContent;
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    // Send message
    chatForm?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const msg = chatInput.value.trim();
        if (!msg) return;

        appendMessage(msg, "user");
        chatInput.value = "";

        // Show typing indicator
        const typingEl = appendTyping();

        try {
            const res = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: msg }),
            });
            const data = await res.json();
            typingEl.remove();
            appendMessage(data.reply || "No response received.", "bot");
        } catch {
            typingEl.remove();
            appendMessage("⚠️ Could not reach the AI assistant. Please try again.", "bot");
        }
    });

    function appendMessage(text, sender) {
        const wrapper = document.createElement("div");
        wrapper.className = sender === "user" ? "flex justify-end" : "flex gap-2";

        if (sender === "user") {
            wrapper.innerHTML = `
                <div class="bg-med-500 text-white rounded-2xl rounded-tr-none px-3.5 py-2.5 max-w-[85%] shadow-sm">
                    <p class="text-[13px] leading-relaxed">${escapeHtml(text)}</p>
                </div>`;
        } else {
            wrapper.innerHTML = `
                <div class="w-6 h-6 rounded-full bg-med-100 dark:bg-med-500/20 flex-shrink-0 flex items-center justify-center">
                    <svg class="w-3.5 h-3.5 text-med-600 dark:text-med-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                </div>
                <div class="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 shadow-sm rounded-2xl rounded-tl-none px-3.5 py-2.5 max-w-[85%]">
                    <p class="text-[13px] text-slate-600 dark:text-slate-300 leading-relaxed">${formatBotText(text)}</p>
                </div>`;
        }

        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendTyping() {
        const wrapper = document.createElement("div");
        wrapper.className = "flex gap-2";
        wrapper.innerHTML = `
            <div class="w-6 h-6 rounded-full bg-med-100 dark:bg-med-500/20 flex-shrink-0 flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-med-600 dark:text-med-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
            </div>
            <div class="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 shadow-sm rounded-2xl rounded-tl-none px-4 py-3">
                <div class="flex gap-1.5">
                    <span class="w-2 h-2 bg-med-300 dark:bg-med-500 rounded-full animate-bounce" style="animation-delay:0s"></span>
                    <span class="w-2 h-2 bg-med-300 dark:bg-med-500 rounded-full animate-bounce" style="animation-delay:0.15s"></span>
                    <span class="w-2 h-2 bg-med-300 dark:bg-med-500 rounded-full animate-bounce" style="animation-delay:0.3s"></span>
                </div>
            </div>`;
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return wrapper;
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function formatBotText(text) {
        // Basic markdown-like formatting for bold (**text**) and newlines
        return escapeHtml(text)
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\n/g, "<br>");
    }

});
