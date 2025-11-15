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

(function () {
    var gridNav = document.querySelector("[data-grid-nav]");
    if (!gridNav) {
        return;
    }

    var scroller = gridNav.querySelector("[data-grid-nav-scroll]");
    if (!scroller) {
        return;
    }

    var buttons = gridNav.querySelectorAll("[data-grid-nav-btn]");

    var scrollByAmount = function (direction) {
        var distance = scroller.clientWidth * 0.9 * direction;
        if (typeof scroller.scrollBy === "function") {
            scroller.scrollBy({ left: distance, behavior: "smooth" });
        } else {
            scroller.scrollLeft += distance;
        }
    };

    Array.prototype.forEach.call(buttons, function (button) {
        button.addEventListener("click", function () {
            var direction = button.getAttribute("data-grid-nav-btn") === "prev" ? -1 : 1;
            scrollByAmount(direction);
        });
    });

    var prevButton = gridNav.querySelector("[data-grid-nav-btn='prev']");
    var nextButton = gridNav.querySelector("[data-grid-nav-btn='next']");

    var updateButtonState = function () {
        var maxScrollLeft = scroller.scrollWidth - scroller.clientWidth - 1;
        var atStart = scroller.scrollLeft <= 1;
        var atEnd = scroller.scrollLeft >= maxScrollLeft;

        if (prevButton) {
            prevButton.disabled = atStart;
        }
        if (nextButton) {
            nextButton.disabled = atEnd;
        }
    };

    var debounceTimeout;
    var debouncedUpdate = function () {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(updateButtonState, 100);
    };

    scroller.addEventListener("scroll", debouncedUpdate);
    window.addEventListener("resize", debouncedUpdate);
    updateButtonState();
})();

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

// Lets users press "/" key to focus the search bar
document.addEventListener('keydown', function(event) {
  if ((event.key === '/') && $('input:focus, textarea:focus').length === 0) {
    event.preventDefault();

    const searchInput = document.getElementById('search-2');
    searchInput.setSelectionRange(0, searchInput.value.length);
    searchInput.focus();
  }
});
