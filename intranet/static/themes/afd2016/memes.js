$(function() {
    memeBinds = function() {
        $(".meme-options .meme-option").click(function() {
            var was_selected = $(this).hasClass("selected");
            $(".meme-options .meme-option").removeClass("selected");

            if (was_selected) {
                $(".meme-submit").prop("disabled", true);
                return;
            }

            var this_id = $(this).attr("data-meme");

            $(this).addClass("selected");
            $(".meme-hidden").val(this_id);
            $(".meme-submit").prop("disabled", false);
        });
    }

    memeBinds();

    $(".get-memes").click(function(e) {
        e.preventDefault();
        $(this).html("Getting memes...");
        var btn = $(this);
        var form = $(this).parent().parent();
        var endpoint = form.attr("data-get-memes");

        $.getJSON(endpoint, {}, function(res) {
            console.log(res);
            var html = "";

            for (var i = 0; i < res.length; i++) {
                html += '<div class="meme-option" style="background-image: url(' + res[i].url + ')" data-meme="' + res[i].id + '"></div>';
            }

            $(".meme-options", form).html(html);
            btn.html('<i class="fa fa-refresh"></i> Get more memes');
            memeBinds();
        });
    });
});
