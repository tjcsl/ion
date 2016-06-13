/* global $ */
$(function() {
    Messenger.options = {
        extraClasses: "messenger-fixed messenger-on-bottom messenger-on-right",
        theme: "flat",
        messageDefaults: {
            hideAfter: 10,
            showCloseButton: true
        }
    };
});

$(function() {
    var time = 150;

    var clickInside = function(event) {
        event.stopPropagation();
    }

    var clickOutside = function(e) {
        if ($(e.target).parents().andSelf().hasClass("dropdown-allow")) return;

        if (!$(e.target).parents().andSelf().hasClass("dropdown-item-wrapper")) {
            closeMenu($(".dropdown-open .dropdown-menu"), true);
            $(".has-dropdown").removeClass("dropdown-open");
        }
    }

    var openMenu = function(menu, bindEvents) {
        menu.show();
        menu.stop().animate({
            top: "0",
            opacity: 1
        }, time, "easeInQuart", function() {
            if (bindEvents) {
                $(document).bind("click tap", clickOutside);
                $(".dropdown-menu").bind("click", clickInside);
            }
        });
    }

    var closeMenu = function(menu, unbindEvents) {
        menu.stop().animate({
            top: "10px",
            opacity: 0
        }, time, "easeOutQuart", function() {
            menu.hide();

            if (unbindEvents) {
                $(".dropdown-menu").unbind("click", clickInside);
                $(document).unbind("click tap", clickOutside);
            }
        });
    }

    $(".has-dropdown").click(function(event) {
        var menu_clicked = $(this).children(".dropdown-menu");
        var already_open = $(".dropdown-open .dropdown-menu")

        if ($(this).hasClass("dropdown-open")) {
            // Closing open menu
            closeMenu(menu_clicked);
            $(document).unbind("click tap", clickOutside);
            $(".dropdown-menu").unbind("click", clickInside);
            $(".has-dropdown").removeClass("dropdown-open");
        } else if (already_open.length === 0) {
            // All menus closed, opening one of them
            openMenu(menu_clicked, true);
            menu_clicked.parent().addClass("dropdown-open");
        } else {
            // Switching menu
            openMenu(menu_clicked, false);
            closeMenu(already_open, false);
            $(".has-dropdown").removeClass("dropdown-open");
            menu_clicked.parent().addClass("dropdown-open");
        }
    });

    arrowPosition = function() {
        // Calculate dimensions to align arrow to icons/text in header
        $(".notifications .dropdown-menu .arrow").css("right", ($(".notifications").width() / 2) + "px");
        $(".username .dropdown-menu .arrow").css("right", ((($(".username .dropdown-item-wrapper").width()) / 2) + 5) + "px");
    }

    arrowPosition();
    window.onresize = arrowPosition;
});