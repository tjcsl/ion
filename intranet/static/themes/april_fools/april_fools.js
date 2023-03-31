$(function() {
    $('link[rel="icon"]').attr('href', '/static/themes/april_fools/april_fools_logo.png');
    $(".intranet-title h1").text("Intranet 4");
    let navbar = $("ul.nav");
    $(navbar).append($(`
        <li class="nav-chat">
            <a href="/chat">
                <i class="chat-nav-icon fas fa-comments"></i>
                ChatION
            </a>
        </li>
    `));
    $(navbar).find("li.nav-chat").click(function() {
        $(this).addClass("selected");
    });
    if(location.href.endsWith("chat")) {
        $(navbar).find("li.nav-chat").addClass("selected");
    }
    if(window.innerWidth > 768) {
        $("iframe").attr("scrolling", "no");
    }
});
