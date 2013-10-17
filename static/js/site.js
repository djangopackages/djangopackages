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


$(".rotatingnav").rotatingnav({
    panelCount: 14,
    activeCount: 5
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