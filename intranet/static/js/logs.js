function goToPage(pageNum) {
    let url = window.location.href;
    if (url.includes("page=")) {
        url = url.replace(/page=\d+/, "page=" + pageNum);
    }
    else {
        url = "?page=" + pageNum + "&" + url.split("?")[1] || "";
    }
    window.location.href = url;
}

$(function() {
    $(".raw-json-header, .iframe-container-header").click(function () {
        $(this).next().slideToggle("fast");
        $(this.children[1]).toggleClass("fa-angle-up fa-angle-down");
    });
    $(".pagination a").click(function () {
        goToPage($(this).attr("data-page"));
    });
    $(".pagination form").submit(function (e) {
        e.preventDefault();
        goToPage($(this).find("input").val());
    });
});
