$(function() {
    $(".meme-options .meme-option").click(function() {
        var was_selected = $(this).hasClass("selected");
        var this_id = $(this).attr("data-meme");
        $(".meme-options .meme-option").removeClass("selected");
        if(was_selected) {
            $(".meme-submit").prop("disabled", "disabled");
            return;    
        }
        $(this).addClass("selected");
        $(".meme-hidden").attr("value", this_id);
        $(".meme-submit").prop("disabled", "");
    });

    $(".get-memes").click(function(e) {
        e.preventDefault();
        $(this).html("Getting memes...");
        var btn = $(this);
        var form = $(this).parent().parent();
        var endpoint = form.attr("data-get-memes");
        $.get(endpoint, {}, function(resp) {
            var res = JSON.parse(resp);
            console.log(res);
            var html = "";
            for(var i=0; i<res.length; i++) {
                html += '<div class="meme-option" style="background-image: url(' + res[i]["url"] + ')" data-meme="' + res[i]["id"] + '"></div>';
            }
            $(".meme-options", form).html(html);
            btn.html('<i class="fa fa-refresh"></i> Get more memes');
        }, "text");
    })
})