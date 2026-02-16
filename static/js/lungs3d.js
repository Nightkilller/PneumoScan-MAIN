/* ══════════════════════════════════════════════════════════
   PneumoScan — 3D Lungs Glow Controller (Sketchfab Embed)
   ═══════════════════════════════════════════════════════════ */

window.PneumoLungs = (() => {
    const overlay = document.getElementById("lungGlowOverlay");

    function setGlow(color) {
        overlay.classList.remove("glow-blue", "glow-red");
        if (color === "blue") overlay.classList.add("glow-blue");
        else if (color === "red") overlay.classList.add("glow-red");
    }

    function resetGlow() {
        overlay.classList.remove("glow-blue", "glow-red");
    }

    // Default: subtle blue glow on load
    setTimeout(() => setGlow("blue"), 2000);

    return { setGlow, resetGlow };
})();
