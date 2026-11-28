$(function() {
    // One in 10 chance of a hair appearing on the page
    if (Math.random() < 0.1) {
        const hairElem = $(`<div class="hair"><div class="hair-click"></div></div>`)
        $("body").append(hairElem);

        // Randomly position the hair
        const width = Math.random() * 8 + 2;
        const height = Math.random() * 6 + 2;
        const top = Math.min(Math.random() * 100, 80 - height);
        const left = Math.min(Math.random() * 100, 80 - width);
        const angle = Math.random() * 360;
        hairElem.css({
            width: `${width}vw`,
            height: `${height}vh`,
            "margin-bottom": `${-height}vh`,
            top: `${top}vh`,
            left: `${left}vw`,
            transform: `rotate(${angle}deg)`,
        });

        // Popup configuration
        const alertText = "Happy April Fools' Day!<br />&ensp;- Your Friendly Neighborhood Sysadmins";
        const hairClickElem = hairElem.find(".hair-click");
        let hairClickHoverTimer = null;
        function sendHairMessage() {
            if(window.Messenger) {
                const hairMessage = Messenger().info({
                    message: alertText,
                    hideAfter: 5,
                    showCloseButton: false
                });
            }
        }

        // Popup on click
        hairClickElem.on("click", () => {
            if (hairClickHoverTimer) {
                clearTimeout(hairClickHoverTimer);
                hairClickHoverTimer = null;
            }
            sendHairMessage();
        });

        // Popup on hover for 1.5 seconds
        hairClickElem.hover(() => {
            hairClickHoverTimer = setTimeout(() => {
                hairClickHoverTimer = null;
                sendHairMessage();
            }, 1500);
        }, () => {
            if (hairClickHoverTimer) {
                clearTimeout(hairClickHoverTimer);
                hairClickHoverTimer = null;
            }
        });
    }
});
