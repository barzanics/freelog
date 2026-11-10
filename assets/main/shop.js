/* Loading Area Start */
function hideLoader() {
    $(".shp-loader").removeClass("show");
}
$(document).ready(hideLoader);
/* Loading Area End */

/**
 * Menu andicator line
 */
$(document).ready(function() {
    var navLineDiv = document.querySelector(".shp-main-nav-line")
    var navListItems = document.querySelectorAll(".shp-main-nav>ul>li")

    function indicator(e) {
        navLineDiv.style.left = e.offsetLeft + "px";
        navLineDiv.style.width = e.offsetWidth + "px";
        navLineDiv.style.transform = "scaleX(100%)";
    }

    navListItems.forEach(item => {
        item.addEventListener("mouseenter", (e) => {
            indicator(e.target);
        });
        item.addEventListener("mouseleave", (e) => {
            navLineDiv.style.transform = "scaleX(0%)";
        })
    })
})
function scrollToTop(selector = null) {
    if (typeof selector === "string") {
        $(selector).animate({ scrollTop: 0 }, "slow");
    } else {
        $("html, body").animate({ scrollTop: 0 }, "fast");
    }
}

/**
 * Navbar
*/
function toggleMenuBar() {
    $(".shp-main-nav-absolute").toggleClass("slideLeft")
    $(".shp-main-nav-overlay").toggleClass("show")
}

$(document).ready(function () {
    $("[data-back-menu]").click(function() {
        $("nav.shp-main-nav").removeClass("overflow-hidden")
        $(".shp-list-mega-content").removeClass("show")
        $(this).parent(".shp-list-mega-show[data-menu-show]").removeClass("show")
    })
    setMenuResponsive()
    function setMenuResponsive() {
        $(".shp-list-item-mega").unbind("mouseenter")
        $(".shp-list-item-mega").unbind("mouseleave")
        $(".shp-list-item-mega a").unbind("click")
        $(".shp-main-nav-overlay").unbind("click")
        $(".shp-list-mega-wrapper").unbind("click")
        $(".shp-list-mega-wrapper").unbind("mouseenter")
        $("nav.shp-main-nav li a").unbind("mouseenter")
        if ($(window).width() > 1200)
            {
                $(".shp-main-nav-absolute").removeClass("slideLeft")
                $(".shp-main-nav-overlay").removeClass("show")
                $(".shp-main-nav-absolute").removeClass("slideUp")
                $("nav.shp-main-nav").removeClass("overflow-hidden")

                $(".shp-list-item-mega").on("mouseenter",function() {
                    if ($(".shp-header-search-box").hasClass("show")) {
                        $(".shp-header-search-box").removeClass("show")
                        $(".overlay").removeClass("show")
                    }
                    $(".shp-main-nav-overlay").addClass("show")
                }).on("mouseleave",function() {
                    $(".shp-main-nav-overlay").removeClass("show")
                })

                $("nav.shp-main-nav li a").on("mouseenter", function() {
                    if ($(".shp-header-search-box").hasClass("show")) {
                        $(".shp-header-search-box").removeClass("show")
                        $(".overlay").removeClass("show")
                    }
                })

                /**
                 * Hovering each menu item
                 */
                $(".shp-list-mega-wrapper").find("li[data-menu-id]").each(function () {
                    $(this).on("mouseenter", function () {
                        const id = $(this).data("menu-id")
                        $(this).addClass("active").siblings("li[data-menu-id]").removeClass("active")
                        $(".shp-list-mega-show[data-menu-show='" + id + "']").addClass("show").siblings("[data-menu-show]").removeClass("show")
                    })
                })

                /**
                 * Scroll to toggle menu
                 */
                var lastScrollTop=0;
                $(".shp-body-content").on("scroll", (event) => {

                    if ($(".shp-body-content").scrollTop() > lastScrollTop && $(".shp-body-content").scrollTop() > 300 && !document.querySelector('.shp-main-nav-absolute:hover')) {
                        $(".shp-main-nav-absolute").addClass("slideUp")
                        $(".shp-product-nav").addClass("slideUp")
                        $(".shp-product-sticky-box").addClass("slideUp")
                    } else {
                        $(".shp-main-nav-absolute").removeClass("slideUp")
                        $(".shp-product-nav").removeClass("slideUp")
                        $(".shp-product-sticky-box").removeClass("slideUp")
                    }
                    lastScrollTop = $(".shp-body-content").scrollTop()
                })

                $(".my-body-content").on("scroll", (event) => {

                    if ($(".my-body-content").scrollTop() > lastScrollTop && $(".my-body-content").scrollTop() > 300 && !document.querySelector('.shp-main-nav-absolute:hover')) {
                        $(".shp-main-nav-absolute").addClass("slideUp")
                        $(".shp-product-nav").addClass("slideUp")
                        $(".shp-product-sticky-box").addClass("slideUp")
                    } else {
                        $(".shp-main-nav-absolute").removeClass("slideUp")
                        $(".shp-product-nav").removeClass("slideUp")
                        $(".shp-product-sticky-box").removeClass("slideUp")
                    }
                    lastScrollTop = $(".my-body-content").scrollTop()
                })

            } 
        else 
            {
                $(".shp-main-nav-absolute").removeClass("slideLeft")
                $(".shp-main-nav-overlay").removeClass("show")
                $(".shp-main-nav-absolute").removeClass("slideUp")
                $("nav.shp-main-nav").removeClass("overflow-hidden")
                $(".shp-list-item-mega a").on("click",function() {
                    if ($(this).parent(".shp-list-item-mega").hasClass("show")) {
                        $(this).parent(".shp-list-item-mega").removeClass("show").siblings(".shp-list-item-mega").removeClass("show")
                    } else {
                        $(this).parent(".shp-list-item-mega").addClass("show").siblings(".shp-list-item-mega").removeClass("show")
                    }
                })
                $(".shp-main-nav-overlay").on("click", toggleMenuBar)
                
                /**
                 * Clicking each menu item
                 */
                $(".shp-list-mega-wrapper").find("li[data-menu-id]").each(function () {
                    $(this).on("click",function() {
                        const id = $(this).data("menu-id")
                        $(this).addClass("active").siblings("li[data-menu-id]").removeClass("active")
                        $(".shp-list-mega-content").addClass("show")
                        $("nav.shp-main-nav").addClass("overflow-hidden")
                        $(".shp-list-mega-show[data-menu-show='" + id + "']").addClass("show").siblings("[data-menu-show]").removeClass("show")
                    })
                })

            }
    }
    $(window).on("resize", setMenuResponsive)
})

/**
 * Search X button
 */
$(document).ready(function() {
    const clearButton = $('input::after');

    clearButton.on('click', () => {
        searchInput.val("")
    });
})

function showByCheckbox(checkboxName, showDivId = "", hideDivId = "") {
    var value = "";
    $(document).ready(function() {
        value = $(`[name=${checkboxName}]:checked`).val() ?? ""
        if ($(`[name=${checkboxName}]`)[0]?.checked) {
            if (showDivId.length) $("#"+showDivId).removeClass("hide")
            else if (value.length) $("#"+value).removeClass("hide")
        } else {
            if (showDivId.length) $("#"+showDivId).addClass("hide")
            else if (value.length) $("#"+value).addClass("hide")
        }
    })
    $(`[name=${checkboxName}]`).on("change", function(e) {
        value = e.target.value
        if (e.target.checked) {
            if (showDivId.length) $("#"+showDivId).removeClass("hide")
            else if (value.length) $("#"+value).removeClass("hide")
            if (hideDivId.length) $("#"+hideDivId).addClass("hide")
        } else {
            if (showDivId.length) $("#"+showDivId).addClass("hide")
            else if (value.length) $("#"+value).addClass("hide")
            if (hideDivId.length) $("#"+hideDivId).removeClass("hide")
        }
    })
}

function toggleByRadio(radioName, divId = "") {
    var value = "";
    $(document).ready(function() {
        value = $(`[name=${radioName}]:checked`).val() ?? ""
        if ($(`[name=${radioName}]`)[0]?.checked) {
            if (divId.length) $("#"+divId).removeClass("hide")
            else {
                $(`[name=${radioName}]`).each(function() { 
                    if ($(this).is(":checked")) {
                        if ($(this).val()) $("#"+$(this).val()).removeClass("hide")
                    } else {
                        if ($(this).val()) $("#"+$(this).val()).addClass("hide")
                    }
                })
            }
        } else {
            if (divId.length) $("#"+divId).addClass("hide")
            else {
                $(`[name=${radioName}]`).each(function() { 
                    if ($(this).is(":checked")) {
                        if ($(this).val()) $("#"+$(this).val()).removeClass("hide")
                    } else {
                        if ($(this).val()) $("#"+$(this).val()).addClass("hide")
                    }
                })
            }
        }
    })
    $(`[name=${radioName}]`).on("change", function(e) {
        if (e.target.checked) {
            if (divId.length) $("#"+divId).removeClass("hide")
            else {
                $(`[name=${radioName}]`).each(function() { 
                    if ($(this).is(":checked")) {
                        if ($(this).val()) $("#"+$(this).val()).removeClass("hide")
                    } else {
                        if ($(this).val()) $("#"+$(this).val()).addClass("hide")
                    }
                })
            }
        } else {
            if (divId.length) $("#"+divId).addClass("hide")
            else {
                $(`[name=${radioName}]`).each(function() { 
                    if ($(this).is(":checked")) {
                        if ($(this).val()) $("#"+$(this).val()).removeClass("hide")
                    } else {
                        if ($(this).val()) $("#"+$(this).val()).addClass("hide")
                    }
                })
            }
        }
    })
}

function scrollToId(element){   
    var ele = document.getElementById(element); 
    $(".shp-body-content").animate({ scrollTop: ele.offsetTop }, "fast");
}

function setClearBtn(id) {
    $("#"+id).on("input", function(e) {
        if (e.target.value.length > 0) {
            if (!$("#"+id).parent().find(".shp-clear-btn").length) {
                $("#"+id).parent().append(`
                <button class="g-center shp-clear-btn" onclick="clearInput('${id}')">
                    <i class="fa fa-xmark-circle fw-bold fs-16"></i>
                </button>`)
            }
        } else {
            $("#"+id).parent().find(".shp-clear-btn").remove()
        }
    })
}
function clearInput(id) {
    $("#"+id).val("")
    $(event.target).parents(".shp-clear-btn").remove()
    $(event.target).remove()
    $("#"+id).focus()
}

function shpUploadFile(id) {
    document.getElementById(id).click();
}

function setUploadableBox(inputSelector, contentSelector, processUploadedFile) {
    var isAdvancedUpload = function() {
        var div = document.createElement('div');
        return (('draggable' in div) || ('ondragstart' in div && 'ondrop' in div)) && 'FormData' in window && 'FileReader' in window;
    }();

    var form = document.querySelector(contentSelector);
    // Check if the browser supports advanced file upload features
    if (isAdvancedUpload) {
        form.className += " has-advanced-upload";

        // Add event listeners for drag and drop
        form.addEventListener('dragover', function(e) {
            e.preventDefault();
            // Highlight the drop area
            // Add any visual effects you want
        });

        form.addEventListener('dragleave', function(e) {
            e.preventDefault();
            // Remove any visual effects
        });

        form.addEventListener('drop', function(e) {
            e.preventDefault();
            // Handle the dropped file(s)
            var files = e.dataTransfer.files;
            // Process the files (e.g., upload to server)                                                                            
            processUploadedFile(files)
        });
    }

    var uploadInput = document.querySelector(inputSelector)
    uploadInput.addEventListener("change", function() {
        processUploadedFile(uploadInput.files)
    })
}

/**
 * Chunk Divs
 */
$(document).ready(function() {
    $("[data-chunk]").each(function() {
        const config = JSON.parse($(this).attr('data-chunk'))
        const count = config.count,
            classes = config.classes,
            children = $(this).children()

        const chunkSize = Math.ceil(children.length / count);

        const newChildren = Array.from(
            { length: count },
            (_, i) => children.slice(i * chunkSize, (i + 1) * chunkSize)
        );
        $(this).html("")
        newChildren.forEach(children => {
            var parentDiv = $(`<div class="${classes}">`)
            parentDiv.append(children)
            $(this).append(parentDiv)
        })                                                                
    })
})