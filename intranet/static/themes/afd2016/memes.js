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
})