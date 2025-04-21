document.addEventListener("DOMContentLoaded", () => {
    const $toggleBar  = $(".senior-dests-toggle");
    const $contentBox = $(".senior-dests-content");

    if (!$toggleBar.length || !$contentBox.length) {return;}

    const $expandBtn   = $toggleBar.find(".senior-dests-expand");
    const $collapseBtn = $contentBox.find(".senior-dests-collapse");

    $expandBtn.on("click", () => {
        $contentBox.stop(true, true).slideDown(200).addClass("open");
        $toggleBar.hide();
    });

    $collapseBtn.on("click", () => {
        $contentBox.stop(true, true).slideUp(200, () => {
            $contentBox.removeClass("open");
            $toggleBar.show();
        });
    });
});