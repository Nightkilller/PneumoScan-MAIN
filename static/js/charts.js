/* ══════════════════════════════════════════════════════════
   PneumoScan — Medical Data Card Charts (Chart.js)
   ═══════════════════════════════════════════════════════════ */

window.PneumoCharts = (() => {
    let confidenceChart = null;
    let qualityChart = null;
    let confidenceChartMobile = null;
    let qualityChartMobile = null;

    // Wait for Chart.js to load
    function init() {
        if (typeof Chart === "undefined") {
            setTimeout(init, 200);
            return;
        }

        const baseOpts = {
            responsive: false,
            cutout: "72%",
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            animation: { animateRotate: true, duration: 1000 },
        };

        // ── AI Confidence doughnut (Desktop) ──
        const confCtx = document.getElementById("confidenceChart");
        if (confCtx) {
            confidenceChart = new Chart(confCtx, {
                type: "doughnut",
                data: {
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ["rgba(56, 189, 248, 0.6)", "rgba(255,255,255,0.03)"],
                        borderWidth: 0,
                    }],
                },
                options: baseOpts,
            });
        }

        // ── Image Quality doughnut (Desktop) ──
        const qualCtx = document.getElementById("qualityChart");
        if (qualCtx) {
            qualityChart = new Chart(qualCtx, {
                type: "doughnut",
                data: {
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ["rgba(52, 211, 153, 0.6)", "rgba(255,255,255,0.03)"],
                        borderWidth: 0,
                    }],
                },
                options: baseOpts,
            });
        }

        // ── AI Confidence doughnut (Mobile) ──
        const confCtxMobile = document.getElementById("confidenceChartMobile");
        if (confCtxMobile) {
            confidenceChartMobile = new Chart(confCtxMobile, {
                type: "doughnut",
                data: {
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ["rgba(56, 189, 248, 0.6)", "rgba(255,255,255,0.03)"],
                        borderWidth: 0,
                    }],
                },
                options: baseOpts,
            });
        }

        // ── Image Quality doughnut (Mobile) ──
        const qualCtxMobile = document.getElementById("qualityChartMobile");
        if (qualCtxMobile) {
            qualityChartMobile = new Chart(qualCtxMobile, {
                type: "doughnut",
                data: {
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ["rgba(52, 211, 153, 0.6)", "rgba(255,255,255,0.03)"],
                        borderWidth: 0,
                    }],
                },
                options: baseOpts,
            });
        }
    }

    function update(confidence, isPneumonia) {
        const confVal = document.getElementById("confChartVal");
        const qualVal = document.getElementById("qualChartVal");
        const confValMobile = document.getElementById("confChartValMobile");
        const qualValMobile = document.getElementById("qualChartValMobile");

        const color = isPneumonia ? "rgba(239, 68, 68, 0.7)" : "rgba(56, 189, 248, 0.7)";
        const textClass = "text-xs sm:text-sm font-bold tabular-nums " +
            (isPneumonia ? "text-red-400" : "text-sky-400");

        // Update desktop confidence chart
        if (confidenceChart) {
            confidenceChart.data.datasets[0].data = [confidence, 100 - confidence];
            confidenceChart.data.datasets[0].backgroundColor[0] = color;
            confidenceChart.update();
        }
        // Update mobile confidence chart
        if (confidenceChartMobile) {
            confidenceChartMobile.data.datasets[0].data = [confidence, 100 - confidence];
            confidenceChartMobile.data.datasets[0].backgroundColor[0] = color;
            confidenceChartMobile.update();
        }

        // Update confidence labels
        if (confVal) { confVal.textContent = confidence + "%"; confVal.className = textClass; }
        if (confValMobile) { confValMobile.textContent = confidence + "%"; confValMobile.className = "text-[10px] sm:text-xs font-bold tabular-nums " + (isPneumonia ? "text-red-400" : "text-med-600"); }

        // Simulated quality score
        const quality = Math.min(100, Math.round(confidence * 0.95 + Math.random() * 5));

        if (qualityChart) {
            qualityChart.data.datasets[0].data = [quality, 100 - quality];
            qualityChart.update();
        }
        if (qualityChartMobile) {
            qualityChartMobile.data.datasets[0].data = [quality, 100 - quality];
            qualityChartMobile.update();
        }
        if (qualVal) qualVal.textContent = quality + "%";
        if (qualValMobile) qualValMobile.textContent = quality + "%";
    }

    function reset() {
        [confidenceChart, confidenceChartMobile].forEach(chart => {
            if (chart) {
                chart.data.datasets[0].data = [0, 100];
                chart.data.datasets[0].backgroundColor[0] = "rgba(56, 189, 248, 0.6)";
                chart.update();
            }
        });
        [qualityChart, qualityChartMobile].forEach(chart => {
            if (chart) {
                chart.data.datasets[0].data = [0, 100];
                chart.update();
            }
        });

        const confVal = document.getElementById("confChartVal");
        const qualVal = document.getElementById("qualChartVal");
        const confValMobile = document.getElementById("confChartValMobile");
        const qualValMobile = document.getElementById("qualChartValMobile");

        if (confVal) { confVal.textContent = "--"; confVal.className = "text-xs sm:text-sm font-bold text-med-600 tabular-nums"; }
        if (confValMobile) { confValMobile.textContent = "--"; confValMobile.className = "text-[10px] sm:text-xs font-bold text-med-600 tabular-nums"; }
        if (qualVal) { qualVal.textContent = "--"; }
        if (qualValMobile) { qualValMobile.textContent = "--"; }
    }

    init();

    return { update, reset };
})();
