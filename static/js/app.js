/* ═══════════════════════════════════════════════════════════
   AquaGuard — Application Logic
   Charts, Predictions, Animations
   ═══════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
    initWaterCanvas();
    initScrollAnimations();
    initNavbar();
    loadModelInfo();
    initForm();
    initPresets();
    initInputRanges();
    initCharts();
});

/* ── 1. Water Background Canvas ─────────────────────────── */
function initWaterCanvas() {
    const canvas = document.getElementById("water-canvas");
    const ctx = canvas.getContext("2d");
    let w, h, bubbles;

    function resize() {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    }

    function createBubbles() {
        const count = Math.min(Math.floor((w * h) / 20000), 60);
        bubbles = Array.from({ length: count }, () => ({
            x: Math.random() * w,
            y: Math.random() * h,
            r: Math.random() * 2.5 + 0.5,
            vx: (Math.random() - 0.5) * 0.3,
            vy: -(Math.random() * 0.4 + 0.1),
            alpha: Math.random() * 0.3 + 0.05,
            pulse: Math.random() * Math.PI * 2,
        }));
    }

    function draw() {
        ctx.clearRect(0, 0, w, h);

        bubbles.forEach((b) => {
            b.x += b.vx;
            b.y += b.vy;
            b.pulse += 0.02;
            if (b.y < -10) { b.y = h + 10; b.x = Math.random() * w; }
            if (b.x < -10) b.x = w + 10;
            if (b.x > w + 10) b.x = -10;

            const a = b.alpha * (0.5 + 0.5 * Math.sin(b.pulse));
            ctx.beginPath();
            ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(77, 168, 218, ${a * 0.7})`;
            ctx.fill();
        });

        // Connection lines
        for (let i = 0; i < bubbles.length; i++) {
            for (let j = i + 1; j < bubbles.length; j++) {
                const dx = bubbles[i].x - bubbles[j].x;
                const dy = bubbles[i].y - bubbles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(bubbles[i].x, bubbles[i].y);
                    ctx.lineTo(bubbles[j].x, bubbles[j].y);
                    ctx.strokeStyle = `rgba(92, 184, 178, ${0.025 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(draw);
    }

    resize();
    createBubbles();
    draw();
    window.addEventListener("resize", () => { resize(); createBubbles(); });
}

/* ── 2. Scroll Animations ──────────────────────────────── */
function initScrollAnimations() {
    const obs = new IntersectionObserver(
        (entries) => entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("visible"); }),
        { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );
    document.querySelectorAll(".animate-on-scroll").forEach((el) => obs.observe(el));
}

/* ── 3. Navbar ─────────────────────────────────────────── */
function initNavbar() {
    const nav = document.getElementById("navbar");
    window.addEventListener("scroll", () => nav.classList.toggle("scrolled", window.scrollY > 40));

    // Smooth scroll for nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(link.getAttribute('href'));
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });
}

/* ── 4. Load Model Info ────────────────────────────────── */
async function loadModelInfo() {
    // Model info loads silently - no UI display needed
}

/* ── 5. Charts ─────────────────────────────────────────── */
function initCharts() {
    buildDistributionChart();
    buildHealthRiskChart();
}

function chartDefaults() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { labels: { color: "#7b9bb5", font: { family: "'Outfit'" } } },
        },
        scales: {
            x: { ticks: { color: "#4a6a80", font: { family: "'Outfit'" } }, grid: { color: "rgba(255,255,255,0.04)" } },
            y: { ticks: { color: "#4a6a80", font: { family: "'Outfit'" } }, grid: { color: "rgba(255,255,255,0.04)" } },
        },
    };
}

function buildDistributionChart() {
    const ctx = document.getElementById("fluoride-distribution-chart");
    if (!ctx) return;

    // Simulated distribution based on typical Bengaluru data
    const labels = ["0-0.3", "0.3-0.6", "0.6-0.8", "0.8-1.0", "1.0-1.2", "1.2-1.5", "1.5-2.0", ">2.0"];
    const values = [35, 95, 120, 85, 60, 50, 40, 15];
    const colors = values.map((_, i) => i < 4 ? "rgba(67, 233, 123, 0.7)" : i < 6 ? "rgba(245, 158, 11, 0.7)" : "rgba(239, 68, 68, 0.7)");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Number of Readings",
                data: values,
                backgroundColor: colors,
                borderColor: colors.map((c) => c.replace("0.7", "1")),
                borderWidth: 1,
                borderRadius: 6,
            }],
        },
        options: {
            ...chartDefaults(),
            plugins: {
                ...chartDefaults().plugins,
                annotation: {
                    annotations: {
                        whoLine: { type: "line", xMin: 5.5, xMax: 5.5, borderColor: "#f59e0b", borderWidth: 2, borderDash: [5, 5] },
                    },
                },
            },
            scales: {
                ...chartDefaults().scales,
                x: { ...chartDefaults().scales.x, title: { display: true, text: "Fluoride Concentration (mg/L)", color: "#7b9bb5" } },
                y: { ...chartDefaults().scales.y, title: { display: true, text: "Number of Readings", color: "#7b9bb5" } },
            },
        },
    });
}

function buildHealthRiskChart() {
    const ctx = document.getElementById("health-risk-chart");
    if (!ctx) return;

    new Chart(ctx, {
        type: "line",
        data: {
            labels: ["0", "0.5", "1.0", "1.5", "2.0", "3.0", "4.0", "5.0+"],
            datasets: [
                {
                    label: "Dental Fluorosis Risk",
                    data: [0, 5, 15, 40, 60, 75, 85, 90],
                    borderColor: "#facc15",
                    backgroundColor: "rgba(250, 204, 21, 0.1)",
                    fill: true, tension: 0.4, borderWidth: 2,
                },
                {
                    label: "Skeletal Fluorosis Risk",
                    data: [0, 0, 2, 8, 15, 35, 65, 85],
                    borderColor: "#ef4444",
                    backgroundColor: "rgba(239, 68, 68, 0.08)",
                    fill: true, tension: 0.4, borderWidth: 2,
                },
                {
                    label: "Neurological Risk",
                    data: [0, 0, 5, 12, 25, 45, 60, 70],
                    borderColor: "#a855f7",
                    backgroundColor: "rgba(168, 85, 247, 0.08)",
                    fill: true, tension: 0.4, borderWidth: 2,
                },
            ],
        },
        options: {
            ...chartDefaults(),
            scales: {
                ...chartDefaults().scales,
                x: { ...chartDefaults().scales.x, title: { display: true, text: "Fluoride (mg/L)", color: "#7b9bb5" } },
                y: { ...chartDefaults().scales.y, title: { display: true, text: "Risk Level (%)", color: "#7b9bb5" }, max: 100 },
            },
        },
    });
}



/* ── 6. Form ───────────────────────────────────────────── */
function initForm() {
    const form = document.getElementById("predict-form");
    const btn = document.getElementById("predict-btn");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        btn.classList.add("loading");
        btn.disabled = true;

        const payload = {
            ph: parseFloat(document.getElementById("ph").value),
            ec: parseFloat(document.getElementById("ec").value),
            temperature: parseFloat(document.getElementById("temperature").value),
            hardness: parseFloat(document.getElementById("hardness").value),
        };

        try {
            const res = await fetch("/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            if (data.success) showResult(data);
            else alert("Error: " + (data.error || "Unknown error"));
        } catch (err) {
            alert("Network error.");
            console.error(err);
        } finally {
            btn.classList.remove("loading");
            btn.disabled = false;
        }
    });
}

/* ── 7. Display Result ─────────────────────────────────── */
function showResult(data) {
    document.getElementById("result-placeholder").style.display = "none";
    const content = document.getElementById("result-content");
    content.style.display = "block";
    content.className = "result-content show";

    document.getElementById("result-timestamp").textContent = data.timestamp;

    // Water gauge level
    const maxVal = 2.0;
    const pct = Math.min(data.fluoride / maxVal, 1) * 100;
    const gaugeWater = document.getElementById("gauge-water");
    const gaugeNumber = document.getElementById("gauge-value");

    // Set color based on status
    let color;
    if (data.status === "NORMAL") {
        color = "#43e97b";
        gaugeWater.style.background = "linear-gradient(180deg, #43e97b, rgba(67,233,123,0.3))";
    } else if (data.status === "BORDERLINE") {
        color = "#f59e0b";
        gaugeWater.style.background = "linear-gradient(180deg, #f59e0b, rgba(245,158,11,0.3))";
    } else {
        color = "#ef4444";
        gaugeWater.style.background = "linear-gradient(180deg, #ef4444, rgba(239,68,68,0.3))";
    }

    gaugeWater.style.height = pct + "%";
    gaugeNumber.style.color = color;
    animateNumber(gaugeNumber, 0, data.fluoride, 1200);

    // Status badge
    const badge = document.getElementById("status-badge");
    badge.className = `status-badge ${data.status === "NORMAL" ? "normal" : data.status === "BORDERLINE" ? "borderline" : "exceeds"}`;
    document.getElementById("status-text").textContent = data.status_label;

    // Remediation alert
    const alert = document.getElementById("remediation-alert");
    if (data.status === "NORMAL") {
        alert.style.display = "none";
    } else {
        alert.style.display = "block";
        alert.className = "remediation-alert " + (data.status === "BORDERLINE" ? "warning-alert" : "danger-alert");
        document.getElementById("alert-title").textContent =
            data.status === "BORDERLINE" ? "Caution — Approaching Unsafe Level" : "⛔ Danger — Fluoride Exceeds Safe Limit";
        document.getElementById("alert-desc").textContent =
            data.status === "BORDERLINE"
                ? `Fluoride at ${data.fluoride} mg/L is nearing the BIS limit. Consider these preventive steps:`
                : `Fluoride at ${data.fluoride} mg/L exceeds safe limits. Take immediate action:`;
    }

    document.getElementById("result-card").scrollIntoView({ behavior: "smooth", block: "center" });
}

function animateNumber(el, start, end, duration) {
    const t0 = performance.now();
    const diff = end - start;
    function step(t) {
        const p = Math.min((t - t0) / duration, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = (start + diff * eased).toFixed(2);
        if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

/* ── 8. Presets ────────────────────────────────────────── */
function initPresets() {
    document.querySelectorAll(".preset-chip").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.getElementById("ph").value = btn.dataset.ph;
            document.getElementById("ec").value = btn.dataset.ec;
            document.getElementById("temperature").value = btn.dataset.temp;
            document.getElementById("hardness").value = btn.dataset.hardness;
            updateRanges();
            btn.style.transform = "scale(0.95)";
            setTimeout(() => (btn.style.transform = ""), 150);
        });
    });
}

/* ── 9. Input Range Indicators ─────────────────────────── */
function initInputRanges() {
    ["ph", "ec", "temperature", "hardness"].forEach((id) => {
        document.getElementById(id).addEventListener("input", updateRanges);
    });
}

function updateRanges() {
    const ph = parseFloat(document.getElementById("ph").value) || 0;
    const ec = parseFloat(document.getElementById("ec").value) || 0;
    const temp = parseFloat(document.getElementById("temperature").value) || 0;
    const hard = parseFloat(document.getElementById("hardness").value) || 0;

    setRange("ph-range", ph, 0, 14);
    setRange("ec-range", ec, 0, 1500);
    setRange("temp-range", temp, 10, 40);
    setRange("hard-range", hard, 0, 600);
}

function setRange(id, val, min, max) {
    const el = document.getElementById(id);
    if (el) el.style.width = Math.min(100, Math.max(0, ((val - min) / (max - min)) * 100)) + "%";
}
