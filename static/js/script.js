const checkboxes = Array.from(document.querySelectorAll("input[type='checkbox'][value]"));
const selectedBox = document.getElementById("selected-box");
const selectedCount = document.getElementById("selected-count");
const resultsBody = document.getElementById("results-body");
const setupInfo = document.getElementById("setup-info");
const statusBadge = document.getElementById("status-badge");
const runBtn = document.getElementById("run-btn");
const clearBtn = document.getElementById("clear-btn");
const clearSmallBtn = document.getElementById("clear-small-btn");
const selectAllBtn = document.getElementById("select-all-btn");
const searchInput = document.getElementById("search");
const companyItems = Array.from(document.querySelectorAll(".company-item"));
const chartCanvas = document.getElementById("time-chart");

checkboxes.forEach(cb => cb.addEventListener("change", updateSelected));
searchInput.addEventListener("input", filterCompanies);
clearBtn.addEventListener("click", clearAll);
clearSmallBtn.addEventListener("click", clearAll);
selectAllBtn.addEventListener("click", selectVisible);
runBtn.addEventListener("click", runExperiment);
window.addEventListener("resize", () => drawChart(window.lastChart || []));

updateSelected();
drawChart([]);

function getSelected() {
    return checkboxes.filter(cb => cb.checked);
}

function updateSelected() {
    const selected = getSelected();

    selectedCount.textContent = selected.length;
    selectedBox.innerHTML = "";

    companyItems.forEach(item => {
        const cb = item.querySelector("input");
        item.classList.toggle("active", cb.checked);
    });

    if (selected.length === 0) {
        selectedBox.innerHTML = `
            <div class="empty-selected">
                إذا ما اخترت شركات، النظام يستخدم أول n من الداتا.
            </div>
        `;
        return;
    }

    selected.forEach(cb => {
        const item = cb.closest(".company-item");
        const name = item.querySelector("span").textContent.trim();
        const symbol = cb.value;

        const tag = document.createElement("div");
        tag.className = "selected-tag";

        tag.innerHTML = `
            <span>${name}</span>
            <small>${symbol}</small>
            <button>×</button>
        `;

        tag.querySelector("button").addEventListener("click", () => {
            cb.checked = false;
            updateSelected();
        });

        selectedBox.appendChild(tag);
    });
}

function filterCompanies() {
    const term = searchInput.value.trim().toLowerCase();

    companyItems.forEach(item => {
        const name = item.dataset.name || "";
        const symbol = item.dataset.symbol || "";
        const isVisible = name.includes(term) || symbol.includes(term);

        item.classList.toggle("hidden", !isVisible);
    });
}

function clearAll() {
    checkboxes.forEach(cb => cb.checked = false);
    updateSelected();
}

function selectVisible() {
    companyItems.forEach(item => {
        if (!item.classList.contains("hidden")) {
            item.querySelector("input").checked = true;
        }
    });

    updateSelected();
}

async function runExperiment() {
    const payload = {
        stocks: getSelected().map(cb => cb.value),
        max_n: Number(document.getElementById("max-n").value || 50),
        repetitions: Number(document.getElementById("repetitions").value || 5),
        case_type: document.getElementById("case-type").value,
        include_extra: document.getElementById("include-extra").checked,
        custom_budget: Number(document.getElementById("custom-budget")?.value || 0)
    };


    setLoading(true);

    try {
        const response = await fetch("/run_experiment", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Experiment failed");
        }

        renderSetup(data.setup, data.algorithms);
        renderTable(data.rows);

        window.lastChart = data.chart;
        drawChart(data.chart);

        statusBadge.textContent = "Done";
        statusBadge.className = "status-badge done";

    } catch (error) {
        resultsBody.innerHTML = `
            <tr>
                <td colspan="10" class="empty-row error">${error.message}</td>
            </tr>
        `;

        setupInfo.innerHTML = `
            <div class="empty-state error">
                تأكد أن ملفات dataset/archive موجودة وأن السيرفر يعمل.
            </div>
        `;

        drawChart([]);

        statusBadge.textContent = "Error";
        statusBadge.className = "status-badge error";

    } finally {
        setLoading(false);
    }
}

function setLoading(isLoading) {
    runBtn.disabled = isLoading;
    runBtn.textContent = isLoading ? "جاري الحساب..." : "تشغيل التجربة";

    if (isLoading) {
        statusBadge.textContent = "Running";
        statusBadge.className = "status-badge running";
    }
}

function renderSetup(setup, algorithms) {
    const algoText = algorithms.map(a => `• ${a.name}`).join("<br>");

    setupInfo.innerHTML = `
        <div class="setup-card highlight-card">
            <span>🏆 Top 3 Best Companies (If all budget invested)</span>
            <strong>${setup.top_best_companies.join("<br>")}</strong>
        </div>
        <div class="setup-card warning-card">
            <span>⚠️ Top 3 Worst Companies (If all budget invested)</span>
            <strong>${setup.top_worst_companies.join("<br>")}</strong>
        </div>
        <div class="setup-card">
            <span>📊 Dataset & Budget</span>
            <strong>Budget: ${setup.budget_used}<br>Dataset Used: ${setup.dataset_size_used} companies<br>Case: ${setup.case_type}<br>Repetitions: ${setup.repetitions}</strong>
        </div>
        <div class="setup-card">
            <span>⚙️ Configuration</span>
            <strong>${setup.same_inputs}<br><br>Algorithms:<br>${algoText}</strong>
        </div>
    `;
}

function infoItem(label, value) {
    return `
        <div class="setup-card">
            <span>${label}</span>
            <strong>${value}</strong>
        </div>
    `;
}

function renderTable(rows) {
    if (!rows || rows.length === 0) {
        resultsBody.innerHTML = `
            <tr>
                <td colspan="10" class="empty-row">لا توجد نتائج.</td>
            </tr>
        `;
        return;
    }

    resultsBody.innerHTML = rows.map(row => `
        <tr class="${row.skipped ? "muted" : ""}">
            <td>${row.n}</td>
            <td>${row.case}</td>
            <td>${row.algorithm}${row.skipped ? " (Skipped)" : ""}</td>
            <td>${row.family}</td>
            <td>${format(row.avg_time_ms)}</td>
            <td>${format(row.best_time_ms)}</td>
            <td>${format(row.worst_time_ms)}</td>
            <td>${format(row.avg_profit)}</td>
            <td>${row.time_complexity}</td>
            <td>${row.space_complexity}</td>
        </tr>
    `).join("");
}

function format(value) {
    if (value === null || value === undefined) {
        return "-";
    }

    return value;
}

function drawChart(chartData) {
    const canvas = chartCanvas;
    const ctx = canvas.getContext("2d");

    const parentWidth = canvas.parentElement.clientWidth - 40;

    canvas.width = Math.max(parentWidth, 500);
    canvas.height = 280;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const padding = 45;
    const width = canvas.width - padding * 2;
    const height = canvas.height - padding * 2;

    ctx.strokeStyle = "#334155";
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, padding + height);
    ctx.lineTo(padding + width, padding + height);
    ctx.stroke();

    if (!chartData || chartData.length === 0) {
        ctx.fillStyle = "#64748b";
        ctx.font = "14px Inter";
        ctx.textAlign = "center";
        ctx.fillText("Run the experiment to draw the graph", canvas.width / 2, canvas.height / 2);
        return;
    }

    const keys = ["greedy", "dp", "bruteforce"].filter(key =>
        chartData.some(row => row[key] !== null && row[key] !== undefined)
    );

    const labels = {
        greedy: "Greedy",
        dp: "DP",
        bruteforce: "Brute Force"
    };

    const colors = {
        greedy: "#60a5fa",
        dp: "#34d399",
        bruteforce: "#fbbf24"
    };

    const maxN = Math.max(...chartData.map(row => row.n));
    const maxTime = Math.max(
        1,
        ...chartData.flatMap(row => keys.map(key => row[key] || 0))
    );

    ctx.fillStyle = "#94a3b8";
    ctx.font = "12px Inter";
    ctx.textAlign = "center";

    chartData.forEach(row => {
        const x = padding + (row.n / maxN) * width;
        ctx.fillText(row.n, x, padding + height + 22);
    });

    ctx.textAlign = "right";

    for (let i = 0; i <= 4; i++) {
        const value = (maxTime / 4) * i;
        const y = padding + height - (value / maxTime) * height;

        ctx.fillStyle = "#475569";
        ctx.fillText(value.toFixed(2), padding - 8, y + 4);

        ctx.strokeStyle = "rgba(51,65,85,.35)";
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(padding + width, y);
        ctx.stroke();
    }

    keys.forEach((key, index) => {
        ctx.strokeStyle = colors[key];
        ctx.fillStyle = colors[key];
        ctx.lineWidth = 2;

        ctx.beginPath();

        chartData.forEach((row, i) => {
            if (row[key] === null || row[key] === undefined) {
                return;
            }

            const x = padding + (row.n / maxN) * width;
            const y = padding + height - (row[key] / maxTime) * height;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        chartData.forEach(row => {
            if (row[key] === null || row[key] === undefined) {
                return;
            }

            const x = padding + (row.n / maxN) * width;
            const y = padding + height - (row[key] / maxTime) * height;

            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        });

        ctx.fillText(labels[key], padding + width - (index * 95), padding - 18);
    });
}