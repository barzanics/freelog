$(document).ready(function() {
    let hamburgerBtn = $('.hamburger-btn')
    let sidebarEl = $('.profile-sidebar')
    let overlay = $('.overlay')

    hamburgerBtn.on('click', function () {
        sidebarEl.toggleClass('show')
        if (sidebarEl.hasClass('show')) {
            overlay.addClass('show')
        } else {
            overlay.removeClass('show')
        }
    })

    overlay.on('click', function () {
        if (sidebarEl.hasClass('show')) {
            sidebarEl.removeClass('show')
            $(this).removeClass('show')
        }
    })
})

/* Main section fix the height start */
$(document).ready(function () {
    mainHeightApply();
});
function mainHeightApply(...extraElements) {
    var tag = document.createElement("div");
    tag.id = "control-height";
    tag.style.height = "100vh";
    tag.style.width = "0";
    tag.style.position = "absolute";
    document.body.appendChild(tag);

    const actualHeight = window.innerHeight;
    const elementHeight = document.querySelector("#control-height").clientHeight;

    const barHeight = elementHeight - actualHeight;
    var extraHeights = 0;
    extraElements.forEach((element) => {
        if (element && element.css("display") !== "none" && element.outerHeight()) {
            extraHeights += element.outerHeight();
        }
    });
    
    $(".profile-body-content").css("padding-bottom", extraHeights + barHeight + 8 + "px");
    document.body.removeChild(tag);
}

$(window).on("resize", function () {
    mainHeightApply();
});