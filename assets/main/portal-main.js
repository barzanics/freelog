$(document).ready(function() {
    const navbar = $("#navBar");
    const overlay = $(".overlay");
    $(document).on("click", "#hamburgerBtn", () => {
        navbar.toggleClass("show");
        if (navbar.hasClass("show")) {
            overlay.addClass("show");
        } else {
            overlay.removeClass("show");
        }
    });
    
    $(document).on("click", ".overlay", () => {
        if (navbar.hasClass("show")) {
            navbar.removeClass("show");
            overlay.removeClass("show");
        }
    });
    
    // Navigation
    $("#navBar ul li").each(function () {
        $(this).on("click", (e) => {
            if ($(e.target).closest($(this).find("ul")).length > 0) {
                // Clicked inside the container
            } else {
                // Clicked outside the container
                $(this).toggleClass("show");
                if ($(this).hasClass("show")) {
                    // $(this).children('ul').stop().slideDown();
                    $(this).siblings().removeClass("show");
                } else {
                    // $(this).children('ul').stop().slideUp();
                }
            }
        });
    });
    
    // Search
    const searchBtn = $("#searchBtn");
    const searchForm = $(".search-form");
    searchBtn.on("click", function () {
        searchForm.stop().slideToggle();
    });
    
    // Search V2
    const searchBoxBtn = $("#searchBoxBtn");
    const searchFormV2 = $(".search-form-v2");
    const closeSearchBtn = $("#closeSearchBtn");
    searchBoxBtn.on("click", function () {
        if ($("#navBar").hasClass('show')) return;
        searchFormV2.addClass("show")
    });
    closeSearchBtn.on("click", function () {
        searchFormV2.removeClass("show")
    });
    

    
    $("#back_to_top").click(function () {
        $("html, body, .main-wrapper, section.main").animate({ scrollTop: 0 }, 1);
        return false;
    });

    // When the user scrolls the page, execute myFunction
    window.onscroll = function () {
        headerSticky();
    };

    // Get the header
    var header = document.getElementById("mainHeader");

    // Get the offset position of the navbar
    var sticky = header.offsetTop;

    // Add the sticky class to the header when you reach its scroll position. Remove "sticky" when you leave the scroll position
    function headerSticky() {
        if (window.pageYOffset > sticky) {
            header.classList.add("sticky");
        } else {
            header.classList.remove("sticky");
        }
    }
})

/* Sliders */
new Swiper("#galleryImages", {
    speed: 400,
    spaceBetween: 16,
    breakpoints: {
        360: {
            slidesPerView: 1,
        },
        576: {
            slidesPerView: 2,
        },
        768: {
            slidesPerView: 3,
        },
        976: {
            slidesPerView: 3,
        },
        1200: {
            slidesPerView: 4,
        },
    },
    navigation: {
        nextEl: ".slider-btn-right",
        prevEl: ".slider-btn-left",
    },
});

// new Swiper("#newsBannerSwiper", {
//     speed: 400,
//     spaceBetween: 0,
//     slidesPerView: 1,
//     autoplay: {
//         delay: 5000,
//     },
//     allowTouchMove: false,
//     loop: true,
// });

new Swiper("#topBannerSwiper", {
    speed: 400,
    spaceBetween: 0,
    slidesPerView: 1,
    autoplay: {
        delay: 5000,
        disableOnInteraction: false,
    },
    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    },
    allowTouchMove: true,
    // loop: true,
});

/* Back to top button */
$(window).scroll(function (event) {
    if ($(this).scrollTop() > 300) {
        $("#back_to_top").addClass("show");
    } else {
        $("#back_to_top").removeClass("show");
    }
});
