$(".messages li a").click(function() {
    $(this).parent().fadeOut();
    return false;
});


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// make the rotating nav a bit more mobile friendly.
var width = $(window).width();
var activeCount = 5;
if(width < 650){
    activeCount = 2;
    $(".rotatingnav-inner>.item").css("width", "45%")

}
else if(width < 700){
    activeCount = 3;
    $(".rotatingnav-inner>.item").css("width", "30%")

}
$(".rotatingnav").rotatingnav({
    panelCount: 14,
    activeCount: activeCount
});

$('input#id_q_p').click(function() {
    $("input#id_q_p").val('');
});
$('input#id_q_p').keyup(function() {
    if ($("input#id_q_p").val().length){
      $("#search_button").removeClass("btn-default").addClass("btn-success");
    } else {
      $("#search_button").removeClass("btn-success").addClass("btn-default");
    }
});

// initialize scrollable
$(".scrollable").scrollable();

$(".topbar").topBar({
  slide: false
});
