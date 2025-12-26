$(function() {
    /*global Fireworks*/

    function showFireworks() {
        const overlay = document.createElement("div");
        overlay.id = "fireworks-overlay";
        overlay.style.position = "fixed";
        overlay.style.top = "0";
        overlay.style.left = "0";
        overlay.style.width = "100vw";
        overlay.style.height = "100vh";
        overlay.style.zIndex = "9999";
        overlay.style.pointerEvents = "none";
        overlay.style.background = "rgba(0, 0, 0, 0.5)";
        document.body.appendChild(overlay);

        requestAnimationFrame(() => overlay.classList.add("show"));

        document.body.style.overflow = "hidden";

        const FireworksDefault = Fireworks.default;
        const fireworks = new FireworksDefault(overlay, {
            autoresize: true,
            opacity: 0.5,
            acceleration: 1.03,
            friction: 0.99,
            gravity: 1.5,
            particles: 200,
            traceLength: 3,
            traceSpeed: 10,
            explosion: 6,
            intensity: 30,
            flickering: 50,
            lineStyle: "round",
            hue: { min: 0, max: 360 },
            delay: { min: 30, max: 40 },
            rocketsPoint: { min: 50, max: 50 },
            lineWidth: { explosion: { min: 1, max: 4 }, trace: { min: 0.1, max: 1 } },
            brightness: { min: 50, max: 80 },
            decay: { min: 0.015, max: 0.03 },
            mouse: { click: false, move: false, max: 1 },
            sound: {
                enabled: true,
                volume: { min: 2, max: 4 },
                files: [
                    "static/themes/new_years/explosion0.mp3",
                    "static/themes/new_years/explosion1.mp3",
                    "static/themes/new_years/explosion2.mp3"
                ],
            }
        });
        fireworks.start();

        setTimeout(() => {
            fireworks.waitStop();
            overlay.classList.remove("show");
            overlay.addEventListener("transitionend", () => {
                overlay.remove();
                document.body.style.overflow = "";
            }, { once: true });
        }, 5000);
    }

    function markAsSeen() {
        $.cookie("new-years-fireworks-seen", "1", { expires: 31, path: "/" });
    }

    const hasSeenFireworks = $.cookie("new-years-fireworks-seen") === "1";
    if (!hasSeenFireworks) {
        showFireworks();
        markAsSeen();
    }

    $(document).on("keydown", function(e) {
        if (e.ctrlKey && e.key === "b") {
            e.preventDefault();
            showFireworks();
        }
    });
});
