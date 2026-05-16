(function () {
    function ready(fn) {
        if (document.readyState !== "loading") {
            fn();
        } else {
            document.addEventListener("DOMContentLoaded", fn);
        }
    }

    ready(function () {
        var shell = document.querySelector(".wrapped-shell");
        if (!shell) {
            return;
        }

        var cards = Array.prototype.slice.call(document.querySelectorAll(".wrapped-card"));
        var progress = Array.prototype.slice.call(document.querySelectorAll(".wrapped-progress__item"));
        var prev = document.querySelector(".wrapped-nav--prev");
        var next = document.querySelector(".wrapped-nav--next");
        var index = 0;

        function animateNumbers(card) {
            Array.prototype.slice.call(card.querySelectorAll("[data-count-to]")).forEach(function (node) {
                var target = parseInt(node.getAttribute("data-count-to"), 10);
                if (!Number.isFinite(target) || target > 9999 || node.dataset.done === "1") {
                    return;
                }
                node.dataset.done = "1";
                var start = performance.now();
                var duration = 1000;
                function tick(now) {
                    var progressValue = Math.min((now - start) / duration, 1);
                    node.textContent = Math.round(target * (1 - Math.pow(1 - progressValue, 3)));
                    if (progressValue < 1) {
                        requestAnimationFrame(tick);
                    }
                }
                requestAnimationFrame(tick);
            });
        }

        function show(nextIndex) {
            index = Math.max(0, Math.min(cards.length - 1, nextIndex));
            cards.forEach(function (card, cardIndex) {
                card.classList.toggle("is-active", cardIndex === index);
            });
            progress.forEach(function (item, progressIndex) {
                item.classList.toggle("is-active", progressIndex <= index);
            });
            if (prev) {
                prev.disabled = index === 0;
            }
            if (next) {
                next.disabled = index === cards.length - 1;
            }
            animateNumbers(cards[index]);
        }

        function downloadCanvas(canvas) {
            var link = document.createElement("a");
            link.download = "ion-wrapped.png";
            link.href = canvas.toDataURL("image/png");
            link.click();
        }

        function exportShareCard(button) {
            var card = document.getElementById("wrapped-share-card");
            if (!card || !window.html2canvas) {
                return;
            }
            if (button) {
                button.disabled = true;
            }
            card.classList.add("wrapped-share-card--exporting");
            window.html2canvas(card, {
                backgroundColor: null,
                scale: Math.min(window.devicePixelRatio || 2, 3),
                useCORS: true,
            }).then(function (canvas) {
                downloadCanvas(canvas);
                card.classList.remove("wrapped-share-card--exporting");
                if (button) {
                    button.disabled = false;
                }
            }, function () {
                card.classList.remove("wrapped-share-card--exporting");
                if (button) {
                    button.disabled = false;
                }
            });
        }

        if (prev) {
            prev.addEventListener("click", function () { show(index - 1); });
        }
        if (next) {
            next.addEventListener("click", function () { show(index + 1); });
        }
        document.addEventListener("keydown", function (event) {
            if (event.key === "ArrowRight" || event.key === " ") {
                show(index + 1);
            } else if (event.key === "ArrowLeft") {
                show(index - 1);
            }
        });
        document.querySelector(".wrapped-stage").addEventListener("click", function (event) {
            if (event.target.closest("button") || event.target.closest("a")) {
                return;
            }
            show(index + 1);
        });

        var exportButton = document.getElementById("wrapped-export");
        if (exportButton) {
            exportButton.addEventListener("click", function () {
                exportShareCard(exportButton);
            });
        }

        show(0);
    });
}());
