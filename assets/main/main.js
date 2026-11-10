const API_TOKEN =
    "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImEyZjhhYWMzYWRiNDY0ZGNkZGIyZDc1MTdhYmEzZWIyZTllZGVhNWU2MTQ5NDg0N2YxM2UxZmE2NDNkM2Y3MmM1MDEyOWQxMzMzZTcyNzVkIn0.eyJhdWQiOiIyNzA5NiIsImp0aSI6ImEyZjhhYWMzYWRiNDY0ZGNkZGIyZDc1MTdhYmEzZWIyZTllZGVhNWU2MTQ5NDg0N2YxM2UxZmE2NDNkM2Y3MmM1MDEyOWQxMzMzZTcyNzVkIiwiaWF0IjoxNzE0MDIwMjA3LCJuYmYiOjE3MTQwMjAyMDcsImV4cCI6MTcxNjYxMjIwNywic3ViIjoiIiwic2NvcGVzIjpbImJhc2ljIl19.QglmY_BC0PXU7TauXAarScVz_EFLO_EVr8hwyKjalp4LVJhSN8OZ2pBin7mANWp0KUr4Pf72w1LLEkAvNGsJsk-gzeKcd8LmBU9hdihWzNtOyI-btYRKI2-W9uXAmF1NRXFDMceH2U8bEyzfZATWqWoJRCJvPZIb8l-hvSmC7TLGQJgWEzgyF8MrN7mABfVWJu7MyNn2bMN3N4EopAVe_D8yV1VOMqhfmNfRvunSAsm-IhNLhFuRXxo7uA0m6ET8l0o_4Cw3ml5Hh5X_I9W-9b9pXbBjrl6LD4K07mJtJOaSEwZO6K4NYaPAvxeRC_SDXWM6azB9k-hIfrcIaRyfCw";
function getDomain() {
    var url = window.location.href
    const parsedUrl = new URL(url);
    const hostParts = parsedUrl.hostname.split('.');

    // Check for IP addresses
    if (hostParts.length === 4 && hostParts.every(part => /^\d+$/.test(part))) {
        return parsedUrl.hostname; // Return IP address as-is
    }

    // Check if the domain has at least two parts
    if (hostParts.length >= 2) {
        // If the last part is 'localhost', return it
        if (hostParts[hostParts.length - 1].toLowerCase() === 'localhost') {
            return 'localhost';
        }

        // Return the last two parts joined together
        return hostParts.slice(-2).join('.');
    }

    return parsedUrl.hostname; // Fallback to the full hostname if no valid domain found
}

/* Cookies Helper Start */
function setCookie(name, value, daysToExpire) {
    let expires = new Date();
    if (daysToExpire) expires.setTime(expires.getTime() + (daysToExpire * 24 * 60 * 60 * 1000));
    else expires = 'Session'
    const domain = getDomain();
    const cookie = `${name}=${encodeURIComponent(value)};${(window.location.protocol == 'http:' ? '' : 'Secure;')}expires=${expires};path=/;domain=.${domain}`;
    document.cookie = cookie;
}

function getCookie(name) {
    const cookieName = `${name}=`;
    const cookies = document.cookie.split(';');

    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith(cookieName)) {
            return decodeURIComponent(cookie.substring(cookieName.length));
        }
    }

    return null;
}

function deleteCookie(name) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
}

var aside = $("aside");
/* Design sidebar start */
var overlayElements = [];
function toggleWithOverlay(element, className, type = "toggle") {
    if (!overlayElements) overlayElements = [];
    let overlay = $(".overlay");
    var id = "";
    if (element.attr("id")) {
        id = element.attr("id");
    } else {
        id = generateId();
        element.attr("id", id);
    }
    if (type === "toggle") {
        if (element.hasClass(className)) {
            overlayElements = overlayElements.filter((elem) => elem.id != id);
            element.removeClass(className);
            overlay.removeClass("show");
        } else {
            overlayElements.push({ id, element, className });
            element.addClass(className);
            overlay.addClass("show");
        }
    } else if (type === "add") {
        overlayElements.push({ id, element, className });
        element.addClass(className);
        overlay.addClass("show");
    } else if (type === "remove") {
        overlayElements = overlayElements.filter((elem) => elem.id != id);
        element.removeClass(className);
        overlay.removeClass("show");
    }
}

function hide_sidebar() {toggleWithOverlay($('aside'),'show','remove')}
const themeCustomDarkClass = document.getElementsByTagName("html")?.[0]?.getAttribute("data-dark") || 'dark';
/* Cookies Helper end */
const classes = ["slate", "blue", "fuchsia", "emerald", "sky", "red", "yellow", "green", "purple", "pink", "indigo", themeCustomDarkClass, "orange", "yellow-blue", "slate-dark", "blue-dark", "fuchsia-dark", "emerald-dark", "sky-dark", "red-dark", "yellow-dark", "green-dark", "purple-dark", "pink-dark", "indigo-dark", "orange-dark"];
document.addEventListener("DOMContentLoaded", function () {
    var switcherThemeInput = $(".switcher-theme-input")
    switcherThemeInput.each(function() {
        // Switcher Theme
        changeTheme();
        $(this).each(function () {
            $(this).on("change", changeTheme);
        });
    })
});

function changeTheme() {
    var switcherThemeInput = $(".switcher-theme-input")
    const lightTheme = $(this).attr("value") ?? switcherThemeInput.attr('value');
    var selectedTheme = themeCustomDarkClass;
    if ($(this).length && this != window) {
        selectedTheme = !$(this).hasClass('switcher-theme-input') || $(this).is(":checked") ? lightTheme : themeCustomDarkClass;
    } else {
        selectedTheme = getCookie("theme_mode") ? getCookie("theme_mode") : (lightTheme ?? "sky")
    }
    setTimeout(() => {
        if (selectedTheme === themeCustomDarkClass) {
            switcherThemeInput.prop("checked", false)
        }
        else {
            switcherThemeInput.prop("checked", true)
        }
    }, 50);
    if (!$("body").first().hasClass(selectedTheme)) {
        const extraClasses = classes.filter((c) => c !== selectedTheme);
        $("body").addClass(selectedTheme);
        setCookie('theme_mode', selectedTheme, 2)
        extraClasses.map((c) => {
            $("body").removeClass(c);
        });
        $(document).trigger("themeChanged", {
            themeName: selectedTheme,
        });
    }
}

const lightTheme = $(".switcher-theme-input").attr("value") ?? getCookie("theme_mode");
if (getCookie("theme_mode")?.length) {
    if (getCookie("theme_mode") === lightTheme && !lightTheme.includes(themeCustomDarkClass)) {
        $(this).each(function () {
            $(".switcher-theme-input").attr("checked", "checked");
            $(".switcher-theme-input").prop('checked', true);
        });
    } else if (getCookie("theme_mode") !== lightTheme && getCookie("theme_mode") !== themeCustomDarkClass) {
        $(this).each(function () {
            $(".switcher-theme-input").attr("checked", "checked");
            $(".switcher-theme-input").prop('checked', true);
        });
    }
    else
        $(this).each(function () {
            $(".switcher-theme-input").prop('checked', false);
            $(".switcher-theme-input").removeAttr("checked");
        });
}

function defaultTheme(theme) {
    if (!$("body").hasClass(theme)) {
        const extraClasses = classes.filter((c) => c !== theme);
        $("body").addClass(theme);
        setCookie("theme_mode", theme);
        extraClasses.map((c) => {
            $("body").removeClass(c);
        });
        $(document).trigger("themeChanged", {
            themeName: theme,
        });
    }
}

/* Loading Area Start */
function hideDOMLoader() {
    $("#loading").fadeOut("slow");
}
/* Loading Area End */
$(document).ready(function () {
    window.cs = getComputedStyle(document.querySelector("body"));
    $("a").each(function () {
        if (typeof $(this).attr("href") === "undefined" || $(this).attr("href") === "#" || $(this).attr("href") === "") {
            $(this).on("click", function (e) {
                e.preventDefault();
            });
        }
    });
});

/** Process Svgs start */
async function applySvgProcess(svgElement, useElement, href) {
    if (!href?.length) return;
    try {
        const response = await fetch(href);
        const svgText = await response.text();
        svgElement.innerHTML = svgText;
    } catch(err) {
        console.log(err)
    }
}

async function initGradientDetection() {
    const svgElements = document.querySelectorAll('svg');
    let promises = []
    if (svgElements.length) {
        svgElements.forEach(svgElement => {
            const useElement = svgElement.querySelector('use');
            if (useElement) {
                const href = useElement.getAttribute('svghref') || useElement.getAttribute('xlink:svghref');
                promises.push(applySvgProcess(svgElement, useElement, href))
            }
        })
    }
    await Promise.all(promises)
}
$(document).ready(hideDOMLoader);
$(document).ready(() => {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(async node => {
                if (node.nodeName === 'SVG') {
                    const useElement = node.querySelector('use');
                    if (useElement) {
                        const href = useElement.getAttribute('svghref') || useElement.getAttribute('xlink:svghref');
                        applySvgProcess(node, useElement, href);
                    }
                } else if (typeof node.querySelectorAll == 'function') {
                    const svgElements = node.querySelectorAll('svg');
                    let promises = []
                    if (svgElements.length) {
                        svgElements.forEach(svgElement => {
                            const useElement = svgElement.querySelector('use');
                            if (useElement) {
                                const href = useElement.getAttribute('svghref') || useElement.getAttribute('xlink:svghref');
                                promises.push(applySvgProcess(svgElement, useElement, href))
                            }
                        })
                    }
                    await Promise.all(promises)
                }
            });
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });
});
document.addEventListener('DOMContentLoaded', initGradientDetection);
/** Process Svgs end */

var modalTimeout;
$(document).ready(function () {
    var modalId = 0
    var lastModalId = null
    // Function to handle the modal mount
    function handleModalMount(modal = null) {
        const showBsModal = () => {
            modalId = Date.now()
            $(".portal-header").css({
                zIndex: "1000"
            })
            $(".design-header").css({
                zIndex: "1000"
            })
            $(".my-header").css({
                zIndex: "1000"
            })
            $("aside.sidebar").css({
                zIndex: "1010"
            })
            $("nav#navBar").css({
                zIndex: "1000"
            })
            $("nav.bottom-navbar").css({
                zIndex: "1000"
            })
            $("nav.bottom-navbar-v2").css({
                zIndex: "1000"
            })
            $(".shp-header").css({
                zIndex: "1000"
            })
            $(".profile-sidebar").css({
                zIndex: "1000"
            })
        }
        const hideBsModal = () => {
            lastModalId = modalId
        }
        const hiddenBsModal = () => {
            if ($(".modal.show").length < 1) {
                // if modal have been hidden.
                if (modalId == lastModalId) {
                    $(".portal-header").css({
                        zIndex: "2750"
                    })
                    $(".design-header").css({
                        zIndex: "2700"
                    })
                    $(".my-header").css({
                        zIndex: "2700"
                    })
                    $("aside.sidebar").css({
                        zIndex: "2750"
                    })
                    $("nav#navBar").css({
                        zIndex: "2750"
                    })
                    $("nav.bottom-navbar").css({
                        zIndex: "2700"
                    })
                    $("nav.bottom-navbar-v2").css({
                        zIndex: "2700"
                    })
                    $(".shp-header").css({
                        zIndex: "2750"
                    })
                    $(".profile-sidebar").css({
                        zIndex: "2750"
                    })
                }
            }
            lastModalId = modalId
        }
        $(".modal").unbind("show.bs.modal", showBsModal);
        $(".modal").unbind("shown.bs.modal", showBsModal);
        $(".modal").unbind("hide.bs.modal", hideBsModal);
        $(".modal").unbind("hidden.bs.modal", hiddenBsModal);
        // Fix the z-index problem for modal & lightgallery start
        $(".modal").on("show.bs.modal", showBsModal).on("hide.bs.modal", hideBsModal).on("hidden.bs.modal", hiddenBsModal)
    }

    function handleLightGalleryMount(lightgallery = null) {
        $(".lightgallery").unbind("lgBeforeOpen")
        $(".lightgallery").unbind("lgAfterClose")
        $(".lightgallery").on("lgBeforeOpen", function () {
            $(".portal-header").css({
                zIndex: "1000"
            })
            $(".design-header").css({
                zIndex: "1000"
            })
            $(".my-header").css({
                zIndex: "1000"
            })
            $("aside.sidebar").css({
                zIndex: "1010"
            })
            $("nav#navBar").css({
                zIndex: "1000"
            })
            $("nav.bottom-navbar").css({
                zIndex: "1000"
            })
            $("nav.bottom-navbar-v2").css({
                zIndex: "1000"
            })
            $(".shp-header").css({
                zIndex: "1000"
            })
            $(".profile-sidebar").css({
                zIndex: "1000"
            })
        }).on("lgAfterClose", function () {
            $(".portal-header").css({
                zIndex: "2550"
            })
            $(".design-header").css({
                zIndex: "2500"
            })
            $(".my-header").css({
                zIndex: "2500"
            })
            $("aside.sidebar").css({
                zIndex: "2550"
            })
            $("nav#navBar").css({
                zIndex: "2550"
            })
            $("nav.bottom-navbar").css({
                zIndex: "2500"
            })
            $("nav.bottom-navbar-v2").css({
                zIndex: "2500"
            })
            $(".shp-header").css({
                zIndex: "2750"
            })
            $(".profile-sidebar").css({
                zIndex: "2750"
            })
        })
    }

    // Callback function for the MutationObserver
    function mutationCallback(mutationsList, observer) {
        mutationsList.forEach(mutation => {
            // Check if any nodes are added to the DOM
            mutation.addedNodes.forEach(node => {
                // Check if the added node is a modal
                if (node.classList && node.classList.contains('modal')) {
                    handleModalMount(node);
                } else if (node.classList && node.classList.contains('lightgallery')) {
                    handleLightGalleryMount(node);
                } else {
                    handleModalMount(node);
                    handleLightGalleryMount(node);
                }
            });
        });
    }

    // Create a MutationObserver instance
    const modalObserver = new MutationObserver(mutationCallback);

    // Start observing the document body for changes
    modalObserver.observe(document.body, { childList: true, subtree: true });

    handleModalMount();
    handleLightGalleryMount();
    // Fix the z-index problem end

    // Z Index modal form confilicts start
    function setTabIndexes(elements) {
        $(elements).each(function() {
            var tabindex = $(this).attr("tabindex");
            $(this).attr("tabindex", -1);
            $(this).attr("data-tabindex", tabindex);
        })
    }

    function resetTabIndexes(elements) {
        $(elements).each(function() {
            var tabindex = $(this).attr("data-tabindex");
            $(this).attr("tabindex", tabindex);
            $(this).removeAttr("data-tabindex");
        })
    }
    const handleModalTabindexConfilicts = (selector) => {
        const modals = document.querySelectorAll(selector);
        if (!modals.length) return;
        modals.forEach(modal => {
            const allElements = document.querySelectorAll('body *[tabindex]');
            $(modal).on("show.bs.modal", () => setTabIndexes(allElements));
            $(modal).on("hide.bs.modal", () => resetTabIndexes(allElements));
        })
    };

    handleModalTabindexConfilicts('.modal');

    // Z Index modal form confilicts end
})

/* Snackbar Start */
async function snackbar(id, text, type = "", userOptions = {}) {
    const defaultOptions = {
        duration: 3000,
        hasIcon: false,
        hasProgress: true,
        isConfirmed: false,
        acceptText: "بله",
        cancelText: "خیر",
        hasCancelBtn: true,
        textStyles: {
            textAlign: "center",
            fontWeight: "normal",
        },
        data: null,
        iconStyles: {},
        forceGenerate: false,
        clickToRemove: false,
        clickIconToRemove: true,
        clickOutsideToRemove: false,
    };

    const options = { ...defaultOptions, ...userOptions };
    const data = { data: options.data, isConfirmed: false };
    const startTime = Date.now();
    // Check if has force to generate snackbar
    if (options.forceGenerate) {
        if (document.getElementById(id)) id = "snackbar_element_" + generateId();
    } else {
        if (document.getElementById(id)) return;
    }
    var snackbarElem = document.createElement("div");
    snackbarElem.className = "snackbar";
    // Text inside snackbar
    var textElem = document.createElement("p");
    textElem.innerHTML = text;

    if (!options.hasProgress) snackbarElem.classList.add("hide-progress");

    var mountedToDom = false;
    if (options.clickOutsideToRemove)
        document.addEventListener("click", function (event) {
            if (!snackbarElem.contains(event.target) && mountedToDom) {
                snackbarElem.classList.add("hide-progress");
                const clickTime = Date.now();
                snackbarElem.style.setProperty("--snackbar-duration", clickTime - startTime + "ms");
                window.global_snackbar_timeout = setTimeout(() => {
                    if (!removedFromDom) {
                        removedFromDom = true;
                        snackbarElem.classList.remove("show");
                        document.body.removeChild(snackbarElem);
                        // Create event
                        snackbarElem.dispatchEvent(new Event("snackbarRemoved"));
                    }
                }, 500);
                mountedToDom = false;
            }
        });

    if (options.clickToRemove) {
        snackbarElem.addEventListener("click", () => {
            if (mountedToDom) {
                snackbarElem.classList.add("hide-progress");
                const clickTime = Date.now();
                snackbarElem.style.setProperty("--snackbar-duration", clickTime - startTime + "ms");
                window.global_snackbar_timeout = setTimeout(() => {
                    if (!removedFromDom) {
                        removedFromDom = true;
                        snackbarElem.classList.remove("show");
                        document.body.removeChild(snackbarElem);
                        // Create event
                        snackbarElem.dispatchEvent(new Event("snackbarRemoved"));
                    }
                }, 500);
                mountedToDom = false;
            }
        });
    }

    if (options.hasIcon) {
        // Icon and Text Wrapper div
        var divFlexElem = document.createElement("div");
        divFlexElem.className = "d-flex align-items-center gap-3";
        // Icon Element
        var iconElem = document.createElement("i");
        iconElem.className = "fs-22 cursor-pointer";
        switch (type) {
            case "success":
                iconElem.className += " fa-regular fa-check";
                break;
            case "danger":
            case "error":
                iconElem.className += " fa-regular fa-xmark";
                break;
            case "info":
                iconElem.className += " fa-regular fa-info-circle";
                break;
            case "warning":
                iconElem.className += " fa-regular fa-warning";
                break;
            default:
                iconElem.className += " fa-regular fa-exclamation-circle";
                break;
        }
        // Set styles for Icon element
        for (var style in options.iconStyles) {
            iconElem.style[style] = options.iconStyles[style];
        }

        divFlexElem.appendChild(iconElem);
        divFlexElem.appendChild(textElem);
        snackbarElem.appendChild(divFlexElem);

        if (options.clickIconToRemove) {
            iconElem.addEventListener("click", () => {
                if (mountedToDom) {
                    snackbarElem.classList.add("hide-progress");
                    const clickTime = Date.now();
                    snackbarElem.style.setProperty("--snackbar-duration", clickTime - startTime + "ms");
                    window.global_snackbar_timeout = setTimeout(() => {
                        if (!removedFromDom) {
                            removedFromDom = true;
                            snackbarElem.classList.remove("show");
                            document.body.removeChild(snackbarElem);
                            // Create event
                            snackbarElem.dispatchEvent(new Event("snackbarRemoved"));
                        }
                    }, 500);
                    mountedToDom = false;
                }
            });
        }
    } else {
        snackbarElem.appendChild(textElem);
    }
    for (var style in options.textStyles) {
        snackbarElem.style[style] = options.textStyles[style];
    }
    switch (type) {
        case "success":
            snackbarElem.className += " snackbar-success";
            break;
        case "danger":
        case "error":
            snackbarElem.className += " snackbar-danger";
            break;
        case "info":
            snackbarElem.className += " snackbar-info";
            break;
        case "warning":
            snackbarElem.className += " snackbar-warning";
            break;
        case "light":
            snackbarElem.className += " snackbar-light";
            break;
        default:
            snackbarElem.className += " snackbar-default";
            break;
    }
    if (options.isConfirmed) {
        snackbarElem.classList.add("flex-column", "align-items-stretch");
        var buttonsDiv = document.createElement("div");
        buttonsDiv.classList.add("d-flex", "justify-content-end", "gap-2");
        var btnAccept = document.createElement("button");
        btnAccept.classList.add("btn", "btn-sm", "btn-success", "px-3");
        btnAccept.setAttribute("data-accept-snackbar", "");
        btnAccept.setAttribute("tabindex", 1);
        btnAccept.innerText = options.acceptText;
        btnAccept.addEventListener("click", function () {
            if (mountedToDom) {
                snackbarElem.classList.add("hide-progress");
                data.isConfirmed = true;
                const clickTime = Date.now();
                snackbarElem.style.setProperty("--snackbar-duration", clickTime - startTime + "ms");
                window.global_snackbar_timeout = setTimeout(() => {
                    if (!removedFromDom) {
                        removedFromDom = true;
                        snackbarElem.classList.remove("show");
                        document.body.removeChild(snackbarElem);
                        // Create event
                        snackbarElem.dispatchEvent(new Event("snackbarRemoved"));
                    }
                }, 500);
                mountedToDom = false;
            }
        });
        if (options.hasCancelBtn) {
            var btnCancel = document.createElement("button");
            btnCancel.classList.add("btn", "btn-sm", "btn-danger", "px-3");
            btnCancel.setAttribute("data-cancel-snackbar", "");
            btnCancel.setAttribute("tabindex", 1);
            btnCancel.innerText = options.cancelText;

            btnCancel.addEventListener("click", function () {
                if (mountedToDom) {
                    snackbarElem.classList.add("hide-progress");
                    const clickTime = Date.now();
                    snackbarElem.style.setProperty("--snackbar-duration", clickTime - startTime + "ms");
                    window.global_snackbar_timeout = setTimeout(() => {
                        if (!removedFromDom) {
                            removedFromDom = true;
                            snackbarElem.classList.remove("show");
                            document.body.removeChild(snackbarElem);
                            // Create event
                            snackbarElem.dispatchEvent(new Event("snackbarRemoved"));
                        }
                    }, 500);
                    mountedToDom = false;
                }
            });
            buttonsDiv.append(btnCancel);
        }
        buttonsDiv.append(btnAccept);
        snackbarElem.append(buttonsDiv);
    }
    snackbarElem.id = id;
    document.body.appendChild(snackbarElem);
    setTimeout(() => {
        mountedToDom = true;
    }, 200);
    snackbarElem.classList.add("show");
    if (options.isConfirmed)
        setTimeout(() => {
            snackbarElem.querySelector("[data-accept-snackbar]").focus();
        }, 50);
    let removedFromDom = false;
    if (options.duration && options.duration != null) {
        snackbarElem.style.setProperty("--snackbar-duration", options.duration + "ms");
        snackbarTimeout(options.duration + 300);
    } else {
        snackbarElem.classList.add("hide-progress");
        snackbarElem.style.setProperty("--snackbar-duration", 100000000 + "ms");
    }

    return new Promise((resolve) => {
        setInterval(() => {
            if (removedFromDom) resolve(data);
        }, 100);
    });

    function snackbarTimeout(timeout) {
        return window.global_snackbar_timeout = setTimeout(() => {
            if (!removedFromDom) {
                snackbarElem.classList.remove("show");
                document.body.removeChild(snackbarElem);
                removedFromDom = true;
                // Create event
                snackbarElem.dispatchEvent(new Event("snackbarRemoved"));
            }
        }, timeout);
    }
}
/* Snackbar End */

/* Search Result Box start */
function searchResultSet(inputId, boxId) {
    $(document).ready(function () {
        $(`#${inputId}`).on("focus", function () {
            $(`#${boxId}`).addClass("show");
        });

        $(document).on("click", function (event) {
            // If the target is not the container or a child of the container, then process
            // the click event for outside of the container.
            if ($(event.target).closest(`#${boxId}`).length === 0 && $(event.target).closest(`#${inputId}`).length === 0) {
                $(`#${boxId}`).removeClass("show");
            }
        });
    });
}
/* Search Result Box end */

// var numbersPattern = new RegExp("[^\u06F0-\u06F90-9\n]");
/* Helpers Start */
var numbersPattern = new RegExp("[^\u06F0-\u06F90-9\n]");
var decimalNumbersPattern = new RegExp("[^\u06F0-\u06F90-9.\n]");
var englishNumbersPattern = new RegExp("[^0-9\n]");
var persianNumbersPattern = new RegExp("[^\u06F0-\u06F9\n ]");
var englishCharsPattern = new RegExp("[^A-Za-z\u06F0-\u06F90-9\n ]");
var englishAndSpecialCharsPattern = new RegExp("[^A-Za-z\u06F0-\u06F90-9\n `!@#$%^&*()_+\\-=\\[\\]{};':\"\\\\|,.<>\\/?~÷×]");
var persianCharsPattern = new RegExp("[^\u0600-\u06FF\u06F0-\u06F90-9\n]");
var persianAndSpecialCharsPattern = new RegExp("[^\u0600-\u06FF\u06F0-\u06F90-9\n\\s`!@#$%^&*()_+\\-=\\[\\]{};':\"\\\\|,.<>\\/?~÷×«»]");
var englishAndPersianAndSpecialCharsPattern = new RegExp("[^A-Za-z\u06F0-\u06F9\u0600-\u06FF\u06F0-\u06F90-9\n\\s`!@#$%^&*()_+\\-=\\[\\]{};':\"\\\\|,.<>\\/?~÷×«»]");
var englishLettersPattern = new RegExp("[^A-Za-z\n]");
var persianLettersPattern = new RegExp("[^\u0600-\u06FF\n]");
var specialPattern = new RegExp("[^`!@#$%^&*()_+\\-=\\[\\]{};':\"\\\\|,.<>\\/?~÷×]");
var punycodePattern = /xn--[^@]+/; // a regular expression that matches Punycode strings

function shouldNumber(input, limit = null, allowZero = true, fillZero = false) {
    let lastInputValue = "";
    input.on("input", (e) => {
        let value = e.target.value;
        if ((value === "" && e.originalEvent?.inputType === "insertText") || (value === lastInputValue && e.originalEvent?.inputType === "insertText")) input.val(lastInputValue.length > 1 ? lastInputValue : "");
        if (value === "" && e.originalEvent?.inputType === "deleteContentBackward") lastInputValue = "";
        // If a number started with zero and allowZero = false, we should remove the zero from the beggining of input.
        if (!allowZero && value.startsWith("0")) {
            value = value.substring(1, value.length);
            input.val(value);
        }
        // If input is empty and fillZero = true, we should fill the input with the zero number.
        var newValue = value.replace(numbersPattern, "");
        if (fillZero && newValue.length == 0) {
            value = "0"
            newValue = "0"
            input.val("0");
        }
        lastInputValue = newValue.length > 0 ? newValue : lastInputValue;
        if (limit && value.length > limit) {
            input.val(value.substring(0, limit));
            lastInputValue = lastInputValue.substring(0, limit);
            snackbar("element_snackbar_18535934", "حداکثر تعداد کاراکتر مجاز "+ limit + " عدد می باشد.", "warning");
        }
        if (value !== newValue) {
            input.val(newValue);
            snackbar("element_snackbar_18535934", "لطفا صفحه کلید خود را عددی نمایید", "warning");
        }
    });

    input.on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text");
        const newPastedValue = pastedValue.replace(numbersPattern, "");
        if (pastedValue !== newPastedValue) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "لطفا متن عددی وارد نمایید", "warning");
            return false;
        }
        return true;
    });
}

function shouldPattern(input, pattern, limit = null, showSnackbar = true) {
    let lastInputValue = "";
    input.on("input", (e) => {
        let value = e.target.value;
        if ((value === "" && e.originalEvent?.inputType === "insertText") || (value === lastInputValue && e.originalEvent?.inputType === "insertText")) input.val(lastInputValue.length > 1 ? lastInputValue : "");
        if (value === "" && e.originalEvent?.inputType === "deleteContentBackward") lastInputValue = "";

        // If input is empty and fillZero = true, we should fill the input with the zero number.
        var newValue = value.replace(new RegExp(pattern), "");
        lastInputValue = newValue.length > 0 ? newValue : lastInputValue;
        if (limit && value.length > limit) {
            input.val(value.substring(0, limit));
            lastInputValue = lastInputValue.substring(0, limit);
            if (showSnackbar) snackbar("element_snackbar_18535934", "حداکثر تعداد کاراکتر مجاز "+ limit + " عدد می باشد.", "warning");
        }
        if (value !== newValue) {
            input.val(newValue);
            if (showSnackbar) snackbar("element_snackbar_18535934", "مقدار وارد شده غیر مجاز میباشد", "warning");
        }
    });

    input.on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text");
        const newPastedValue = pastedValue.replace(new RegExp(pattern), "");
        if (pastedValue !== newPastedValue) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "لطفا مقادیر معتبری وارد نمایید", "warning");
            return false;
        }
        return true;
    });
}

function shouldValue(input, minvalue, maxvalue) {
    var lastInputValue = "";
    input.on("input", (e) => {
        var value = e.target.value;
        if (maxvalue && value > maxvalue) {
            snackbar("element_snackbar_18535934", "عدد وارده باید حداکثر " + maxvalue + " باشد", "warning");
            if (lastInputValue <= maxvalue) {
                input.val(lastInputValue);
            } else {
                input.val(value.substring(0, maxvalue.toString().length - 1));
            }
        }
        lastInputValue = input.val();
    });
    input.on("blur", function (e) {
        var value = e.target.value;
        if (minvalue && value.length && value < minvalue) {
            snackbar("element_snackbar_18535934", "عدد وارده باید حداقل " + minvalue + " باشد", "danger");
            input.val("");
        }
    });

    input.on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text");
        if (minvalue && maxvalue && (pastedValue < minvalue || pastedValue > maxvalue)) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "مقدار وارده باید حداقل " + minvalue + " و حداکثر " + maxvalue + " باشد.", "danger");
            return false;
        } else if (minvalue && pastedValue < minvalue) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "مقدار وارده باید حداقل " + minvalue + " باشد.", "danger");
            return false;
        } else if (maxvalue && pastedValue > maxvalue) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "مقدار وارده باید حداکثر " + maxvalue + " باشد.", "warning");
            return false;
        }
        return true;
    });
}

function shouldPhoneNumber(input) {
    shouldNumber(input, 11);
    input.on("input", function (e) {
        if (e.originalEvent?.inputType === "insertText") {
            let value = e.target.value.replace(/ /g, "");
            if (value[0] != 0) {
                snackbar("element_snackbar_18535934", "تلفن همراه وارد شده باید با 09 شروع شود.", "warning");
                input.val("");
            } else if (value.length > 1 && value[1] != 9) {
                snackbar("element_snackbar_18535934", "تلفن همراه وارد شده باید با 09 شروع شود.", "warning");
                input.val(value.substring(0, 1));
            }
        }
    });

    shouldStartsWith(input, "09", "تلفن همراه")
}

function shouldStartsWith(input, expectedValue, fieldName = "متن") {
    expectedValue = expectedValue.toString()
    input.on("input", (e) => {
        let value = e.target.value;
        value.split("").forEach((character,index) => {
            if (value.length > index && expectedValue[index]) {
                if (character !== expectedValue[index]) {
                    input.val(value.substring(0, index))
                    snackbar("element_snackbar_18535934", fieldName + " وارد شده باید با " + expectedValue + " شروع شود.", "warning");
                }
            }
        })
    });

    input.on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text").replace(/ /g, "");
        pastedValue.split("").forEach((character,index) => {
            if (pastedValue.length > index && expectedValue[index]) {
                if (character !== expectedValue[index]) {
                    e.preventDefault();
                    snackbar("element_snackbar_18535934", fieldName + " وارد شده باید با " + expectedValue + " شروع شود.", "warning");
                    return false;
                }
            }
        })
        return true;
    });
}

function shouldDecimalNumber(input, decimalPoint = null, limit = null) {
    let lastInputValue = "";
    input.on("input", (e) => {
        let value = e.target.value;
        if (value === "" && e.originalEvent?.inputType === "insertText") input.val(lastInputValue.length > 1 ? lastInputValue : "");
        if (value === "" && e.originalEvent?.inputType === "deleteContentBackward") lastInputValue = "";
        var newValue = value.replace(decimalNumbersPattern, "");
        if ((value.split(".").length - 1) > 1) {
            newValue = newValue.replace(/\.(?=[^.]*$)/, "")
            lastInputValue = lastInputValue.replace(/\.(?=[^.]*$)/, "")
        }
        var decimalValues = newValue.indexOf(".") > 0 ? newValue.slice(newValue.indexOf(".") + 1, newValue.length) : (newValue.startsWith(".")? newValue.slice(1,newValue.length) : undefined);
        var numberValues = newValue.indexOf(".") > 0 ? newValue.slice(0, newValue.indexOf(".")) : (newValue.startsWith(".")? "" : newValue);
        var newNumberValue = numberValues;
        var newDecimalValue = decimalValues;
        if (limit && numberValues?.length > limit) {
            newNumberValue = numberValues.substring(0, limit)
            snackbar("element_snackbar_18535934", "حداکثر رقم بدون اعشار " + limit + " عدد می باشد", "warning");
        }

        if (decimalPoint && decimalValues?.length > decimalPoint) {
            newDecimalValue = decimalValues.substring(0, decimalPoint)
            snackbar("element_snackbar_18535934", "حداکثر رقم اعشار " + decimalPoint + " عدد می باشد", "warning");
        }

        if (numberValues?.length) {
            if (decimalValues?.length) {
                input.val(newNumberValue + "." + newDecimalValue);
            } else {
                if (!newValue.endsWith(".")) {
                    input.val(newNumberValue);
                }
            }
        } else if (decimalValues?.length) {
            input.val("." + newDecimalValue);
        }

        lastInputValue = newValue.length ? newValue : lastInputValue;
        if (value !== newValue) {
            input.val(newValue);
            snackbar("element_snackbar_18535934", "لطفا صفحه کلید خود را عددی نمایید", "warning");
        }
    });

    input.on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text").replace(/ /g, "");
        const newPastedValue = pastedValue.replace(decimalNumbersPattern, "");
        if (pastedValue !== newPastedValue) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "لطفا متن اعشاری وارد نمایید", "warning");
            return false;
        }
        return true;
    });
}

function shouldPersianAndSpecialChars(input, limit = null) {
    input.on("input", (e) => {
        let value = e.target.value;
        if (limit && value.length > limit) {
            input.val(value.substring(0, limit));
        }
        const newValue = value.replace(persianAndSpecialCharsPattern, "");
        if (value !== newValue) {
            input.val(newValue);
            snackbar("element_snackbar_18535934", "لطفا صفحه کلید خود را فارسی نمایید", "warning");
        }
    });

    input.on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text");
        const newPastedValue = pastedValue.replace(persianAndSpecialCharsPattern, "");
        if (pastedValue !== newPastedValue) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "لطفا متن فارسی یا کاراکتر خاص وارد نمایید", "warning");
            return false;
        }
        return true;
    });
}

function shouldEnglishAndSpecialChars(input, limit = null) {
    input.on("input", (e) => {
        let value = e.target.value;
        if (limit && value.length > limit) {
            input.val(value.substring(0, limit));
        }
        let newValue = value.replace(englishAndSpecialCharsPattern, "");
        newValue = newValue.replace(punycodePattern, "");
        if (value !== newValue) {
            input.val(newValue);
            snackbar("element_snackbar_18535934", "لطفا صفحه کلید خود را انگلیسی نمایید", "warning");
        }
    });

    input.on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text");
        const newPastedValue = pastedValue.replace(englishAndSpecialCharsPattern, "");
        if (pastedValue !== newPastedValue) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "لطفا متن انگلیسی یا کاراکتر خاص وارد نمایید", "warning");
            return false;
        }
        return true;
    });
}

function shouldEnglishAndPersianAndSpecialChars(input, limit = null) {
    input.on("input", (e) => {
        let value = e.target.value;
        if (limit && value.length > limit) {
            input.val(value.substring(0, limit));
        }
        let newValue = value.replace(englishAndPersianAndSpecialCharsPattern, "");
        newValue = newValue.replace(punycodePattern, "");
        if (value !== newValue) {
            input.val(newValue);
            snackbar("element_snackbar_18535934", "لطفا صفحه کلید خود را انگلیسی یا فارسی نمایید", "warning");
        }
    });

    input.on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text");
        const newPastedValue = pastedValue.replace(englishAndPersianAndSpecialCharsPattern, "");
        if (pastedValue !== newPastedValue) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "لطفا متن انگلیسی یا فارسی و یا کاراکتر خاص وارد نمایید", "warning");
            return false;
        }
        return true;
    });
}

function shouldPersianChars(input, limit = null) {
    input.on("input", (e) => {
        let value = e.target.value;
        if (limit && value.length > limit) {
            input.val(value.substring(0, limit));
        }
        const newValue = value.replace(persianCharsPattern, "");
        if (value !== newValue) {
            input.val(newValue);
            snackbar("element_snackbar_18535934", "لطفا صفحه کلید خود را فارسی نمایید", "warning");
        }
    });

    input.on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text");
        const newPastedValue = pastedValue.replace(persianCharsPattern, "");
        if (pastedValue !== newPastedValue) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "لطفا متن فارسی وارد نمایید", "warning");
            return false;
        }
        return true;
    });
}

function shouldEnglishChars(input, limit = null) {
    input.on("input", (e) => {
        let value = e.target.value;
        if (limit && value.length > limit) {
            input.val(value.substring(0, limit));
        }
        const newValue = value.replace(englishCharsPattern, "");
        if (value !== newValue) {
            input.val(newValue);
            snackbar("element_snackbar_18535934", "لطفا صفحه کلید خود را انگلیسی نمایید", "warning");
        }
    });

    input.on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text");
        const newPastedValue = pastedValue.replace(englishCharsPattern, "");
        if (pastedValue !== newPastedValue) {
            e.preventDefault();
            snackbar("element_snackbar_18535934", "لطفا متن انگلیسی وارد نمایید", "warning");
            return false;
        }
        return true;
    });
}

/* Helpers End */

/* Focus Visible Element Start */
$(function () {
    $("label").on("keydown", function (e) {
        if (e.keyCode === 32) {
            // Space bar key code
            e.preventDefault();
            switch ($("#" + $(this).attr("for")).attr("type")) {
                case "radio":
                    $("#" + $(this).attr("for")).prop("checked", !$("#" + $(this).attr("for")).prop("checked"));
                    break;
                default:
                    $("#" + $(this).attr("for")).focus();
                    break;
            }
        }
    });
});
/* Focus Visible Element End */

/* Clock timepicker defaults Start */

/* Clock timepicker defaults End */

/* Captcha Start */
function createCaptcha(id) {
    //clear the contents of captcha div first
    document.getElementById(id).innerHTML = "";
    let charsArray = "0123456789";
    let lengthOtp = 5;
    let captchaArray = [];
    let beforeIndex = -1;
    for (let i = 0; i < lengthOtp; i++) {
        let index = Math.floor(Math.random() * charsArray.length);
        //below code will not allow Repetition of Characters
        if (index === beforeIndex) {
            i--;
            continue;
        } else {
            beforeIndex = index;
        }
        captchaArray.push(charsArray[index]);
    }
    let canv = document.createElement("canvas");
    canv.id = id + "Canvas";
    canv.width = 64;
    canv.height = 37;
    let ctx = canv.getContext("2d");
    ctx.font = "17px IRanSans"; // Georgia
    ctx.strokeStyle = "white";
    ctx.textBaseline = "middle";
    ctx.textAlign = "center";
    ctx.fillStyle = "rgb(255,255,255)";
    ctx.fillText(captchaArray.join(""), 32, 23);
    ctx.strokeText(captchaArray.join(""), 32, 23);
    //storing captcha so that can validate you can save it somewhere else according to your specific requirements
    document.getElementById(id).appendChild(canv);
    return captchaArray.join("");
}
/* Captcha End */

/* Password Start */
const showPassword = (inputId, buttonId) => {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    if (input.getAttribute("type") === "password") {
        input.setAttribute("type", "text");
        button.classList.add("show_icon");
    } else {
        input.setAttribute("type", "password");
        button.classList.remove("show_icon");
    }
    input.focus();
};

function copyInput(buttonId, inputId) {
    var clipboard = new ClipboardJS(`#${buttonId}`, {
        container: document.getElementById(buttonId),
        text: function () {
            return $(`#${inputId}`).val();
        },
    });
    clipboard.on("success", function (e) {
        snackbar("element_clipboard_13423", "با موفقیت کپی گردید.", "success", { hasIcon: true });
        e.clearSelection();
    });

    clipboard.on("error", function (e) {
        if ($(`#${inputId}`).val().length < 1) snackbar("element_clipboard_13423", "متنی برای کپی وجود ندارد.", "warning", { hasIcon: true });
        else snackbar("element_clipboard_13423", "خطایی در هنگام کپی رخ داد.", "danger", { hasIcon: true });
    });
}

function copyText(text) {
    if (text.length) {
        const textCopied = ClipboardJS.copy(text);
        if (textCopied.length) snackbar("element_clipboard_13423", "با موفقیت کپی گردید.", "success", { hasIcon: true });
        else snackbar("element_clipboard_13423", "خطایی در هنگام کپی رخ داد.", "danger", { hasIcon: true });
    } else snackbar("element_clipboard_13423", "متنی برای کپی وجود ندارد.", "warning", { hasIcon: true });
}

function passwordCheck(password, id = "") {
    var strength = 0;
    if (password.length >= 8) strength += 1;
    if (password.match(/(?=.*[0-9])/)) strength += 1;
    if (password.match(/(?=.*[!,%,&,@,#,$,^,*,?,_,~,<,>,{,},+,(,),])/)) strength += 1;
    if (password.match(/(?=.*[a-z][A-Z])/)) strength += 1;
    displayBar(strength, id);
}

function displayBar(strength, id) {
    $("#password-strength-group"+id).attr("data-strength", strength);
    $("#password-strength-message"+id).attr("data-strength", strength);
    if (strength >= 3) {
        $("#check-strength").val("strength");
    } else {
        $("#check-strength").val("");
    }
}

function generatePass() {
    let char_int = "1234567890";
    let char_str = "abcdefghijklmnopqrstuvwxyz";
    let char_str2 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    let char_oper = "!@#$%^&*()~_+{}?><";
    let passLength = 5;
    let password = "";

    for (let i = 0; i < passLength; i++) {
        password += char_int[Math.floor(Math.random() * char_int.length)];
        password += char_str[Math.floor(Math.random() * char_str.length)];
        password += char_str2[Math.floor(Math.random() * char_str2.length)];
        password += char_oper[Math.floor(Math.random() * char_oper.length)];
    }

    return password;
}

function generatePassword(buttonId, inputId , form_element_id) {
    let btn = document.getElementById(buttonId);
    const input = $(`#${inputId}`);
    input.val(generatePass());
    passwordCheck(input.val() , form_element_id);
    input.focus();
}
/* Password End */
/* Generate random id start */
function generateId() {
    return "id-" + Math.random().toString(36).substring(2) + new Date().getTime().toString(36);
}
/* Generate random id end */
/* Dropdown Start */
function createDropdown(wrapperId) {
    /*Dropdown Menu*/
    const dropdown = $(`#${wrapperId}`);
    const dropdownSelect = dropdown.find("select");
    const dropdownValues = dropdown.find(".dropdown-values");
    const dropdownOptions = dropdown.find(".dropdown-options");
    $(document).ready(function () {
        var selectOptionsHTML = "";
        dropdownOptions.children("li").each(function () {
            const id = generateId();
            $(this).attr("id", id);
            selectOptionsHTML += `
               <option id="${id}" value="${$(this).attr("value")}">${$(this).text()}</option>
            `;
        });
        dropdownSelect.html(selectOptionsHTML);

        dropdownOptions.children("li").each(function () {
            const id = $(this).attr("id");
            const relatedOption = dropdownSelect.find(`option[id=${id}]`);
            if ($(this).attr("selected") === "selected") {
                dropdownValues.html(`<span>${$(this).text()}</span>`);
                $(this).attr("selected", "selected");
                $(this).siblings().removeAttr("selected");
                relatedOption.attr("selected", true);
                relatedOption.prop("selected", true);
                relatedOption.siblings().attr("selected", false);
                relatedOption.siblings().prop("selected", false);
            }
        });
    });

    dropdown.on("click", function () {
        if (dropdown.hasClass("open")) dropdown.removeClass("open");
        else dropdown.addClass("open");
    });

    dropdownOptions.children("li").each(function () {
        $(this).on("click", function () {
            const id = $(this).attr("id");
            const relatedOption = dropdownSelect.find(`option[id=${id}]`);
            if ($(this).attr("selected")) {
                $(this).removeAttr("selected");
                relatedOption.removeAttr("selected");
            } else {
                $(this).attr("selected", "selected");
                $(this).siblings().removeAttr("selected");
                relatedOption.attr("selected", true);
                relatedOption.prop("selected", true);
                relatedOption.siblings().attr("selected", false);
                relatedOption.siblings().prop("selected", false);

                dropdownSelect.trigger("change", dropdownSelect.val());
                dropdownValues.html(`<span>${relatedOption.text()}</span>`);
            }
        });
    });
    /*End Dropdown Menu*/
}

function resetDropdown(wrapperId) {
    const placeholderWrapper = $(`#${wrapperId}`).find("span[data-text]");
    placeholderWrapper.text(placeholderWrapper.attr("data-text"));
    $(`#${wrapperId}`)
        .find("ul.dropdown-menu li")
        .each(function () {
            $(this).removeAttr("data-selected");
        });
}

function setItemsOnSelect(selectedElId, relatedElId, data) {
    $(`#${selectedElId}`).on("change", function (event) {
        var res = data(event.target.value);
        var dropDownHTML = "";
        if (res) {
            res.forEach((item) => {
                dropDownHTML += `<option value="${item.value}">${item.label}</option>`;
            });
            $(`#${relatedElId}`).empty();
            $(`#${relatedElId}`).html(dropDownHTML);
        }
    });
}
/* Dropdown End */

/* Price Helper start */
function toPrice(value) {
    return parseInt(value).toLocaleString();
}

function toFaPrice(price) {
    return parseInt(price).toLocaleString() + " ریال";
}
/* Price Helper end */

/* Image Preview Start */
function previewImgSet(id) {
    /* Preview Avatar Image */
    $(document).ready(function () {
        var previewImg = document.querySelector(`.preview-img-${id} img`);
        var rotateOption = document.querySelectorAll(`.rotate-${id} span`);
        var rotate = 0;
        var flipHorizontal = 1;
        var flipVertical = 1;
        var applyFilter = () => {
            previewImg.style.transform = `rotate(${rotate}deg) scale(${flipHorizontal}, ${flipVertical})`;
        };

        rotateOption.forEach((option) => {
            option.addEventListener("click", () => {
                if (option.id === "left-rotate") {
                    rotate -= 90;
                } else if (option.id === "right-rotate") {
                    rotate += 90;
                } else if (option.id === "horizontal") {
                    flipHorizontal = flipHorizontal === 1 ? -1 : 1;
                } else {
                    flipVertical = flipVertical === 1 ? -1 : 1;
                }
                applyFilter();
            });
        });
    });
}
function drag(id) {
    var previewImg = document.querySelector(`.preview-img-${id} img`);
    $(`#draggable_${id}`).draggable();
    previewImg.style.cursor = "grab";
}
function zoomIn(id) {
    var previewImg = document.querySelector(`.preview-img-${id} img`);
    let width = previewImg.clientWidth;
    let height = previewImg.clientHeight;
    previewImg.style.width = width + 50 + "px";
    previewImg.style.height = height + 50 + "px";
    drag(id);
}
function zoomOut(id) {
    var previewImg = document.querySelector(`.preview-img-${id} img`);
    let width = previewImg.clientWidth;
    let height = previewImg.clientHeight;
    previewImg.style.width = width - 50 + "px";
    previewImg.style.height = height - 50 + "px";
    drag(id);
}
/* Image Preview End */
/* Current time */
function getTime() {
    var now = new Date();
    var hour = now.getHours();
    var minute = now.getMinutes();
    var second = now.getSeconds();
    if (hour.toString().length == 1) {
        hour = "0" + hour;
    }
    if (minute.toString().length == 1) {
        minute = "0" + minute;
    }
    if (second.toString().length == 1) {
        second = "0" + second;
    }
    var time = hour + ":" + minute + ":" + second;
    return time;
}

function getDate() {
    let options = { year: "numeric", month: "long", day: "numeric" };
    let today = new Date().toLocaleDateString("fa-IR", options);
    return today;
}

function getWeekDay() {
    let currentWeekday = new Date().getDay();
    switch (currentWeekday) {
        case 6:
            currentWeekday = "شنبه";
            break;
        case 0:
            currentWeekday = "یک شنبه";
            break;
        case 1:
            currentWeekday = "دوشنبه";
            break;
        case 2:
            currentWeekday = "سه شنبه";
            break;
        case 3:
            currentWeekday = "چهارشنبه";
            break;
        case 4:
            currentWeekday = "پنجشنبه";
            break;
        case 5:
            currentWeekday = "جمعه";
            break;
    }
    return currentWeekday;
}
function setCurrentTimeTo(id) {
    setInterval(function () {
        let currentTime = getTime();
        document.getElementById(id).innerHTML = currentTime;
    }, 1000);
}
function setCurrentDateTo(id) {
    let currentDate = getWeekDay() + " " + getDate();
    document.getElementById(id).innerHTML = currentDate;
}

/* Touch and Mouse Zoom Start */
function mouseZoom(elementId, resetBtnId = null, mode = "scale") {
    let element = document.getElementById(elementId);
    let currentZoom = 100;
    let minZoom = 70;
    let maxZoom = 200;
    let stepSize = 5;
    if (resetBtnId && resetBtnId.length) {
        let resetBtn = document.getElementById(resetBtnId);
        resetBtn.addEventListener("click", () => {
            switch (mode) {
                case "zoom":
                    element.style.zoom = 1;
                    break;
                case "transform":
                    element.style.transform = "scale(" + 1 + ")";
                    break;
                default:
                    element.style.transform = "scale(" + 1 + ")";
                    break;
            }
            currentZoom = 100;
            resetBtn.classList.add("hide");
        });
    }
    element.addEventListener("wheel", function (event) {
        event.preventDefault();
        // Zoom in or out based on the scroll direction
        let direction = event.deltaY > 0 ? -1 : 1;
        zoomElement(direction, mode);
    });
    function zoomElement(direction) {
        let newZoom = currentZoom + direction * stepSize;

        // Limit the zoom level to the minimum and maximum values
        if (newZoom < minZoom || newZoom > maxZoom) {
            return;
        }

        currentZoom = newZoom;

        // Update the CSS transform of the image to scale it

        switch (mode) {
            case "zoom":
                element.style.zoom = currentZoom / 100;
                break;
            case "transform":
                element.style.transform = "scale(" + currentZoom / 100 + ")";
                break;
            default:
                element.style.transform = "scale(" + currentZoom / 100 + ")";
                break;
        }

        // Trigger zoom event
        $(`#${elementId}`).trigger("mouseZoomed", {
            zoom: currentZoom,
        });

        if (document.getElementById(resetBtnId)) document.getElementById(resetBtnId).classList.remove("hide");
    }
}
function touchZoom(elementId, resetBtnId, mode = "scale", minZoom = 70, maxZoom = 150, speed = 100, defaultZoom = 100) {
    var scaling = false;
    var element = document.getElementById(elementId);
    if (resetBtnId && resetBtnId.length) {
        let resetBtn = document.getElementById(resetBtnId);
        resetBtn.addEventListener("click", () => {
            switch (mode) {
                case "zoom":
                    element.style.zoom = 1;
                    break;
                case "transform":
                    element.style.transform = "scale(" + 1 + ")";
                    break;
                default:
                    element.style.transform = "scale(" + 1 + ")";
                    break;
            }
            defaultZoom = 100;
            resetBtn.classList.add("hide");
        });
    }
    element.addEventListener("touchstart", (e) => {
        if (e.touches.length === 2) {
            scaling = true;
            pinchStart(e);
        }
    });

    element.addEventListener("touchmove", (e) => {
        if (scaling) {
            pinchMove(e);
        }
    });

    element.addEventListener("touchend", (e) => {
        if (scaling) {
            scaling = false;
            pinchEnd(e);
        }
    });
    var lastDist = 0;
    function pinchStart(e) {
        var dist = Math.round(Math.hypot(e.touches[0].pageX - e.touches[1].pageX, e.touches[0].pageY - e.touches[1].pageY));
        lastDist = dist;
    }

    function pinchMove(e) {
        var dist = Math.round(Math.hypot(e.touches[0].pageX - e.touches[1].pageX, e.touches[0].pageY - e.touches[1].pageY));
        if (dist > lastDist) {
            // Zoom In
            if (defaultZoom < maxZoom) defaultZoom += speed / 100;
        } else {
            // Zoom Out
            if (defaultZoom > minZoom) defaultZoom -= speed / 100;
        }

        switch (mode) {
            case "zoom":
                element.style.zoom = defaultZoom / 100;
                break;
            case "transform":
                element.style.transform = "scale(" + defaultZoom / 100 + ")";
                break;
            default:
                element.style.transform = "scale(" + defaultZoom / 100 + ")";
                break;
        }

        // Trigger zoom event
        $(`#${elementId}`).trigger("touchZoomed", {
            zoom: defaultZoom / 100,
        });

        if (document.getElementById(resetBtnId)) document.getElementById(resetBtnId).classList.remove("hide");
    }

    function pinchEnd(e) { }
}

function dragElements(elements, eventCallback = () => ("")) {
    elements.forEach(element => {
        element.parentElement.style.height = element.parentElement.clientHeight + "px";
        element.style.position = "absolute";
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        if (document.getElementById(element.id + "header")) {
            // If present, the header is where you move the DIV from
            document.getElementById(element.id + "header").onmousedown = dragMouseDown;
        } else {
            // Otherwise, move the DIV from anywhere inside the DIV
            element.onmousedown = dragMouseDown;
        }
        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            eventCallback("mousedown")
            // Get the mouse cursor position at startup
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            // Call a function whenever the cursor moves
            document.onmousemove = elementDrag;
        }
        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            eventCallback("mousemove")
            // Calculate the new cursor position
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            // Set the element's new position
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
        }
        function closeDragElement() {
            eventCallback("mouseup")
            // Stop moving when the mouse button is released
            document.onmouseup = null;
            document.onmousemove = null;
        }
        element.addEventListener("touchstart", touchStart, false);
        element.addEventListener("touchmove", touchMove, false);
        element.addEventListener("touchend", touchEnd, false);
        function touchStart(e) {
            eventCallback("touchstart")
            pos3 = e.touches[0].clientX;
            pos4 = e.touches[0].clientY;
        }
        function touchMove(e) {
            e.preventDefault();
            eventCallback("touchmove")
            pos1 = pos3 - e.touches[0].clientX;
            pos2 = pos4 - e.touches[0].clientY;
            pos3 = e.touches[0].clientX;
            pos4 = e.touches[0].clientY;
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
        }
        function touchEnd() {eventCallback("touchend")}
    })
}
/* Touch and Mouse Zoom End */

/* Print Start */
function print_button(container) {
    window.print(container);
}
/* Print End */
var zoom = 1;
function zoomReset(elementId) {
    const element = $(`#${elementId}`);
    zoom = 1;
    element.css("zoom", zoom);
    element.css("-ms-transform", "scale("+zoom+")");
    element.css("-o-transform", "scale("+zoom+")");
    element.css("-moz-transform", "scale("+zoom+")");
}
function zoomIn(elementId) {
    const element = $(`#${elementId}`);
    if (zoom < 2) {
        zoom += 0.25;
        element.css("zoom", zoom);
        element.css("-ms-transform", "scale("+zoom+")");
        element.css("-o-transform", "scale("+zoom+")");
        element.css("-moz-transform", "scale("+zoom+")");
    }
}
function zoomOut(elementId) {
    const element = $(`#${elementId}`);
    if (zoom > 0.5) {
        zoom -= 0.25;
        element.css("zoom", zoom);
        element.css("-ms-transform", "scale("+zoom+")");
        element.css("-o-transform", "scale("+zoom+")");
        element.css("-moz-transform", "scale("+zoom+")");
    }
}

function readFilePreview(input, preview_id) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const fileType = file.type;
        const fileName = file.name;
        const fileExtension = fileName.split('.').pop().toLowerCase();
        const reader = new FileReader();
        
        reader.onload = function (e) {
            const previewElement = $("#" + preview_id);
            previewElement.removeClass("d-none");
            previewElement.empty();
            const previewContainer = $('<div class="w-100 h-100 position-relative"></div>');
            const deleteButton = $(`
                <button type="button" class="btn btn-danger btn-sm position-absolute top-0 end-0 m-1" onclick="emptyFile('${input.id}', '${preview_id}', 'file_old')">
                    <i class="fa-solid fa-trash-alt"></i>
                </button>
            `);
            if (fileType.startsWith("image/")) {
                const img = $('<img class="w-100 h-100 rounded object-fit-cover">');
                img.attr('src', e.target.result);
                img.hide().fadeIn(650);
                previewContainer.append(img);
                
            } else if (fileType.startsWith("video/")) {
                const videoPreview = $(`
                    <div class="w-100 h-100 d-flex align-items-center justify-content-center">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width="80%" height="80%">
                            <g>
                                <path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Zm-77-20.83c-.6,0-1.19-.17-1.71-.48-.97-.6-1.54-1.66-1.51-2.8v-38.42c-.03-1.14.55-2.2,1.51-2.8.94-.59,2.12-.64,3.11-.14l39.2,19.24c1.59.79,2.24,2.72,1.45,4.32-.31.63-.82,1.14-1.45,1.45l-39.2,19.24c-.43.24-.91.37-1.4.39Zm3.22-36.54v28.14l28.59-14-28.59-14.14Z"></path>
                            </g>
                        </svg>
                        <div class="position-absolute bottom-0 start-0 end-0 bg-dark bg-opacity-50 text-white p-1 text-center small rounded-2 fs-10">
                            ${fileName}
                        </div>
                    </div>
                `);
                previewContainer.append(videoPreview);
                
            } else if (fileType.startsWith("audio/")) {
                const audioPreview = $(`
                    <div class="w-100 h-100 d-flex align-items-center justify-content-center">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32.14 40" width="60%" height="60%">
                            <g>
                                <path class="file-manager-bg-dark" d="m8.28,0L0,8.28v28.15c0,1.97,1.6,3.57,3.57,3.57h25c1.97,0,3.57-1.6,3.57-3.57V3.57c0-1.97-1.6-3.57-3.57-3.57M7.84,2.44v3.76c.02.95-1.05,1.66-1.94,1.66h-3.46L7.84,2.44Zm22.88,33.99c0,1.18-.96,2.14-2.14,2.14H3.57c-1.18,0-2.14-.96-2.14-2.14h0V13.57h29.29v22.86Zm-14.14-18.97h0c-.06,0-.11,0-.17,0-.05,0-.1,0-.15,0-.32.1-.54.38-.56.71l-.22,2.96h0l-.46,6.01c-1.43-.05-5,.14-5.55,3.2-.21.95.21,1.92,1.04,2.42.56.34,1.21.51,1.86.5.9,0,1.77-.28,2.51-.79.92-.67,1.5-1.72,1.57-2.86,0-.04,0-.09,0-.13l.59-7.35c1.62.55,3.1,1.45,4.33,2.64.15.15.36.24.57.24.12,0,.23-.03.34-.07.3-.14.49-.45.48-.79-.03-3.49-2.7-6.38-6.17-6.7Zm-2.64,13.74c-.74.53-1.71.62-2.53.24-.26-.14-.39-.43-.33-.71.3-1.63,2.44-1.86,3.57-1.86h.14c.17.88-.16,1.78-.86,2.34Zm3.25-10.71l.07-1.19c1.52.37,2.78,1.43,3.42,2.86-1.06-.77-2.25-1.32-3.52-1.63l.03-.04Z"></path>
                            </g>
                        </svg>
                        <div class="position-absolute bottom-0 start-0 end-0 bg-dark bg-opacity-50 text-white p-1 text-center small rounded-2 fs-10">
                            ${fileName}
                        </div>
                    </div>
                `);
                previewContainer.append(audioPreview);
                
            } else if (fileType.includes("pdf") || 
                      fileType.includes("msword") || 
                      fileType.includes("wordprocessingml") || 
                      fileType.includes("officedocument") ||
                      fileExtension === "doc" || fileExtension === "docx" ||
                      fileExtension === "xls" || fileExtension === "xlsx" ||
                      fileExtension === "ppt" || fileExtension === "pptx") {
                const docPreview = $(`
                    <div class="w-100 h-100 d-flex align-items-center justify-content-center">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width="80%" height="80%">
                            <g>
                                <path class="file-manager-bg-dark" d="m37.13,138.18c-2.43.03-4.76-1-6.38-2.81-2.94-3.83-2.45-9.28,1.12-12.53,2.61-2.81,9.97-5.84,18.46-8.43,1.87-4.83,3.85-10.77,5.93-17.81-2.33-5.9-3.66-12.15-3.93-18.49-.39-7.59,3.65-11.91,7.84-12.28,3.32-.28,7.22,2.08,7.95,7.89h0c.29,2.67.04,5.38-.76,7.95l-1.07,3.68c-1.04,3.65-2.08,7.3-3.15,10.87,2.16,4.81,5.11,9.22,8.71,13.06,3.92-.76,7.89-1.22,11.88-1.38,8.18,0,11.24,3.71,12.47,5.9,1.46,2.66,1.31,5.91-.37,8.43-1.85,2.66-5.02,4.07-8.23,3.68-6.75-1.43-12.94-4.79-17.81-9.66-4.69.96-9.78,2.19-14.55,3.54-3.01,7.44-5.98,12.9-8.91,14.95-2.64,2.07-5.86,3.27-9.21,3.43Zm10.06-15.9c-3.81,1.03-7.41,2.75-10.59,5.09-1.4,1.52-1.6,3.15-.98,3.88s3.12.96,7-1.77c2.03-2.03,3.6-4.49,4.58-7.19Zm30.9-7.44c2.97,2.35,6.47,3.94,10.2,4.64.85.17,1.73-.14,2.28-.81.33-.54.33-1.23,0-1.77-.31-.59-1.69-2.44-6.8-2.47-1.89.05-3.78.22-5.65.51l-.03-.08Zm-17.64-9.83c-.84,2.56-1.66,5.03-2.47,7.39,2.22-.59,4.44-1.12,6.63-1.6-1.5-1.84-2.88-3.77-4.13-5.79h-.03Zm.25-32.62h0c-.65,0-2.11,1.74-1.94,5.62.12,2.47.41,4.93.87,7.36.14-.53.31-1.04.45-1.57l1.07-3.71c.54-1.72.73-3.54.56-5.34h0c-.22-1.8-.84-2.36-.98-2.36h-.03ZM112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Z"></path>
                            </g>
                        </svg>
                        <div class="position-absolute bottom-0 start-0 end-0 bg-dark bg-opacity-50 text-white p-1 text-center small rounded-2 fs-10">
                            ${fileName}
                        </div>
                    </div>
                `);
                previewContainer.append(docPreview);
                
            } else {
                const genericPreview = $(`
                    <div class="w-100 h-100 d-flex align-items-center justify-content-center">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width="80%" height="80%">
                            <g>
                                <path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.26,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14Zm-19.15,22.92c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-16.52,0c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-16.52,0c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-29.01-13.37v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.56L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4V53.2h114.8v89.6Zm-18.76-20.03c0,.91-.37,1.73-.96,2.32-.59.59-1.41.96-2.32.96s-1.73-.37-2.32-.96c-.59-.59-.96-1.41-.96-2.32s.37-1.72.96-2.31c.59-.6,1.41-.96,2.32-.96,1.81,0,3.28,1.46,3.28,3.27Zm12.45-32.1c0,2.05-.56,4.12-1.66,6.19-1.1,2.07-3.04,3.95-5.81,5.63-2.12,1.69-3.37,2.8-3.74,3.35-.37.54-.74,1.14-1.1,1.8-.36.65-.62,1.87-.8,3.63v.53c0,1.54-1.24,2.78-2.78,2.78-.77,0-1.47-.31-1.97-.81s-.82-1.2-.82-1.97v-.03c-.11-1.47,0-2.93.33-4.39.74-2.43,1.94-4.39,3.6-5.9,2.54-2.18,4.64-4.08,6.33-5.68,1.68-1.61,2.52-3.36,2.52-5.26,0-2.34-.96-4.27-2.87-5.79-1.91-1.51-4.12-2.27-6.63-2.27s-4.42.77-6.06,2.31c-1.27,1.19-2.28,2.86-3.02,5.02-.41,1.18-1.61,1.91-2.86,1.8h-.06c-1.74-.17-2.93-1.89-2.42-3.57.73-2.42,1.99-4.59,3.77-6.51,2.56-2.75,6.11-4.13,10.65-4.13s8.52,1.24,11.27,3.73,4.13,5.67,4.13,9.54Zm-31.48-10.46c0,1.78-1.44,3.22-3.22,3.22h-44.38c-1.78,0-3.22-1.44-3.22-3.22s1.44-3.22,3.22-3.22h44.38c1.78,0,3.22,1.44,3.22,3.22Zm-54.55,0c0,1.78-1.44,3.22-3.22,3.22h-7.98c-1.78,0-3.23-1.44-3.23-3.22s1.44-3.22,3.22-3.22h7.99c1.78,0,3.23,1.44,3.22,3.22Zm34.69,21.3c0,1.78-1.44,3.22-3.22,3.22H16.86c-1.78,0-3.22-1.45-3.22-3.23s1.44-3.22,3.22-3.22h42.67c1.78,0,3.23,1.45,3.22,3.23Zm26.52,21.29c0,1.78-1.44,3.22-3.22,3.22h-45.23c-1.78.01-3.23-1.44-3.23-3.22s1.44-3.22,3.22-3.22h45.23c1.78,0,3.23,1.44,3.23,3.22Zm-57,0c0,1.78-1.44,3.22-3.22,3.22h-12.19c-1.78,0-3.22-1.44-3.22-3.22s1.44-3.22,3.22-3.22h12.19c1.78,0,3.22,1.44,3.22,3.22Z"></path>
                            </g>
                        </svg>
                        <div class="position-absolute bottom-0 start-0 end-0 bg-dark bg-opacity-50 text-white p-1 text-center small rounded-2 fs-10">
                            ${fileName}
                        </div>
                    </div>
                `);
                previewContainer.append(genericPreview);
            }
            
            previewContainer.append(deleteButton);
            
            previewElement.append(previewContainer);
            previewElement.hide().fadeIn(650);
        };
        
        reader.readAsDataURL(file);
    }
}

// function emptyFile(inputId, previewId, oldFileInputId) {
//     const input = document.getElementById(inputId);
//     const preview = document.getElementById(previewId);
    
//     if (input) {
//         // Clear the file input
//         input.value = '';
//     }
    
//     if (preview) {
//         // Hide the preview
//         preview.classList.add("d-none");
//         preview.innerHTML = '';
//     }
    
//     // If there's an old file input, clear it too
//     if (oldFileInputId) {
//         const oldInput = document.getElementById(oldFileInputId);
//         if (oldInput) {
//             oldInput.value = '';
//         }
//     }
// }

function newFilePreview(preview_id, file) {
    $("#" + preview_id).removeClass("d-none");
    $("#" + preview_id + " > img").attr("src", file);
    $("#" + preview_id + " > img").hide();
    $("#" + preview_id + " > img").fadeIn(650);
}

function emptyFile(input, preview_id, file_old) {
    $("#" + preview_id).addClass("d-none");
    $("#" + preview_id + "> img").attr("src", "");
    $("#" + input).val("");
    $('input[name^="' + file_old + '"]').val("");
}
// function outsideClicked(func, selectors=[], condition="and") {
//     elementSelectors.forEach(selector => {
//         $(event.target).closest(selector).length===0
//     })

//     $(document).on("click", function (event) {
//         // If the target is not the container or a child of the container, then process
//         // the click event for outside of the container.
//         if ($(event.target).closest(".field-selectable").length===0&&$(event.target).closest(".field-box[data-type]").length===0) {
//             if ($('.field-selectable').hasClass("selected")) {
//                 $('.field-selectable').removeClass("selected")
//             }
//         }
//     })
// }
function link_preview(link) {
    window.open(link, "", "width=800,height=500,resizable=yes,scrollbars=yes");
}

function tagify_met(input, value, maxTags = 99999) {
    value = value.map((v) => {
        v.value = v.id;
        return v;
    });
    tagify = new Tagify(input, {
        delimiters: null,
        tagTextProp: "title",
        keepInvalidTags: false,
        maxTags,
        callbacks: {
            add: console.log, // callback when adding a tag
            remove: console.log, // callback when removing a tag
        },

        dropdown: {
            enabled: 0, // show the dropdown immediately on focus
            closeOnSelect: true, // keep the dropdown open after selecting a suggestion
            highlightFirst: true,
            searchKeys: ["title"],
        },
        templates: {
            tag: function (tagData) {
                try {
                    return `<tag title="${tagData.value}" contenteditable="false" spellcheck="false" class="tagify__tag ${tagData.class ? tagData.class : ""}" ${this.getAttributes(tagData)}>
                            <x title="حذف" class="tagify__tag__removeBtn"></x>
                            <div>
                                <span class="tagify__tag-text">${tagData.title}</span>
                            </div>
                        </tag>`;
                } catch (err) { }
            },

            dropdownItem: function (tagData) {
                try {
                    return `<div ${this.getAttributes(tagData)} class="tagify__dropdown__item ${tagData.class ? tagData.class : ""}" >
                            <span>${tagData.title}</span>
                        </div>`;
                } catch (err) {
                    console.error(err);
                }
            },
        },
        enforceWhitelist: true,
        whitelist: value,
    });
}

var beforModalId = '';
/* Plate start */
function initCarPlate(json, plateModalId = "carPlateWrapper", uniqueId = "", disabled = false, totalInput = '', totalInputFa = '') {
    var plate_box_one_input = $(".plate-box-one-input"+uniqueId)
    var plate_box_two_input = $(".plate-box-two-input"+uniqueId)
    var plate_box_three_input = $(".plate-box-three-input"+uniqueId)
    var plate_box_four_input = $(".plate-box-four-input"+uniqueId)
    var plate_box_empty_hidden = $("#element_"+uniqueId+"_2")
    var plate_alpha_buttons = $("#plate-alpha-items")
    let plate_alphabet = (!disabled) ? JSON.parse(json) : [];
    $(document).ready(function() {
        updateTotalInput(totalInput, totalInputFa);
        plate_box_three_input.on("input", () => updateTotalInput(totalInput, totalInputFa))
        plate_box_four_input.on("input", () => updateTotalInput(totalInput, totalInputFa))
        if (plate_box_four_input.val().length == 2) {
            if (!disabled) {
                plate_box_four_input.attr("readonly", false)
                plate_box_three_input.attr("readonly", false)
                plate_box_one_input.attr("readonly", false)
            }
        }
    })
    function updateTotalInput(totalInput = '', totalInputFa = '') {
        if (totalInput.length > 0) $(`#${totalInput}`).val(($("#element_"+uniqueId+"_1").val() || '--') + ($("#element_"+uniqueId+"_2").val() || '--') + ($("#element_"+uniqueId+"_3").val() || '---') + ($("#element_"+uniqueId+"_4").val() || '--'));
        if (totalInputFa.length > 0) $(`#${totalInputFa}`).val(($("#element_"+uniqueId+"_1").val() || '--') + ' ' + ($("#element_"+uniqueId+"_3").val() || '--') + ' ' + ($(".plate-box-empty" + uniqueId).text() || '---') + ' ' + ($("#element_"+uniqueId+"_4").val() || '--'));
    }
    if (!disabled) {
        plate_alphabet = !plate_alphabet.length ? JSON.parse(json) : plate_alphabet;
        /* Generate Alphabet HTML Start */
        let html = [];
        for (var key in plate_alphabet) {
            html.push("<button type='button' class='plate-alpha' data-id='" + key + "'>" + plate_alphabet[key] + "</button>")
        }
        $("#"+plateModalId).html(html)
        /* Generate Alphabet HTML End */

        shouldNumber(plate_box_one_input)
        shouldNumber(plate_box_two_input)
        shouldNumber(plate_box_three_input)
        shouldNumber(plate_box_four_input)
        plate_box_one_input.keyup(function () {
            if (plate_box_one_input.val().length == 2) {
                if (!disabled) {
                    window.isOpeningAnotherModal = true;
                    plate_box_two_input.attr("data-bs-toggle", "modal")
                    plate_box_two_input.attr("data-bs-target", "#"+plate_alpha_buttons.attr("id"))
                    plate_alpha_buttons.modal("show")
                }
                plate_box_two_input.attr("data-id", uniqueId)
            } else {
                if (!disabled) {
                    plate_box_two_input.attr("data-bs-toggle", "")
                    plate_box_two_input.attr("data-bs-target", "")
                }
            }
        })
        plate_box_two_input.click(function() {
            lastOpenedModalId = $(this).closest(".modal").attr("id") ?? lastOpenedModalId
            if (plate_box_one_input.val().length == 2) {
                if (!disabled) {
                    window.isOpeningAnotherModal = true;
                    $(this).attr("data-bs-toggle", "modal")
                    $(this).attr("data-bs-target", "#" + plate_alpha_buttons.attr("id"))
                    plate_alpha_buttons.modal("show")
                }
                $(this).attr("data-id", uniqueId)
                updateTotalInput(totalInput, totalInputFa);
            }
        })
        /* On Modal Shown */
        var lastOpenedModalId = ""
        plate_alpha_buttons.on("show.bs.modal", function (e) {
            lastOpenedModalId = $(".modal.show").attr("id") ?? lastOpenedModalId
            if (lastOpenedModalId?.length) {
                window.isOpeningAnotherModal = true;
                $("#" + lastOpenedModalId).modal("hide");
            }
        })
        plate_alpha_buttons.on("shown.bs.modal", function (e) {
            $(this).on("keypress", (e) => {
                if (!plate_box_two_input.attr("data-id") && plate_box_two_input.attr("data-id") !== uniqueId) {
                    return;
                }
                plate_alpha_buttons.find(".plate-alpha").each(function () {
                    if (Object.values(plate_alphabet).map((a) => a.toLowerCase()).includes(e.key.toLowerCase())) {
                        if ($(this).text().toLowerCase() === e.key.toLowerCase()) {
                            $(".plate-box-empty" + uniqueId).text($(this).text())
                            plate_box_empty_hidden.val($(this).data("id"))
                            window.isOpeningAnotherModal = true;
                            plate_alpha_buttons.modal("hide")
                            if (plate_box_three_input.val().length == 0) {
                                plate_box_three_input.attr("readonly", false)
                                plate_box_three_input.focus()
                            }
                            plate_box_two_input.attr("data-id", "")
                            updateTotalInput(totalInput, totalInputFa);
                            return
                        }
                    } else {
                        snackbar("element_3429589435", "حرف پلاک وارد شده وجود ندارد!", "danger")
                    }
                })
            })
            $(this).on("keyup", function () {
                if (!plate_box_two_input.attr("data-id") && plate_box_two_input.attr("data-id") !== uniqueId) return;
                if ($(".plate-box-empty" + uniqueId).text() !== "-") {
                    plate_box_three_input.attr("readonly", false)
                    plate_box_three_input.focus()
                }
            })
        })
        plate_alpha_buttons.on("hide.bs.modal", function () {
        })
        plate_alpha_buttons.on("hidden.bs.modal", function () {
            window.isOpeningAnotherModal = false;
            if (lastOpenedModalId?.length) {
                $("#" + lastOpenedModalId).modal("show");
            }
            if (!plate_box_two_input.attr("data-id") && plate_box_two_input.attr("data-id") !== uniqueId) return;
            setTimeout(() => {
                if ($(".plate-box-empty" + uniqueId).text() !== "-") {
                    plate_box_three_input.focus();
                }
            }, 500)
            plate_box_two_input.attr("data-id", "")
            lastOpenedModalId = ""
            updateTotalInput(totalInput, totalInputFa);
        })
        $(".plate-box-empty" + uniqueId).on("keyup", function (e) {
            if (e.keyCode == 8) {
                if ($(this).text() != "-") {
                    $(this).html("-")
                    plate_box_empty_hidden.val("")
                    $(this).parent().removeAttr("data-bs-target")
                    $(this).parent().removeAttr("data-bs-toggle")
                    $(this).parent().attr("readonly", true)
                    plate_box_one_input.focus()
                    updateTotalInput(totalInput, totalInputFa);
                }
            }
        })
        plate_box_three_input.keyup(function () {
            if (plate_box_three_input.val().length == 3) {
                plate_box_four_input.attr("readonly", false)
                plate_box_four_input.focus()
            }
        })

        plate_alpha_buttons.on("click", ".plate-alpha", function () {
            plate_alpha_buttons.unbind("keypress")
            if (!plate_box_two_input.attr("data-id")?.length && plate_box_two_input.attr("data-id") !== uniqueId) {
                window.isOpeningAnotherModal = true;
                plate_alpha_buttons.modal("hide")
            } else {
                $(".plate-box-empty" + uniqueId).html($(this).html())
                plate_box_empty_hidden.val($(this).data("id"))
                window.isOpeningAnotherModal = true;
                plate_alpha_buttons.modal("hide")
                if (plate_box_three_input.val().length == 0) {
                    plate_box_three_input.attr("readonly", false)
                    plate_box_three_input.focus()
                }
            }
            plate_box_two_input.attr("data-id", "")
            updateTotalInput(totalInput, totalInputFa);
        })

        if (plate_box_one_input.val() !== "")
            plate_box_one_input.attr("readonly", false);
        if (plate_box_two_input.val() !== "")
            plate_box_two_input.attr("readonly", false);
        if (plate_box_three_input.val() !== "")
            plate_box_three_input.attr("readonly", false);
        if (plate_box_four_input.val() !== "")
            plate_box_four_input.attr("readonly", false);
    } else {
        plate_box_one_input.attr("readonly", "readonly");
        plate_box_two_input.attr("readonly", "readonly");
        plate_box_three_input.attr("readonly", "readonly");
        plate_box_four_input.attr("readonly", "readonly");
    }
}
function empty_input(e, id, uniqueId = "", disabled = false, readonly = true) {
    if (disabled) {
        event.preventDefault();
        return;
    }
    if (event.which === 8) {
        var plate_box_input = $(".plate-box-" + id + "-input"+uniqueId)
        var plate_box_empty = $(".plate-box-empty"+uniqueId)
        if (e.value == "") {
            if (id == "two") {
                plate_box_empty.focus()
                if (readonly) e.setAttribute("readonly", true)
            } else if (id != "") {
                plate_box_input.focus()
                if (readonly) e.setAttribute("readonly", true)
            }
        }
    }
}

/* Plate end */

function commafy(num) {
    var str = num.toString().split(".");
    if (str[0].length >= 4) {
        str[0] = str[0].replace(/(\d)(?=(\d{3})+$)/g, "$1,");
    }
    if (str[1] && str[1].length >= 5) {
        str[1] = str[1].replace(/(\d{3})/g, "$1 ");
    }
    return str.join(".");
}


function validateNosaziCode(value) {
    value = value.replace(/\s+/g, '');
    var regex = /^[\d\u06F0-\u06F9]+-[\d\u06F0-\u06F9]+(?:-[\d\u06F0-\u06F9]+)*$/;
    return regex.test(value);
}


/* Map location start */
var map
function publicMap(map_id, lat, lng, path_file, lat_id, lng_id, map_search = SEARCHMAP, markers = [],click = false, uniqueId = "") {
    if (map != undefined) map.remove();
    map = L.map(`${map_id}`, {
        measureControl: true,
        zoomControl: false,
        zoomsliderControl: false,
        attributionControl: false,
    }).setView([lat, lng], 16);
    for (var key in window["app_config"]["_map_types"]) {
        const options = window["app_config"]["_map_types"][key]["option"]
        window[window["app_config"]["_map_types"][key]["var_name"]] = L.tileLayer(window["app_config"]["_map_types"][key]["url"], options);
    }
    if (markers !== null) {
        markers.map(function (item){
            if (item.length >= 3) L.marker([item[1], item[2]], { icon:  L.icon({ iconUrl: item[0], iconSize: [27, 41] }) }).addTo(map);
        })
    }
    primaryTile.addTo(map);
    var additionalClass = uniqueId.length ? `_${uniqueId}` : '';
    $(`#change-layer${additionalClass}`).change(function () {
        if ($(`#change-layer${additionalClass}`).is(":checked")) {
            map.removeLayer(primaryTile);
            sateliteTile.addTo(map);
            $(`#change-layer${additionalClass} #change-layer-box > img`).attr("src", PATHFILE + "/assets/images/map/osm-layer.png");
            if (getCookie("theme_mode")?.length) {
                if (getCookie("theme_mode") === themeCustomDarkClass) {
                    $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
                } else {
                    $(".leaflet-map-pane").css("filter", "none");
                }
            }
        } else {
            if (getCookie("theme_mode")?.length) {
                if (getCookie("theme_mode") === themeCustomDarkClass) {
                    $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
                } else {
                    $(".leaflet-map-pane").css("filter", "none");
                }
                map.removeLayer(sateliteTile);
                primaryTile.addTo(map);
            }
            $(`#change-layer${additionalClass} #change-layer-box > img`).attr("src", PATHFILE + "/assets/images/map/google-layer.png");
        }
    });
    $(`.map_search_live_input${additionalClass}`).on("input", function (e) {
        var searchInput = $(this).val();
        var raw = JSON.stringify({
            text: searchInput,
            $filter: map_search,
        });
        var requestOptions = {
            method: "POST",
            headers: {
                "x-api-key": API_TOKEN,
                "Content-Type": "application/json",
            },
            body: raw,
            redirect: "follow",
        };
        var addresses = document.querySelector(`.map_search_live_result${additionalClass}`);
        addresses.innerHTML = `
                                        <li>
                                            <a href="javascript:void(0);">
                                                <div class="title loading_title line3 loading-animation"></div>
                                                <div class="description loading_desc line3 loading-animation"></div>
                                            </a>
                                        </li>
                                        `;
        fetch("https://map.ir/search/v2/autocomplete", requestOptions)
            .then((res) => {
                if (res.status == 200) {
                    return res.json();
                } else {
                    addresses.innerHTML = `
                                    <li>
                                        <a href="javascript:void(0);">
                                            <div class="title loading_title line3 loading-animation"></div>
                                            <div class="description loading_desc line3 loading-animation"></div>
                                        </a>
                                    </li>
                                    `;
                }
                return new Error("Error :/");
            })
            .then((data) => {
                if (data.value?.length) {
                    addresses.innerHTML = "";
                    data.value.forEach((address, index) => {
                        addresses.insertAdjacentHTML(
                            "beforeend",
                            `<li tabindex="${index + 1}">
                                <a href="javascript:void(0);" class="search-page-places-item d-flex flex-row align-items-center gap-4 px-4 py-2" data-lat="${address.geom.coordinates[0]}" data-lng="${address.geom.coordinates[1]}">
                                    <i class="fa-regular fa-location-dot fs-16"></i>
                                    <span>
                                        <h6 class="title">${address.title}</h6>
                                        <p class="description m-0">${address.title}</p>
                                    </span>
                                </a>
                            </li>
                            `
                        );
                    });
                    $(`ul.map_search_live_result .search-page-places-item`).click(function (e) {
                        var search_page_lat = $(this).attr("data-lat");
                        var search_page_lng = $(this).attr("data-lng");
                        map.setView([search_page_lng, search_page_lat], 16);
                        $(this).parents(".search-result").removeClass("show");
                        // Fill input value with selected item text
                        $(`.map_search_live_input`).val($(this).find("span .title").text());

                        $("#" + lat_id).val(search_page_lat);
                        $("#" + lng_id).val(search_page_lng);
                        $(`#location_internal_latlng${additionalClass}`).html(search_page_lat + "-" + search_page_lng);
                    });
                    if ($(`#search_result${additionalClass}`).hasClass("show")) {
                        /* Implement key up and down select start */
                        const list = document.querySelector(`ul.map_search_live_result${additionalClass}`);
                        const items = list.getElementsByTagName("li");
                        let selectedItem = null;
                        document.addEventListener("keydown", function (event) {
                            if (event.key === "ArrowDown") {
                                event.preventDefault();
                                if (selectedItem === null) {
                                    items[0].focus();
                                    selectedItem = items[0];
                                } else {
                                    const index = Array.prototype.indexOf.call(items, selectedItem);
                                    if (index < items.length - 1) {
                                        items[index + 1].focus();
                                        selectedItem = items[index + 1];
                                    }
                                }
                            } else if (event.key === "ArrowUp") {
                                event.preventDefault();
                                if (selectedItem === null) {
                                    items[items.length - 1].focus();
                                    selectedItem = items[items.length - 1];
                                } else {
                                    const index = Array.prototype.indexOf.call(items, selectedItem);
                                    if (index > 0) {
                                        items[index - 1].focus();
                                        selectedItem = items[index - 1];
                                    }
                                }
                            } else if (event.key === "Enter") {
                                event.preventDefault();
                                if (selectedItem !== null) {
                                    // Do something with the selected item
                                    selectedItem.querySelector("a").click();
                                }
                            }
                        });

                        for (let i = 0; i < items.length; i++) {
                            items[i].addEventListener("click", function () {
                                selectedItem = this;
                            });
                        }
                        /* Implement key up and down select end */
                    }
                } else {
                    addresses.innerHTML = `
                                        <li>
                                            <a href="javascript:void(0);">
                                                <div class="title loading_title line3 loading-animation"></div>
                                                <div class="description loading_desc line3 loading-animation"></div>
                                            </a>
                                        </li>
                                        `;
                }
            });
    });

    if(lat_id !== '' && lng_id !== '') {
        map.on("dragend", function (e) {
            $("#" + lat_id).val(map.getCenter().lat);
            $("#" + lng_id).val(map.getCenter().lng);
            $(`#location_internal_latlng${additionalClass}`).text(map.getCenter().lat + '-' + map.getCenter().lng);
        });
    }

    if(click) {
        map.on('click',function (e){
            var clickMarkerIcon = L.icon({ iconUrl: PATHFILE+"assets/images/marker.png" });
            L.marker([e.latlng.lat, e.latlng.lng], { icon: clickMarkerIcon }).addTo(map);
            add_lines(e.latlng.lat,e.latlng.lng)
        })
    }
    var timeoutLocation;
    var location_button = document.querySelector(`#location_button${additionalClass}`);
    if (location_button)
        location_button.addEventListener("click", function (e) {
            e.preventDefault();
            map.locate({ setView: true, maxZoom: 16 });
            if (timeoutLocation) clearTimeout(timeoutLocation);
            timeoutLocation = setTimeout(() => {
                location_button.classList.add("locate-loader")
                map.on("locationfound", function (e) {
                    location_button.classList.remove("locate-loader")
                    map.setView(e.latlng, 14);
                });
                map.on("locationerror", function (e) {
                    location_button.classList.remove("locate-loader")
                    snackbar("map_snackbar_18394829", "موقعیت مکانی شما یافت نشد.", "danger", {
                        hasIcon: true,
                    });
                });
            }, 200);
        });
    // Theme changed handle start
    if (getCookie("theme_mode")?.length) {
        if (getCookie("theme_mode") === themeCustomDarkClass) {
            $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
        } else {
            $(".leaflet-map-pane").css("filter", "none");
        }
    }
    $(document).on("themeChanged", function (e, { themeName }) {
        if (themeName === themeCustomDarkClass) {
            $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
        } else {
            $(".leaflet-map-pane").css("filter", "none");
        }
    });
}
/* Map location end */

/* Map Pane Handler start */
function handlePaneClick(paneLayer) {
    L.DomEvent.on(paneLayer, "click", function(e) {
        if (e._stopped) { return; }
    
        var target = e.target;
        var stopped;
        var removed;
        var ev = new MouseEvent(e.type, e)
    
        removed = {node: target, display: target.style.display};
        target.style.display = "none";
        target = document.elementFromPoint(e.clientX, e.clientY);
    
        if (target && target !== paneLayer) {
            stopped = !target.dispatchEvent(ev);
            if (stopped || ev._stopped) {
                L.DomEvent.stop(e);
            }
        }
    
        removed.node.style.display = removed.display;
    });
}
/* Map Pane Handler end */

/* Set textarea counter start */
function setTextCounter(targetInputId, currentDivId, maxDivId) {
    /* Characters count Start */
    $(document).ready(() => {
       $("#" + currentDivId).text($("#" + targetInputId).val().length)
       $("#" + maxDivId).text($("#" + targetInputId).attr("maxlength"))
    })
    $("#" + targetInputId).on("change keypress keyup", function (e) {
       var characterCount = $(this).val().length,
             current_count = $("#" + currentDivId),
             maximum_count = $("#" + maxDivId)
       current_count.text(characterCount)
    });
    /* Characters count End */
 }
/* Set textarea counter end */

/* Commafying the price start */
function commafy(num) {
    var str = num.toString().split(".")
    if (str[0].length >= 4) {
        str[0] = str[0].replace(/(\d)(?=(\d{3})+$)/g, "$1,")
    }
    if (str[1] && str[1].length >= 5) {
        str[1] = str[1].replace(/(\d{3})/g, "$1 ")
    }
    return str.join(".")
}
/* Commafying the price end */

function AnswerOpinionScale(tag,element_id) {
    $(tag).parents('ul').find('label').removeClass('selected-scale');
    $(tag).addClass('selected-scale');
    $('#'+element_id).val($(tag).data('answer'));
}
function file_upload(id,form_id,token,maxFileSize = null, elements_id = '', model = '') {
    var $droparea = $("#element_"+id+"_drop_area");
    var fileInput = document.getElementById("element_"+id+"_file")
    var filePreview = document.getElementById("element_"+id+"_preview")
    var fileName = document.getElementById("element_"+id+"_filename")
    var $fileDelete = $("#element_"+id+"_file_delete")
    var $result = $("#single_file_result_"+id)

    var files = fileInput.files
    var filesCount = files.length;
    if (filesCount === 1)
        {
            
            var filePath = fileInput.value;
            var extensions = fileInput.getAttribute("accept");
            if(extensions != "")
                {
                    var extensionsArray = extensions.split(",");
                    var file_extension = filePath.split(".");
                    
                    if (!extensionsArray.includes("." + file_extension[file_extension.length - 1]?.toLowerCase()))
                        {
                            snackbar("element_6598465132", "پسوند فایل مجاز نمی باشد", type = "danger", duration = 3000)
                            fileInput.value = "";
                            return false;
                        }
                }

                var fileSizeInMB = $("#element_"+id+"_file")[0].files[0].size / 1024 / 1000;
                if (maxFileSize && maxFileSize < fileSizeInMB) {
                    snackbar("element_6598654465132", `حجم فایل ارسالی باید زیر ${maxFileSize} مگابایت باشد.`, type = "danger");
                    return;
                };
                
                showLoader(id);
                $droparea.hide();
                var formData = new FormData();
                formData.append("file", $("#element_"+id+"_file")[0].files[0]);
                formData.append("token", token);
                formData.append("form_id", form_id);
                formData.append("id", id);
                formData.append("file_old",$("#element_"+id+"_hide").val());
                formData.append("show_name","true");
                if (elements_id?.length) formData.append("elements",$(`#${elements_id}`).val());

                $.ajax({
                    url  : PATHFILE+"execute/form/add/upload_file",
                    type : "POST",
                    data : formData,
                    processData: false,
                    contentType: false,
                    success : function(data) {
                        hideLoader(id);
                        var image_data = JSON.parse(data);
                        if(image_data.message !== "")
                            {
                                snackbar("element_6598654465132", image_data.message, type = "danger", duration = 3000)
                                $droparea.show();
                            }
                        else
                            {
                                $("#element_"+id+"_hide").val(image_data.name)
                                $("#element_"+id+"_hide").trigger("input");
                                if (fileName) fileName.innerText = image_data.name
                                $result.show();
                                $(document).ready(async function() {
                                    var file_types = image_data.type.split("/");
                                    
                                    if(file_types.includes("video"))
                                        {
                                            var data_video = '{"source":[{"src":"'+image_data.link+'","type":"video/mp4"}],"attributes":{"preload":true,"controls":true,"playsinline":true}}';
                                            $(`#gallery_${id}`).append('<a class="" data-lg-size="1280-720" data-video='+data_video+' data-poster="'+PATHFILE+'assets/images/icons/form-video.webp" data-sub-html="'+image_data.name+'">'+image_data.url+'</div></a>');
                                            if (window["lightGallery_listfile_"+id]) window["lightGallery_listfile_"+id].destroy();
                                            singleFileGallery = lightGallery(document.getElementById(`gallery_${id}`), {
                                                speed: 500,
                                                plugins: [lgVideo]
                                            });
                                            $(`#gallery_${id}`).on("click", () => window["lightGallery_listfile_"+id].openGallery(0))
                                            window["lightGallery_listfile_"+id] = singleFileGallery;
                                        }       
                                    else if(file_types.includes("image"))
                                        {
                                            if (window["lightGallery_listfile_"+id]) window["lightGallery_listfile_"+id].destroy();
                                            $(`#gallery_${id}`).append('<img src="'+image_data.url+'" class="w-100 object-fit-cover '+(model == 'vertical' ? 'h-100' : '')+'" id="element_'+id+'_preview" alt="">');
                                            const tifLinks = document.querySelectorAll('[href$=".tif"], [href$=".tiff"], [src$=".tif"], [src$=".tiff"]');
                                            await Promise.all(Array.from(tifLinks).map(async link => {
                                                const tifUrl = link.href || link.src;
                                                try {
                                                    const pngData = await loadTifAsPng(tifUrl);
                                                    if (link.href) link.href = pngData;
                                                    if (link.src) link.src = pngData;
                                                } catch (error) {console.error(`Failed to process ${tifUrl}:`, error)}
                                            }));
                                            singleFileGallery = lightGallery(document.getElementById(`gallery_${id}`), {
                                                plugins: [lgThumbnail, lgZoom, lgFullscreen, lgShare, lgRotate, lgAutoplay],
                                                download: true,
                                                controls: true,
                                                thumbWidth: 100,
                                                thumbHeight: 100,
                                                showZoomInOutIcons: true,
                                                actualSize: false
                                            });
                                            $(`#gallery_${id}`).on("click", () => window["lightGallery_listfile_"+id].openGallery(0))
                                            window["lightGallery_listfile_"+id] = singleFileGallery;
                                        }
                                    else
                                        {

                                            $(`#gallery_${id}`).append('<a target="_blank" href="'+image_data.link+'">'+image_data.url+'</a>')
                                        }    
                                    
                                })
                            }
                        
                    }
                });
    
                 
        }       
    $fileDelete.on("click", function () {
        $("#element_"+id+"_file").val(null);
        $("#element_"+id+"_hide").val("");
        $("#element_"+id+"_hide").trigger("input");
        $("#gallery_"+id).empty();
        $result.hide();
        $droparea.show();
    });
}


async function file_to_local(url,id,form_id,token) {
    return await new Promise((resolve, reject) => {
        var formData = new FormData();
        formData.append("token", token);
        formData.append("form_id", form_id);
        formData.append("id", id);
        formData.append("url",url);

        $.ajax({
            url  : PATHFILE+"execute/form/add/upload_file_external",
            type : "POST",
            data : formData,
            processData: false,
            contentType: false,
            success : function(data) {
                var image_data = JSON.parse(data);
                if(image_data.status == 8)
                {
                    resolve(image_data);
                }
                else
                {
                    resolve({status: 26, message: image_data.message});
                }
            },
            error: () => reject()
        });
    })
}


function dataURLToBlob(dataURL) {
    var parts = dataURL.split(';base64,');
    var contentType = parts[0].split(':')[1];
    var byteCharacters = atob(parts[1]);
    var byteArrays = [];

    for (let i = 0; i < byteCharacters.length; i += 512) {
        let slice = byteCharacters.slice(i, i + 512);
        let byteNumbers = new Array(slice.length);
        for (let j = 0; j < slice.length; j++) {
            byteNumbers[j] = slice.charCodeAt(j);
        }
        byteArrays.push(new Uint8Array(byteNumbers));
    }

    return new Blob(byteArrays, { type: contentType });
}

function uploadFileViaAjax(formData, id, onSuccess) {
    $("#multifile" + id).show();
    $("#multifile_images_" + id).hide();
    $("#multifile" + id).append('<div id="multifile_' + id + '_loader" class="loader-listfile"><span></span><span></span><span></span><span></span><span></span></div>');

    $.ajax({
        url: PATHFILE + "execute/form/add/upload_multifile",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        success: function (data) {
            $("#multifile_" + id + "_loader").remove();
            if (onSuccess && typeof onSuccess === 'function') {
                onSuccess(data);
            }
        }
    });
}

function format(value, scale, modulo, padding) {
    value = Math.floor(value / scale) % modulo;
    return value.toString().padStart(padding, 0);
}

async function option(form_element_id , set, form_id, token, options = {
    id: ""
}) {
    var formData = new FormData();
    formData.append("token", token);
    formData.append("form_id", form_id);
    formData.append("form_element_id", form_element_id);
    for (var key in options) {
        formData.append(key, options[key]);
    }
    return await $.ajax({
        url  : PATHFILE+"execute/form/option",
        type : "POST",
        data : formData,
        processData: false,
        contentType: false,
        success : function(data) {
            $("#"+set).html(data);
        }
    });
}

function prioritize_sortable(id)
{
    $("#element_ul_"+id).sortable();
    $("#element_ul_"+id).sortable().bind("sortupdate", function(e, ui) {
        var dataIDList = $("#element_ul_"+id+" li").map(function(){
            return $(this).data("id");
        }).get().join(",");
        var dataIDListTitle = $("#element_ul_"+id+" li").map(function(){
            return $(this).attr("title");
        }).get().join(",");
        $("#element_"+id+"_title").val(dataIDListTitle);
        $("#element_"+id).val(dataIDList);
    });
}
var multiGallery;
var singleFileGallery;
var listFileGallery;
function multifile_upload(id , uploadedFileCount,form_id,token,model = '',maxFileSize = null,elements_id = '') {
    if (!window["countUploadFile_"+id]) window["countUploadFile_"+id] = 1
    var multi_fileInput = document.getElementById("element_"+id+"_file");
    var filePath = multi_fileInput.value;
    var extensions = multi_fileInput.getAttribute("accept");
    let uniqueId = generateId();

    if(window["countUploadFile_"+id] && uploadedFileCount !== '' && window["countUploadFile_"+id] > uploadedFileCount)
        {
            snackbar("element_65984656465131", "سقف اپلود شما به پایان رسید", type = "danger", duration = 3000)
            return false;
        }
    if(extensions != "")
        { 
            var extensionsArray = extensions.split(","); 
            var file_extension = filePath.split(".");
            if (!extensionsArray.includes("." + file_extension[file_extension.length - 1]?.toLowerCase())) 
                {
                    snackbar("element_6598465131", "پسوند فایل مجاز نمی باشد", type = "danger", duration = 3000)
                    multi_fileInput.value = "";
                    return false;
                }
        }
    var fileSizeInMB = $("#element_"+id+"_file")[0].files[0].size / 1024 / 1000;
    if (maxFileSize && maxFileSize < fileSizeInMB) {
        snackbar("element_6598654465132", `حجم فایل ارسالی باید زیر ${maxFileSize} مگابایت باشد.`, type = "danger");
        return;
    };
    $("#multifile"+id).show();
    $("#multifile_images_" + id).hide();
    $("#multifile"+id).append('<div id="multifile_' + id + '_loader" class="loader-listfile"><span></span><span></span><span></span><span></span><span></span></div>');
    var formData = new FormData();
    formData.append("file", $("#element_"+id+"_file")[0].files[0]);
    formData.append("token", token);
    formData.append("form_id", form_id);
    formData.append("id", id);
    formData.append("show_name","true");
    window["countUploadFile_"+id]++;
    if (elements_id?.length) formData.append("elements",$(`#${elements_id}`).val());
    $.ajax({
        url  : PATHFILE+"execute/form/add/upload_multifile",
        type : "POST",
        data : formData,
        processData: false,
        contentType: false,
        success : async function(data) {
            var image_data = JSON.parse(data);
                if(image_data.message !== "")
                    {
                        snackbar("element_6598463215132",image_data.message , type = "danger", duration = 3000)
                        $("#multifile_" + id + "_loader").remove();
                    }
                else
                    {

                        $("#multifile_" + id + "_loader").remove();
                        $("#multifile_images_" + id).show();
                        var file_types = image_data.type.split("/");
                        var file_rand = "'"+image_data.file_rand+"'";
                        var file_name = "'"+image_data.name+"'";
                        if(file_types.includes("video"))
                            {
                                var file_seneded_type = "video";
                                var data_video = '{"source":[{"src":"'+image_data.link+'","type":"video/mp4"}],"attributes":{"preload":true,"controls":true,"playsinline":true}}';
                                if (model != 'vertical') $("#multifile_images_" +id).append('<div class="picture-box" id="picture_box_'+uniqueId+'_'+id+'" data-lg-size="1280-720" data-video='+data_video+'  data-sub-html="'+image_data.name+'">'+image_data.url+'<button type="button" class="picture-box-remove" onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+image_data.name+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')"><i class="fa-solid fa-trash-alt"></i></button></div>');
                                else $("#multifile_images_" +id).append('<div id="picture_box_'+uniqueId+'_'+id+'" class="images_item form-gallery-item p-2  rounded-3 shadow border position-relative"  href="'+image_data.url+'"> <div class="w-100 h-100 d-flex"> '+image_data.url+' </div> <div onclick="$(`#gallery_'+id+'`).click()" class="images_overlay position-absolute start-0 bottom-0 top-0 end-0 h-100 rounded-3 d-flex align-items-center justify-content-center"> <i class="fa-solid fa-search fs-25 text-white"></i> <div onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+image_data.name+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')" class="item-delete ms-auto position-absolute top-0 end-0 text-red-600 bg-red-200 p-1 m-1"> <i class="fa-regular fa-trash-alt g-center"></i> </div> </div> </div>');

                                if (multiGallery)
                                    multiGallery.destroy();
                                multiGallery = lightGallery(document.getElementById("multifile_images_"+ id), {
                                    speed: 500,
                                    plugins: [lgVideo]
                                    });
                                
                            }       
                        else if(file_types.includes("image"))
                            {
                                var file_seneded_type = "image";
                                if (model != 'vertical') $("#multifile_images_" +id).append('<div class="picture-box" id="picture_box_'+uniqueId+'_'+id+'" href="'+image_data.link+'"><figure><img src="'+image_data.url+'"></figure><button type="button" class="picture-box-remove" onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+image_data.name+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')"><i class="fa-solid fa-trash-alt"></i></button></div>');
                                else $("#multifile_images_" +id).append('<div id="picture_box_'+uniqueId+'_'+id+'" class="images_item form-gallery-item p-2  rounded-3 shadow border position-relative"  href="'+image_data.url+'"> <div class="w-100 h-100 d-flex"> <img src="'+image_data.url+'" class="w-100 h-100 object-fit-cover"> </div> <div onclick="$(`#gallery_'+id+'`).click()" class="images_overlay position-absolute start-0 bottom-0 top-0 end-0 h-100 rounded-3 d-flex align-items-center justify-content-center"> <i class="fa-solid fa-search fs-25 text-white"></i> <div onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+image_data.name+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')" class="item-delete ms-auto position-absolute top-0 end-0 text-red-600 bg-red-200 p-1 m-1"> <i class="fa-regular fa-trash-alt g-center"></i> </div> </div> </div>');
                                const tifLinks = document.querySelectorAll('[href$=".tif"], [href$=".tiff"], [src$=".tif"], [src$=".tiff"]');
                                await Promise.all(Array.from(tifLinks).map(async link => {
                                    const tifUrl = link.href || link.src;
                                    try {
                                        const pngData = await loadTifAsPng(tifUrl);
                                        if (link.href) link.href = pngData;
                                        if (link.src) link.src = pngData;
                                    } catch (error) {console.error(`Failed to process ${tifUrl}:`, error)}
                                }));
                                if (multiGallery)
                                    multiGallery.destroy();
                                multiGallery = lightGallery(document.getElementById("multifile_images_"+ id), {
                                    plugins: [lgThumbnail, lgZoom, lgFullscreen, lgShare, lgRotate, lgAutoplay],
                                    download: true,
                                    controls: true,
                                    thumbWidth: 100,
                                    thumbHeight: 100,
                                    showZoomInOutIcons: true,
                                    actualSize: false
                                });
                    
                            }
                        else
                            {
                                var file_seneded_type = "other";
                                $("#multifile_images_" +id).append('<div class="position-relative" id="picture_box_'+uniqueId+'_'+id+'"><a class="picture-box  d-block"  href="'+image_data.link+'"><figure>'+image_data.url+'</figure></a><button type="button" class="picture-box-remove" onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+image_data.name+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')"><i class="fa-solid fa-trash-alt"></i></button></div>');
                            }  
                        var data1 = $("#element_"+id+"_hide").val();
                        if(data1 == "")
                            $("#element_"+id+"_hide").val(image_data.name);        
                        else
                            $("#element_"+id+"_hide").val(data1+","+image_data.name);
                        $("#element_"+id+"_hide").trigger("input");
                        window["countUploadFile_"+id]++; 
                    }                                                
        },
        error: () => window["countUploadFile_"+id]--
    });      
}


function handleMultifileUpload(form_id, token, uploadFileCount = '', scannedImage, id) {
    const fileInput = document.getElementById("element_" + id + "_file");

    const fileName = `scanned_${Date.now()}.jpg`;
    const blob = dataURLToBlob(scannedImage.src);
    const file = new File([blob], fileName, { type: "image/jpeg" });

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;

    multifile_upload(id, uploadFileCount, form_id, token, '');
}

function handleFileUpload(form_id, token, scannedImage, id) {
    const fileInput = document.getElementById("element_" + id + "_file");
    const fileName = `scanned_${Date.now()}.jpg`;
    const blob = dataURLToBlob(scannedImage.src); // convert base64 to Blob
    const file = new File([blob], fileName, { type: "image/jpeg" });
    // Simulate user upload via DataTransfer
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;

    // Trigger the existing upload logic
    file_upload(id, form_id, token);
}

function multifile_delete(event,id,div_id,file_name , file_seneded_type,form_id,token) {
    event.preventDefault();
    $("#picture_box_"+id).remove();
    id = id.includes("_") ? id.split("_")[1] : id;
    var str = $("#element_"+id+"_hide").val();
    var res = str.replace(file_name, "").replaceAll(/^,+|,+$/g, "").replaceAll(",,", ",");
    $("#element_"+id+"_hide").val(res);
    $("#element_"+id+"_hide").trigger("input");
    if(file_seneded_type == "image")
        {
            multiGallery.destroy();
            if($("#multifile_images_"+id).children("div").length == 0)
                {
                    $("#multifile" +id).hide();   
                }
            multiGallery = lightGallery(document.getElementById("multifile_images_"+ id), {
                plugins: [lgThumbnail, lgZoom, lgFullscreen, lgShare, lgRotate, lgAutoplay],
                download: true,
                controls: true,
                thumbWidth: 100,
                thumbHeight: 100,
                showZoomInOutIcons: true,
                actualSize: false
            });
        }
    else if(file_seneded_type == "video")
        {
            multiGallery.destroy();
            if($("#multifile_images_"+id).children("div").length == 0)
                {
                    $("#multifile" +id).hide();   
                }
            multiGallery = lightGallery(document.getElementById("multifile_images_"+ id), {
                speed: 500,
                plugins: [lgVideo]
                });
        }
    $.ajax({
        url: PATHFILE+"execute/form/add/delete_multifile",
        data:"id="+id+"&file_name="+file_name+"&token="+token+"&form_id="+form_id,cache:"false",type:"Post",
        success:function(html){
            window["countUploadFile_"+id]--;
            $("#as").html(html);
        }
    });
    
}

async function archive_upload(id,name,file,type='listfile',form_id='',token='',model='') {
    if ($(event.target).hasClass("content-shadow-item")) $(event.target).attr("disabled", true)
    else $(event.target).parent(".content-shadow-item").css("pointer-events", 'none')
    let uniqueId = generateId();
    if (type == 'listfile') {
        const result = await fetch(file).then(res => res);
        var type = result.headers.get("Content-type");
        var file_types = type.split("/");
        var file_rand = "'"+parseInt(Math.random() * 10000)+"'";
        var file_name = "'"+name+"'";
        var $droparea = $("#element_"+id+"_drop_area");
        var fileInput = document.getElementById("element_"+id+"_file")
        var filePreview = document.getElementById("element_"+id+"_preview")
        var fileName = document.getElementById("element_"+id+"_filename")
        var $fileDelete = $("#element_"+id+"_file_delete")
        var $result = $("#single_file_result_"+id)
        $("#element_"+id+"_hide").val(file);
        $("#element_"+id+"_hide").trigger("input");
        $droparea.hide();
        if (fileName) fileName.innerText = name
        $result.show();
        if(file_types.includes("video"))
            {
                var data_video = '{"source":[{"src":"'+file+'","type":"video/mp4"}],"attributes":{"preload":true,"controls":true,"playsinline":true}}';
                // $(`#gallery_${id}`).append('<div id="picture_box_'+uniqueId+'_'+id+'" data-lg-size="1280-720" data-video='+data_video+'  data-sub-html="'+name+'"><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width=" 100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Zm-77-20.83c-.6,0-1.19-.17-1.71-.48-.97-.6-1.54-1.66-1.51-2.8v-38.42c-.03-1.14.55-2.2,1.51-2.8.94-.59,2.12-.64,3.11-.14l39.2,19.24c1.59.79,2.24,2.72,1.45,4.32-.31.63-.82,1.14-1.45,1.45l-39.2,19.24c-.43.24-.91.37-1.4.39Zm3.22-36.54v28.14l28.59-14-28.59-14.14Z"></path></g></svg></div>');
                if (model != 'vertical') $(`#gallery_${id}`).append('<div id="picture_box_'+uniqueId+'_'+id+'" data-lg-size="1280-720" data-video='+data_video+'  data-sub-html="'+name+'"><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width=" 100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Zm-77-20.83c-.6,0-1.19-.17-1.71-.48-.97-.6-1.54-1.66-1.51-2.8v-38.42c-.03-1.14.55-2.2,1.51-2.8.94-.59,2.12-.64,3.11-.14l39.2,19.24c1.59.79,2.24,2.72,1.45,4.32-.31.63-.82,1.14-1.45,1.45l-39.2,19.24c-.43.24-.91.37-1.4.39Zm3.22-36.54v28.14l28.59-14-28.59-14.14Z"></path></g></svg></div>');
                else $("#gallery_" +id).append('<div id="picture_box_'+uniqueId+'_'+id+'" class="images_item form-gallery-item p-2  rounded-3 shadow border position-relative"  href="'+image_data.url+'"> <div class="w-100 h-100 d-flex"><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width=" 100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Zm-77-20.83c-.6,0-1.19-.17-1.71-.48-.97-.6-1.54-1.66-1.51-2.8v-38.42c-.03-1.14.55-2.2,1.51-2.8.94-.59,2.12-.64,3.11-.14l39.2,19.24c1.59.79,2.24,2.72,1.45,4.32-.31.63-.82,1.14-1.45,1.45l-39.2,19.24c-.43.24-.91.37-1.4.39Zm3.22-36.54v28.14l28.59-14-28.59-14.14Z"></path></g></svg></div> <div onclick="$(`#gallery_'+id+'`).click()" class="images_overlay position-absolute start-0 bottom-0 top-0 end-0 h-100 rounded-3 d-flex align-items-center justify-content-center"> <i class="fa-solid fa-search fs-25 text-white"></i> <div onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+file+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')" class="item-delete ms-auto position-absolute top-0 end-0 text-red-600 bg-red-200 p-1 m-1"> <i class="fa-regular fa-trash-alt g-center"></i> </div> </div> </div>');

                if (listFileGallery) listFileGallery.destroy();
                listFileGallery = lightGallery(document.getElementById(`gallery_${id}`), {
                    speed: 500,
                    plugins: [lgVideo]
                });
            }
        else if(file_types.includes("image"))
            {
                $(`#gallery_${id}`).append('<img src="'+file+'" class="w-100 '+(model == 'vertical' ? 'h-100' : '')+' object-fit-cover" id="element_'+id+'_preview" alt="">');
                const tifLinks = document.querySelectorAll('[href$=".tif"], [href$=".tiff"], [src$=".tif"], [src$=".tiff"]');
                await Promise.all(Array.from(tifLinks).map(async link => {
                    const tifUrl = link.href || link.src;
                    try {
                        const pngData = await loadTifAsPng(tifUrl);
                        if (link.href) link.href = pngData;
                        if (link.src) link.src = pngData;
                    } catch (error) {console.error(`Failed to process ${tifUrl}:`, error)}
                }));
                if (listFileGallery) listFileGallery.destroy();
                listFileGallery = lightGallery(document.getElementById(`gallery_${id}`), {
                    plugins: [lgThumbnail, lgZoom, lgFullscreen, lgShare, lgRotate, lgAutoplay],
                    download: true,
                    controls: true,
                    thumbWidth: 100,
                    thumbHeight: 100,
                    showZoomInOutIcons: true,
                    actualSize: false
                });
            }
        else if(file_types.includes("audio")) $(`#gallery_${id}`).append('<a target="_blank" href="'+file+'"><svg id="Layer_2" data2-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32.14 40" width=" 100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m8.28,0L0,8.28v28.15c0,1.97,1.6,3.57,3.57,3.57h25c1.97,0,3.57-1.6,3.57-3.57V3.57c0-1.97-1.6-3.57-3.57-3.57M7.84,2.44v3.76c.02.95-1.05,1.66-1.94,1.66h-3.46L7.84,2.44Zm22.88,33.99c0,1.18-.96,2.14-2.14,2.14H3.57c-1.18,0-2.14-.96-2.14-2.14h0V13.57h29.29v22.86Zm-14.14-18.97h0c-.06,0-.11,0-.17,0-.05,0-.1,0-.15,0-.32.1-.54.38-.56.71l-.22,2.96h0l-.46,6.01c-1.43-.05-5,.14-5.55,3.2-.21.95.21,1.92,1.04,2.42.56.34,1.21.51,1.86.5.9,0,1.77-.28,2.51-.79.92-.67,1.5-1.72,1.57-2.86,0-.04,0-.09,0-.13l.59-7.35c1.62.55,3.1,1.45,4.33,2.64.15.15.36.24.57.24.12,0,.23-.03.34-.07.3-.14.49-.45.48-.79-.03-3.49-2.7-6.38-6.17-6.7Zm-2.64,13.74c-.74.53-1.71.62-2.53.24-.26-.14-.39-.43-.33-.71.3-1.63,2.44-1.86,3.57-1.86h.14c.17.88-.16,1.78-.86,2.34Zm3.25-10.71l.07-1.19c1.52.37,2.78,1.43,3.42,2.86-1.06-.77-2.25-1.32-3.52-1.63l.03-.04Z"></path></g></svg></a>');
        else if(file_types.includes("application")) $(`#gallery_${id}`).append('<a target="_blank" href="'+file+'"><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width="100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m37.13,138.18c-2.43.03-4.76-1-6.38-2.81-2.94-3.83-2.45-9.28,1.12-12.53,2.61-2.81,9.97-5.84,18.46-8.43,1.87-4.83,3.85-10.77,5.93-17.81-2.33-5.9-3.66-12.15-3.93-18.49-.39-7.59,3.65-11.91,7.84-12.28,3.32-.28,7.22,2.08,7.95,7.89h0c.29,2.67.04,5.38-.76,7.95l-1.07,3.68c-1.04,3.65-2.08,7.3-3.15,10.87,2.16,4.81,5.11,9.22,8.71,13.06,3.92-.76,7.89-1.22,11.88-1.38,8.18,0,11.24,3.71,12.47,5.9,1.46,2.66,1.31,5.91-.37,8.43-1.85,2.66-5.02,4.07-8.23,3.68-6.75-1.43-12.94-4.79-17.81-9.66-4.69.96-9.78,2.19-14.55,3.54-3.01,7.44-5.98,12.9-8.91,14.95-2.64,2.07-5.86,3.27-9.21,3.43Zm10.06-15.9c-3.81,1.03-7.41,2.75-10.59,5.09-1.4,1.52-1.6,3.15-.98,3.88s3.12.96,7-1.77c2.03-2.03,3.6-4.49,4.58-7.19Zm30.9-7.44c2.97,2.35,6.47,3.94,10.2,4.64.85.17,1.73-.14,2.28-.81.33-.54.33-1.23,0-1.77-.31-.59-1.69-2.44-6.8-2.47-1.89.05-3.78.22-5.65.51l-.03-.08Zm-17.64-9.83c-.84,2.56-1.66,5.03-2.47,7.39,2.22-.59,4.44-1.12,6.63-1.6-1.5-1.84-2.88-3.77-4.13-5.79h-.03Zm.25-32.62h0c-.65,0-2.11,1.74-1.94,5.62.12,2.47.41,4.93.87,7.36.14-.53.31-1.04.45-1.57l1.07-3.71c.54-1.72.73-3.54.56-5.34h0c-.22-1.8-.84-2.36-.98-2.36h-.03ZM112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Z"></path></g></svg></a>');
        else $(`#gallery_${id}`).append('<a target="_blank" href="'+file+'"><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width="100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.26,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14Zm-19.15,22.92c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-16.52,0c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-16.52,0c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-29.01-13.37v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.56L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4V53.2h114.8v89.6Zm-18.76-20.03c0,.91-.37,1.73-.96,2.32-.59.59-1.41.96-2.32.96s-1.73-.37-2.32-.96c-.59-.59-.96-1.41-.96-2.32s.37-1.72.96-2.31c.59-.6,1.41-.96,2.32-.96,1.81,0,3.28,1.46,3.28,3.27Zm12.45-32.1c0,2.05-.56,4.12-1.66,6.19-1.1,2.07-3.04,3.95-5.81,5.63-2.12,1.69-3.37,2.8-3.74,3.35-.37.54-.74,1.14-1.1,1.8-.36.65-.62,1.87-.8,3.63v.53c0,1.54-1.24,2.78-2.78,2.78-.77,0-1.47-.31-1.97-.81s-.82-1.2-.82-1.97v-.03c-.11-1.47,0-2.93.33-4.39.74-2.43,1.94-4.39,3.6-5.9,2.54-2.18,4.64-4.08,6.33-5.68,1.68-1.61,2.52-3.36,2.52-5.26,0-2.34-.96-4.27-2.87-5.79-1.91-1.51-4.12-2.27-6.63-2.27s-4.42.77-6.06,2.31c-1.27,1.19-2.28,2.86-3.02,5.02-.41,1.18-1.61,1.91-2.86,1.8h-.06c-1.74-.17-2.93-1.89-2.42-3.57.73-2.42,1.99-4.59,3.77-6.51,2.56-2.75,6.11-4.13,10.65-4.13s8.52,1.24,11.27,3.73,4.13,5.67,4.13,9.54Zm-31.48-10.46c0,1.78-1.44,3.22-3.22,3.22h-44.38c-1.78,0-3.22-1.44-3.22-3.22s1.44-3.22,3.22-3.22h44.38c1.78,0,3.22,1.44,3.22,3.22Zm-54.55,0c0,1.78-1.44,3.22-3.22,3.22h-7.98c-1.78,0-3.23-1.44-3.23-3.22s1.44-3.22,3.22-3.22h7.99c1.78,0,3.23,1.44,3.22,3.22Zm34.69,21.3c0,1.78-1.44,3.22-3.22,3.22H16.86c-1.78,0-3.22-1.45-3.22-3.23s1.44-3.22,3.22-3.22h42.67c1.78,0,3.23,1.45,3.22,3.23Zm26.52,21.29c0,1.78-1.44,3.22-3.22,3.22h-45.23c-1.78.01-3.23-1.44-3.23-3.22s1.44-3.22,3.22-3.22h45.23c1.78,0,3.23,1.44,3.23,3.22Zm-57,0c0,1.78-1.44,3.22-3.22,3.22h-12.19c-1.78,0-3.22-1.44-3.22-3.22s1.44-3.22,3.22-3.22h12.19c1.78,0,3.22,1.44,3.22,3.22Z"></path></g></svg></a>');
        $fileDelete.on("click", function () {
            $("#element_"+id+"_file").val(null);
            $("#element_"+id+"_hide").val("");
            $("#element_"+id+"_hide").trigger("input");
            $("#gallery_"+id).empty();
            $result.hide();
            $droparea.show();
        });
    } else if (type == 'file') {
        const result = await fetch(file).then(res => res);
        var type = result.headers.get("Content-type");
        var file_types = type.split("/");
        var file_rand = "'"+parseInt(Math.random() * 10000)+"'";
        var file_name = "'"+name+"'";
        var $droparea = $("#element_"+id+"_drop_area");
        var fileInput = document.getElementById("element_"+id+"_file")
        var filePreview = document.getElementById("element_"+id+"_preview")
        var fileName = document.getElementById("element_"+id+"_filename")
        var $fileDelete = $("#element_"+id+"_file_delete")
        var $result = $("#single_file_result_"+id)
        $("#element_"+id+"_hide").val(file);
        $("#element_"+id+"_hide").trigger("input");
        $droparea.hide();
        if (fileName) fileName.innerText = name
        $result.show();
        if(file_types.includes("video"))
            {
                var data_video = '{"source":[{"src":"'+file+'","type":"video/mp4"}],"attributes":{"preload":true,"controls":true,"playsinline":true}}';
                // $(`#gallery_${id}`).append('<div id="picture_box_'+uniqueId+'_'+id+'" data-lg-size="1280-720" data-video='+data_video+'  data-sub-html="'+name+'"><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width=" 100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Zm-77-20.83c-.6,0-1.19-.17-1.71-.48-.97-.6-1.54-1.66-1.51-2.8v-38.42c-.03-1.14.55-2.2,1.51-2.8.94-.59,2.12-.64,3.11-.14l39.2,19.24c1.59.79,2.24,2.72,1.45,4.32-.31.63-.82,1.14-1.45,1.45l-39.2,19.24c-.43.24-.91.37-1.4.39Zm3.22-36.54v28.14l28.59-14-28.59-14.14Z"></path></g></svg></div>');

                if (model != 'vertical') $(`#gallery_${id}`).append('<div id="picture_box_'+uniqueId+'_'+id+'" data-lg-size="1280-720" data-video='+data_video+'  data-sub-html="'+name+'"><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width=" 100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Zm-77-20.83c-.6,0-1.19-.17-1.71-.48-.97-.6-1.54-1.66-1.51-2.8v-38.42c-.03-1.14.55-2.2,1.51-2.8.94-.59,2.12-.64,3.11-.14l39.2,19.24c1.59.79,2.24,2.72,1.45,4.32-.31.63-.82,1.14-1.45,1.45l-39.2,19.24c-.43.24-.91.37-1.4.39Zm3.22-36.54v28.14l28.59-14-28.59-14.14Z"></path></g></svg></div>');
                else $("#gallery_" +id).append('<div id="picture_box_'+uniqueId+'_'+id+'" class="images_item form-gallery-item p-2  rounded-3 shadow border position-relative"  href="'+image_data.url+'"> <div class="w-100 h-100 d-flex"><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width=" 100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Zm-77-20.83c-.6,0-1.19-.17-1.71-.48-.97-.6-1.54-1.66-1.51-2.8v-38.42c-.03-1.14.55-2.2,1.51-2.8.94-.59,2.12-.64,3.11-.14l39.2,19.24c1.59.79,2.24,2.72,1.45,4.32-.31.63-.82,1.14-1.45,1.45l-39.2,19.24c-.43.24-.91.37-1.4.39Zm3.22-36.54v28.14l28.59-14-28.59-14.14Z"></path></g></svg></div> <div onclick="$(`#gallery_'+id+'`).click()" class="images_overlay position-absolute start-0 bottom-0 top-0 end-0 h-100 rounded-3 d-flex align-items-center justify-content-center"> <i class="fa-solid fa-search fs-25 text-white"></i> <div onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+file+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')" class="item-delete ms-auto position-absolute top-0 end-0 text-red-600 bg-red-200 p-1 m-1"> <i class="fa-regular fa-trash-alt g-center"></i> </div> </div> </div>');

                if (window["lightGallery_listfile_"+id]) window["lightGallery_listfile_"+id].destroy();
                singleFileGallery = lightGallery(document.getElementById(`gallery_${id}`), {
                    speed: 500,
                    plugins: [lgVideo]
                });
            }
        else if(file_types.includes("image"))
            {
                $(`#gallery_${id}`).append('<img src="'+file+'" class="w-100 '+(model == 'vertical' ? 'h-100' : '')+' object-fit-cover" id="element_'+id+'_preview" alt="">');
                const tifLinks = document.querySelectorAll('[href$=".tif"], [href$=".tiff"], [src$=".tif"], [src$=".tiff"]');
                await Promise.all(Array.from(tifLinks).map(async link => {
                    const tifUrl = link.href || link.src;
                    try {
                        const pngData = await loadTifAsPng(tifUrl);
                        if (link.href) link.href = pngData;
                        if (link.src) link.src = pngData;
                    } catch (error) {console.error(`Failed to process ${tifUrl}:`, error)}
                }));
                if (window["lightGallery_listfile_"+id]) window["lightGallery_listfile_"+id].destroy();
                singleFileGallery = lightGallery(document.getElementById(`gallery_${id}`), {
                    plugins: [lgThumbnail, lgZoom, lgFullscreen, lgShare, lgRotate, lgAutoplay],
                    download: true,
                    controls: true,
                    thumbWidth: 100,
                    thumbHeight: 100,
                    showZoomInOutIcons: true,
                    actualSize: false
                });
            }
            else if(file_types.includes("audio")) $(`#gallery_${id}`).append('<a target="_blank" href="'+file+'"><svg id="Layer_2" data2-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32.14 40" width=" 100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m8.28,0L0,8.28v28.15c0,1.97,1.6,3.57,3.57,3.57h25c1.97,0,3.57-1.6,3.57-3.57V3.57c0-1.97-1.6-3.57-3.57-3.57M7.84,2.44v3.76c.02.95-1.05,1.66-1.94,1.66h-3.46L7.84,2.44Zm22.88,33.99c0,1.18-.96,2.14-2.14,2.14H3.57c-1.18,0-2.14-.96-2.14-2.14h0V13.57h29.29v22.86Zm-14.14-18.97h0c-.06,0-.11,0-.17,0-.05,0-.1,0-.15,0-.32.1-.54.38-.56.71l-.22,2.96h0l-.46,6.01c-1.43-.05-5,.14-5.55,3.2-.21.95.21,1.92,1.04,2.42.56.34,1.21.51,1.86.5.9,0,1.77-.28,2.51-.79.92-.67,1.5-1.72,1.57-2.86,0-.04,0-.09,0-.13l.59-7.35c1.62.55,3.1,1.45,4.33,2.64.15.15.36.24.57.24.12,0,.23-.03.34-.07.3-.14.49-.45.48-.79-.03-3.49-2.7-6.38-6.17-6.7Zm-2.64,13.74c-.74.53-1.71.62-2.53.24-.26-.14-.39-.43-.33-.71.3-1.63,2.44-1.86,3.57-1.86h.14c.17.88-.16,1.78-.86,2.34Zm3.25-10.71l.07-1.19c1.52.37,2.78,1.43,3.42,2.86-1.06-.77-2.25-1.32-3.52-1.63l.03-.04Z"></path></g></svg></a>');
            else if(file_types.includes("application")) $(`#gallery_${id}`).append('<a target="_blank" href="'+file+'"><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width="100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m37.13,138.18c-2.43.03-4.76-1-6.38-2.81-2.94-3.83-2.45-9.28,1.12-12.53,2.61-2.81,9.97-5.84,18.46-8.43,1.87-4.83,3.85-10.77,5.93-17.81-2.33-5.9-3.66-12.15-3.93-18.49-.39-7.59,3.65-11.91,7.84-12.28,3.32-.28,7.22,2.08,7.95,7.89h0c.29,2.67.04,5.38-.76,7.95l-1.07,3.68c-1.04,3.65-2.08,7.3-3.15,10.87,2.16,4.81,5.11,9.22,8.71,13.06,3.92-.76,7.89-1.22,11.88-1.38,8.18,0,11.24,3.71,12.47,5.9,1.46,2.66,1.31,5.91-.37,8.43-1.85,2.66-5.02,4.07-8.23,3.68-6.75-1.43-12.94-4.79-17.81-9.66-4.69.96-9.78,2.19-14.55,3.54-3.01,7.44-5.98,12.9-8.91,14.95-2.64,2.07-5.86,3.27-9.21,3.43Zm10.06-15.9c-3.81,1.03-7.41,2.75-10.59,5.09-1.4,1.52-1.6,3.15-.98,3.88s3.12.96,7-1.77c2.03-2.03,3.6-4.49,4.58-7.19Zm30.9-7.44c2.97,2.35,6.47,3.94,10.2,4.64.85.17,1.73-.14,2.28-.81.33-.54.33-1.23,0-1.77-.31-.59-1.69-2.44-6.8-2.47-1.89.05-3.78.22-5.65.51l-.03-.08Zm-17.64-9.83c-.84,2.56-1.66,5.03-2.47,7.39,2.22-.59,4.44-1.12,6.63-1.6-1.5-1.84-2.88-3.77-4.13-5.79h-.03Zm.25-32.62h0c-.65,0-2.11,1.74-1.94,5.62.12,2.47.41,4.93.87,7.36.14-.53.31-1.04.45-1.57l1.07-3.71c.54-1.72.73-3.54.56-5.34h0c-.22-1.8-.84-2.36-.98-2.36h-.03ZM112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Z"></path></g></svg></a>');
        else $(`#gallery_${id}`).append('<a target="_blank" href="'+file+'"><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width="100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.26,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14Zm-19.15,22.92c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-16.52,0c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-16.52,0c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-29.01-13.37v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.56L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4V53.2h114.8v89.6Zm-18.76-20.03c0,.91-.37,1.73-.96,2.32-.59.59-1.41.96-2.32.96s-1.73-.37-2.32-.96c-.59-.59-.96-1.41-.96-2.32s.37-1.72.96-2.31c.59-.6,1.41-.96,2.32-.96,1.81,0,3.28,1.46,3.28,3.27Zm12.45-32.1c0,2.05-.56,4.12-1.66,6.19-1.1,2.07-3.04,3.95-5.81,5.63-2.12,1.69-3.37,2.8-3.74,3.35-.37.54-.74,1.14-1.1,1.8-.36.65-.62,1.87-.8,3.63v.53c0,1.54-1.24,2.78-2.78,2.78-.77,0-1.47-.31-1.97-.81s-.82-1.2-.82-1.97v-.03c-.11-1.47,0-2.93.33-4.39.74-2.43,1.94-4.39,3.6-5.9,2.54-2.18,4.64-4.08,6.33-5.68,1.68-1.61,2.52-3.36,2.52-5.26,0-2.34-.96-4.27-2.87-5.79-1.91-1.51-4.12-2.27-6.63-2.27s-4.42.77-6.06,2.31c-1.27,1.19-2.28,2.86-3.02,5.02-.41,1.18-1.61,1.91-2.86,1.8h-.06c-1.74-.17-2.93-1.89-2.42-3.57.73-2.42,1.99-4.59,3.77-6.51,2.56-2.75,6.11-4.13,10.65-4.13s8.52,1.24,11.27,3.73,4.13,5.67,4.13,9.54Zm-31.48-10.46c0,1.78-1.44,3.22-3.22,3.22h-44.38c-1.78,0-3.22-1.44-3.22-3.22s1.44-3.22,3.22-3.22h44.38c1.78,0,3.22,1.44,3.22,3.22Zm-54.55,0c0,1.78-1.44,3.22-3.22,3.22h-7.98c-1.78,0-3.23-1.44-3.23-3.22s1.44-3.22,3.22-3.22h7.99c1.78,0,3.23,1.44,3.22,3.22Zm34.69,21.3c0,1.78-1.44,3.22-3.22,3.22H16.86c-1.78,0-3.22-1.45-3.22-3.23s1.44-3.22,3.22-3.22h42.67c1.78,0,3.23,1.45,3.22,3.23Zm26.52,21.29c0,1.78-1.44,3.22-3.22,3.22h-45.23c-1.78.01-3.23-1.44-3.23-3.22s1.44-3.22,3.22-3.22h45.23c1.78,0,3.23,1.44,3.23,3.22Zm-57,0c0,1.78-1.44,3.22-3.22,3.22h-12.19c-1.78,0-3.22-1.44-3.22-3.22s1.44-3.22,3.22-3.22h12.19c1.78,0,3.22,1.44,3.22,3.22Z"></path></g></svg></a>');
        $fileDelete.on("click", function () {
            $("#element_"+id+"_file").val(null);
            $("#element_"+id+"_hide").val("");
            $("#element_"+id+"_hide").trigger("input");
            $("#gallery_"+id).empty();
            $result.hide();
            $droparea.show();
        });
    } else if (type == 'multifile') {
        const result = await fetch(file).then(res => res);
        $("#multifile_" + id + "_loader").remove();
        $("#multifile_images_" + id).show();
        $("#multifile" + id).show();
        var type = result.headers.get("Content-type");
        var file_types = type.split("/");
        var file_rand = "'"+parseInt(Math.random() * 10000)+"'";
        var file_name = "'"+name+"'";
        if(file_types.includes("video"))
            {
                var file_seneded_type = "video";
                var data_video = '{"source":[{"src":"'+file+'","type":"video/mp4"}],"attributes":{"preload":true,"controls":true,"playsinline":true}}';
                // $("#multifile_images_" +id).append('<div class="picture-box" id="picture_box_'+uniqueId+'_'+id+'" data-lg-size="1280-720" data-video='+data_video+'  data-sub-html="'+name+'">'+'<svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width=" 100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Zm-77-20.83c-.6,0-1.19-.17-1.71-.48-.97-.6-1.54-1.66-1.51-2.8v-38.42c-.03-1.14.55-2.2,1.51-2.8.94-.59,2.12-.64,3.11-.14l39.2,19.24c1.59.79,2.24,2.72,1.45,4.32-.31.63-.82,1.14-1.45,1.45l-39.2,19.24c-.43.24-.91.37-1.4.39Zm3.22-36.54v28.14l28.59-14-28.59-14.14Z"></path></g></svg>'+'<button type="button" class="picture-box-remove" onclick="event.stopPropagation();multifile_delete(event,'+id+','+file_rand+','+file+' , \''+file_seneded_type+'\')"><i class="fa-solid fa-trash-alt"></i></button></div>');

                if (model != 'vertical') $("#multifile_images_" +id).append('<div class="picture-box" id="picture_box_'+uniqueId+'_'+id+'" data-lg-size="1280-720" data-video='+data_video+'  data-sub-html="'+image_data.name+'">'+image_data.url+'<button type="button" class="picture-box-remove" onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+file+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')"><i class="fa-solid fa-trash-alt"></i></button></div>');
                else $("#multifile_images_" +id).append('<div id="picture_box_'+uniqueId+'_'+id+'" class="images_item form-gallery-item p-2  rounded-3 shadow border position-relative"  href="'+image_data.url+'"> <div class="w-100 h-100 d-flex"> '+image_data.url+' </div> <div onclick="$(`#multifile_images_'+id+'`).click()" class="images_overlay position-absolute start-0 bottom-0 top-0 end-0 h-100 rounded-3 d-flex align-items-center justify-content-center"> <i class="fa-solid fa-search fs-25 text-white"></i> <div onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+file+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')" class="item-delete ms-auto position-absolute top-0 end-0 text-red-600 bg-red-200 p-1 m-1"> <i class="fa-regular fa-trash-alt g-center"></i> </div> </div> </div>');

                if (multiGallery)
                    multiGallery.destroy();
                multiGallery = lightGallery(document.getElementById("multifile_images_"+ id), {
                    speed: 500,
                    plugins: [lgVideo]
                });
            }
        else if(file_types.includes("image"))
            {
                var file_seneded_type = "image";
                if (model != 'vertical') $("#multifile_images_" +id).append('<div class="picture-box" id="picture_box_'+uniqueId+'_'+id+'" href="'+file+'"><figure><img src="'+file+'"></figure><button type="button" class="picture-box-remove" onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+file+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')"><i class="fa-solid fa-trash-alt"></i></button></div>');
                else $("#multifile_images_" +id).append('<div id="picture_box_'+uniqueId+'_'+id+'" class="images_item form-gallery-item p-2  rounded-3 shadow border position-relative"  href="'+file+'"> <div class="w-100 h-100 d-flex"> <img src="'+file+'" class="w-100 h-100 object-fit-cover"> </div> <div onclick="$(`#multifile_images_'+id+'`).click()" class="images_overlay position-absolute start-0 bottom-0 top-0 end-0 h-100 rounded-3 d-flex align-items-center justify-content-center"> <i class="fa-solid fa-search fs-25 text-white"></i> <div onclick="event.stopPropagation();multifile_delete(event,\''+uniqueId+'_'+id+'\','+file_rand+',\''+file+'\',\''+file_seneded_type+'\',\''+form_id+'\',\''+token+'\')" class="item-delete ms-auto position-absolute top-0 end-0 text-red-600 bg-red-200 p-1 m-1"> <i class="fa-regular fa-trash-alt g-center"></i> </div> </div> </div>');
                const tifLinks = document.querySelectorAll('[href$=".tif"], [href$=".tiff"], [src$=".tif"], [src$=".tiff"]');
                await Promise.all(Array.from(tifLinks).map(async link => {
                    const tifUrl = link.href || link.src;
                    try {
                        const pngData = await loadTifAsPng(tifUrl);
                        if (link.href) link.href = pngData;
                        if (link.src) link.src = pngData;
                    } catch (error) {console.error(`Failed to process ${tifUrl}:`, error)}
                }));
                if (multiGallery)
                    multiGallery.destroy();
                multiGallery = lightGallery(document.getElementById("multifile_images_"+ id), {
                    plugins: [lgThumbnail, lgZoom, lgFullscreen, lgShare, lgRotate, lgAutoplay],
                    download: true,
                    controls: true,
                    thumbWidth: 100,
                    thumbHeight: 100,
                    showZoomInOutIcons: true,
                    actualSize: false
                });
            }
        else if(file_types.includes("audio"))
            {
                var file_seneded_type = "audio";
                $("#multifile_images_" +id).append('<div class="picture-box" id="picture_box_'+uniqueId+'_'+id+'" href="'+file+'"><a target="_blank" href="'+file+'"><figure><svg id="Layer_2" data2-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32.14 40" width=" 100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m8.28,0L0,8.28v28.15c0,1.97,1.6,3.57,3.57,3.57h25c1.97,0,3.57-1.6,3.57-3.57V3.57c0-1.97-1.6-3.57-3.57-3.57M7.84,2.44v3.76c.02.95-1.05,1.66-1.94,1.66h-3.46L7.84,2.44Zm22.88,33.99c0,1.18-.96,2.14-2.14,2.14H3.57c-1.18,0-2.14-.96-2.14-2.14h0V13.57h29.29v22.86Zm-14.14-18.97h0c-.06,0-.11,0-.17,0-.05,0-.1,0-.15,0-.32.1-.54.38-.56.71l-.22,2.96h0l-.46,6.01c-1.43-.05-5,.14-5.55,3.2-.21.95.21,1.92,1.04,2.42.56.34,1.21.51,1.86.5.9,0,1.77-.28,2.51-.79.92-.67,1.5-1.72,1.57-2.86,0-.04,0-.09,0-.13l.59-7.35c1.62.55,3.1,1.45,4.33,2.64.15.15.36.24.57.24.12,0,.23-.03.34-.07.3-.14.49-.45.48-.79-.03-3.49-2.7-6.38-6.17-6.7Zm-2.64,13.74c-.74.53-1.71.62-2.53.24-.26-.14-.39-.43-.33-.71.3-1.63,2.44-1.86,3.57-1.86h.14c.17.88-.16,1.78-.86,2.34Zm3.25-10.71l.07-1.19c1.52.37,2.78,1.43,3.42,2.86-1.06-.77-2.25-1.32-3.52-1.63l.03-.04Z"></path></g></svg></figure></a><button type="button" class="picture-box-remove" onclick="event.stopPropagation();multifile_delete(event,'+id+','+file_rand+','+file+', \''+file_seneded_type+'\')"><i class="fa-solid fa-trash-alt"></i></button></div>');
            }
        else if(file_types.includes("application"))
            {
                var file_seneded_type = "application";
                $("#multifile_images_" +id).append('<div class="picture-box" id="picture_box_'+uniqueId+'_'+id+'" href="'+file+'"><a target="_blank" href="'+file+'"><figure><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width="100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m37.13,138.18c-2.43.03-4.76-1-6.38-2.81-2.94-3.83-2.45-9.28,1.12-12.53,2.61-2.81,9.97-5.84,18.46-8.43,1.87-4.83,3.85-10.77,5.93-17.81-2.33-5.9-3.66-12.15-3.93-18.49-.39-7.59,3.65-11.91,7.84-12.28,3.32-.28,7.22,2.08,7.95,7.89h0c.29,2.67.04,5.38-.76,7.95l-1.07,3.68c-1.04,3.65-2.08,7.3-3.15,10.87,2.16,4.81,5.11,9.22,8.71,13.06,3.92-.76,7.89-1.22,11.88-1.38,8.18,0,11.24,3.71,12.47,5.9,1.46,2.66,1.31,5.91-.37,8.43-1.85,2.66-5.02,4.07-8.23,3.68-6.75-1.43-12.94-4.79-17.81-9.66-4.69.96-9.78,2.19-14.55,3.54-3.01,7.44-5.98,12.9-8.91,14.95-2.64,2.07-5.86,3.27-9.21,3.43Zm10.06-15.9c-3.81,1.03-7.41,2.75-10.59,5.09-1.4,1.52-1.6,3.15-.98,3.88s3.12.96,7-1.77c2.03-2.03,3.6-4.49,4.58-7.19Zm30.9-7.44c2.97,2.35,6.47,3.94,10.2,4.64.85.17,1.73-.14,2.28-.81.33-.54.33-1.23,0-1.77-.31-.59-1.69-2.44-6.8-2.47-1.89.05-3.78.22-5.65.51l-.03-.08Zm-17.64-9.83c-.84,2.56-1.66,5.03-2.47,7.39,2.22-.59,4.44-1.12,6.63-1.6-1.5-1.84-2.88-3.77-4.13-5.79h-.03Zm.25-32.62h0c-.65,0-2.11,1.74-1.94,5.62.12,2.47.41,4.93.87,7.36.14-.53.31-1.04.45-1.57l1.07-3.71c.54-1.72.73-3.54.56-5.34h0c-.22-1.8-.84-2.36-.98-2.36h-.03ZM112,0H32.45L0,32.45v110.35c0,7.73,6.27,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14ZM30.8,9.55v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.55L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4h0V53.2h114.8v89.6Z"></path></g></svg></figure></a><button type="button" class="picture-box-remove" onclick="event.stopPropagation();multifile_delete(event,'+id+','+file_rand+','+file+', \''+file_seneded_type+'\')"><i class="fa-solid fa-trash-alt"></i></button></div>');
            }
        else
            {
                var file_seneded_type = "other";
                $("#multifile_images_" +id).append('<div class="picture-box" id="picture_box_'+uniqueId+'_'+id+'" href="'+file+'"><a target="_blank" href="'+file+'"><figure><svg id="Layer_2" data-name="Layer 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 126 156.8" width="100%" height="40px"><g id="Layer_1-2" data-name="Layer 1"><path class="file-manager-bg-dark" d="m112,0H32.45L0,32.45v110.35c0,7.73,6.26,14,14,14h98c7.73,0,14-6.27,14-14V14c0-7.73-6.27-14-14-14Zm-19.15,22.92c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-16.52,0c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-16.52,0c1.92,0,3.48,1.56,3.48,3.48s-1.56,3.48-3.48,3.48-3.48-1.56-3.48-3.48,1.56-3.48,3.48-3.48Zm-29.01-13.37v14.73c0,3.72-4.2,6.52-7.7,6.52h-13.56L30.8,9.55Zm89.6,133.25c0,4.64-3.76,8.4-8.4,8.4H14c-4.64,0-8.4-3.76-8.4-8.4V53.2h114.8v89.6Zm-18.76-20.03c0,.91-.37,1.73-.96,2.32-.59.59-1.41.96-2.32.96s-1.73-.37-2.32-.96c-.59-.59-.96-1.41-.96-2.32s.37-1.72.96-2.31c.59-.6,1.41-.96,2.32-.96,1.81,0,3.28,1.46,3.28,3.27Zm12.45-32.1c0,2.05-.56,4.12-1.66,6.19-1.1,2.07-3.04,3.95-5.81,5.63-2.12,1.69-3.37,2.8-3.74,3.35-.37.54-.74,1.14-1.1,1.8-.36.65-.62,1.87-.8,3.63v.53c0,1.54-1.24,2.78-2.78,2.78-.77,0-1.47-.31-1.97-.81s-.82-1.2-.82-1.97v-.03c-.11-1.47,0-2.93.33-4.39.74-2.43,1.94-4.39,3.6-5.9,2.54-2.18,4.64-4.08,6.33-5.68,1.68-1.61,2.52-3.36,2.52-5.26,0-2.34-.96-4.27-2.87-5.79-1.91-1.51-4.12-2.27-6.63-2.27s-4.42.77-6.06,2.31c-1.27,1.19-2.28,2.86-3.02,5.02-.41,1.18-1.61,1.91-2.86,1.8h-.06c-1.74-.17-2.93-1.89-2.42-3.57.73-2.42,1.99-4.59,3.77-6.51,2.56-2.75,6.11-4.13,10.65-4.13s8.52,1.24,11.27,3.73,4.13,5.67,4.13,9.54Zm-31.48-10.46c0,1.78-1.44,3.22-3.22,3.22h-44.38c-1.78,0-3.22-1.44-3.22-3.22s1.44-3.22,3.22-3.22h44.38c1.78,0,3.22,1.44,3.22,3.22Zm-54.55,0c0,1.78-1.44,3.22-3.22,3.22h-7.98c-1.78,0-3.23-1.44-3.23-3.22s1.44-3.22,3.22-3.22h7.99c1.78,0,3.23,1.44,3.22,3.22Zm34.69,21.3c0,1.78-1.44,3.22-3.22,3.22H16.86c-1.78,0-3.22-1.45-3.22-3.23s1.44-3.22,3.22-3.22h42.67c1.78,0,3.23,1.45,3.22,3.23Zm26.52,21.29c0,1.78-1.44,3.22-3.22,3.22h-45.23c-1.78.01-3.23-1.44-3.23-3.22s1.44-3.22,3.22-3.22h45.23c1.78,0,3.23,1.44,3.23,3.22Zm-57,0c0,1.78-1.44,3.22-3.22,3.22h-12.19c-1.78,0-3.22-1.44-3.22-3.22s1.44-3.22,3.22-3.22h12.19c1.78,0,3.22,1.44,3.22,3.22Z"></path></g></svg></figure></a><button type="button" class="picture-box-remove" onclick="event.stopPropagation();multifile_delete(event,'+id+','+file_rand+','+file+', \''+file_seneded_type+'\')"><i class="fa-solid fa-trash-alt"></i></button></div>');
                // $("#multifile_images_" +id).append('<div class="position-relative" id="picture_box_'+uniqueId+'_'+id+'"><a class="picture-box  d-block"  href="'+file+'">'+file+'</a><button type="button" class="picture-box-remove" onclick="event.stopPropagation();multifile_delete(event,'+id+','+file_rand+','+file+' , \''+file_seneded_type+'\')"><i class="fa-solid fa-trash-alt"></i></button></div>');
            }
        var data1 = $("#element_"+id+"_hide").val();
        if(data1 == "")
            $("#element_"+id+"_hide").val(file);
        else
            $("#element_"+id+"_hide").val(data1+","+file);

        $("#element_"+id+"_hide").trigger("input");
        window["countUploadFile_"+id]++;
    }
}

function listfile(id,form_id,token,maxFileSize = null, elements_id = '', model = '')  {
    var $droparea = $("#element_"+id+"_drop_area");
    var fileInput = document.getElementById("element_"+id+"_file")
    var filePreview = document.getElementById("element_"+id+"_preview")
    var fileName = document.getElementById("element_"+id+"_filename")
    var $fileDelete = $("#element_"+id+"_file_delete")
    var $result = $("#single_file_result_"+id)

    var files = fileInput.files
    var filesCount = files.length;

    if (filesCount === 1)
        {

            var filePath = fileInput.value;
            var extensions = fileInput.getAttribute("accept");
            if(extensions != "")
                {
                    var extensionsArray = extensions.split(",");
                    var file_extension = filePath.split(".");

                    if (!extensionsArray.includes("." + file_extension[file_extension.length - 1]?.toLowerCase()))
                        {
                            snackbar("element_6598465132", "پسوند فایل مجاز نمی باشد", type = "danger", duration = 3000)
                            fileInput.value = "";
                            return false;
                        }
                }
                var fileSizeInMB = $("#element_"+id+"_file")[0].files[0].size / 1024 / 1000;
                if (maxFileSize && maxFileSize < fileSizeInMB) {
                    snackbar("element_6598654465132", `حجم فایل ارسالی باید زیر ${maxFileSize} مگابایت باشد.`, type = "danger");
                    return;
                };
                showLoader(id);
                $droparea.hide();
                var formData = new FormData();
                formData.append("file", $("#element_"+id+"_file")[0].files[0]);
                formData.append("token", token);
                formData.append("form_id", form_id);
                formData.append("form_element_id", id);
                if (elements_id?.length) formData.append("elements",$(`#${elements_id}`).val());
                $.ajax({
                    url  : PATHFILE+"execute/form/add/upload_listfile",
                    type : "POST",
                    data : formData,
                    processData: false,
                    contentType: false,
                    success : async function(data) {
                        hideLoader(id);
                        var image_data = JSON.parse(data);
                        if(image_data.message !== "")
                            {
                                snackbar("element_659823465132", image_data.message || "فایل ارسالی غیر مجاز میباشد", type = "danger", duration = 3000)
                                $droparea.show();
                            }
                        else
                            {
                                $("#element_"+id+"_hide").val(image_data.name);
                                $("#element_"+id+"_hide").trigger("input");
                                // filePreview.setAttribute("src", image_data.url)
                                if (fileName) fileName.innerText = image_data.name
                                $result.show();
                                $(document).ready(async function() {
                                    var file_types = image_data.type.split("/");
                                    if(file_types.includes("video"))
                                        {
                                            if (window["lightGallery_listfile_"+id]) window["lightGallery_listfile_"+id].destroy();
                                            var data_video = '{"source":[{"src":"'+image_data.link+'","type":"video/mp4"}],"attributes":{"preload":true,"controls":true,"playsinline":true}}';
                                            $(`#gallery_${id}`).append('<a class="" data-lg-size="1280-720" data-video='+data_video+' data-poster="'+PATHFILE+'assets/images/icons/form-video.webp" data-sub-html="'+image_data.name+'">'+image_data.url+'</div></a>');
                                            listFileGallery = lightGallery(document.getElementById(`gallery_${id}`), {
                                                speed: 500,
                                                plugins: [lgVideo]
                                            });
                                            window["lightGallery_listfile_"+id] = listFileGallery;
                                            $(`#gallery_${id}`).on("click", () => window["lightGallery_listfile_"+id].openGallery(0))
                                            $fileDelete.on("click", () => window["lightGallery_listfile_"+id].closeGallery())
                                        }       
                                    else if(file_types.includes("image"))
                                        {
                                            if (window["lightGallery_listfile_"+id]) window["lightGallery_listfile_"+id].destroy();
                                            $(`#gallery_${id}`).append('<img src="'+image_data.url+'" class="w-100 '+(model == 'vertical' ? 'h-100' : '')+' object-fit-cover" id="element_'+id+'_preview" alt="">');
                                            const tifLinks = document.querySelectorAll('[href$=".tif"], [href$=".tiff"], [src$=".tif"], [src$=".tiff"]');
                                            await Promise.all(Array.from(tifLinks).map(async link => {
                                                const tifUrl = link.href || link.src;
                                                try {
                                                    const pngData = await loadTifAsPng(tifUrl);
                                                    if (link.href) link.href = pngData;
                                                    if (link.src) link.src = pngData;
                                                } catch (error) {console.error(`Failed to process ${tifUrl}:`, error)}
                                            }));
                                            listFileGallery = lightGallery(document.getElementById(`gallery_${id}`), {
                                                plugins: [lgThumbnail, lgZoom, lgFullscreen, lgShare, lgRotate, lgAutoplay],
                                                download: true,
                                                controls: true,
                                                thumbWidth: 100,
                                                thumbHeight: 100,
                                                showZoomInOutIcons: true,
                                                actualSize: false
                                            });
                                            window["lightGallery_listfile_"+id] = listFileGallery;
                                            $(`#gallery_${id}`).on("click", () => window["lightGallery_listfile_"+id].openGallery(0))
                                            $fileDelete.on("click", () => window["lightGallery_listfile_"+id].closeGallery())
                                        }
                                    else
                                        {
                                            $(`#gallery_${id}`).append('<a target="_blank" href="'+image_data.link+'">'+image_data.url+'</a>')
                                        }    
                                    
                                })
                            }    
                        
                    }
                });
                
                 
        }       
    $fileDelete.on("click", function () {
        $("#element_"+id+"_file").val(null);
        $("#element_"+id+"_hide").val("");
        $("#element_"+id+"_hide").trigger("input");
        $("#gallery_"+id).empty();
        $result.hide();
        $droparea.show();
    });                                    
}

function show_password(id) {
    var password_type = $("#"+id).attr("type");
    if (password_type == "password") {
        $("#"+id).attr("type", "text");

        $(".show_password_icon_"+id.replace("element_" , "")).addClass("show_icon");
    } else {
        $("#"+id).attr("type", "password");
        $(".show_password_icon_"+id.replace("element_" , "")).removeClass("show_icon");
    }
}

function file_delete(id,div_id,file_name,form_id,token){
    $("."+div_id).remove();
    $("#single_file_result_"+id).hide();
    $("#element_"+id+"_file").val("");
    $("#single_file_"+id).show();
    var str = $("#element_"+id+"_hide").val();
    var res = str.endsWith(',') ? str.replace(file_name+",", "").replace(/,+$/, "") : str.replace(file_name, "").replace(/,+$/, "");
    $("#element_"+id+"_hide").val(res+",");
    $("#element_"+id+"_hide").trigger("input");
    $.ajax({
        url:"'._path_file.'execute/form/add/delete_multifile",
        data:"id="+id+"&file_name="+file_name+"&token="+tokne+"&form_id="+form_id,cache:"false",type:"Post",
        success:function(html){$("#as").html(html);}
    });
}

function listfile_delete(id,file_name , form_id,token) {
    $("#listfile"+id+"_div_view").val("");
    $("#listfile"+id+"_div_btn").removeClass("d-none");
    $("#listfile"+id+"_div_btn").addClass("d-show");
    $("#listfile"+id+"_div_btn").addClass("d-flex");
    $("#listfile"+id+"_div_view").removeClass("d-show");
    $("#listfile"+id+"_div_view").addClass("d-none");
    $("#element_"+id+"_hide").val("");
    $("#element_"+id+"_hide").trigger("input");
    $("#"+id+"_hide").val("");
    $.ajax({
        url:"'._path_file.'execute/form/add/delete_listfile",
        data:"id="+id+"&file_name="+file_name+"&token="+token+"&form_id="+form_id,cache:"false",type:"Post",
        success:function(html){$("#as").html(html);}
    });
}

function listfile_delete_edit(id,file_name) {
    $(".listfile"+id+"_img").attr("src",PATHFILE+"upload/icons/btn/btn_green_l_select_file.png");
    $("#listfile"+id+"_div_btn").show();
    $("#listfile"+id+"_div_view").find("*").remove();
    $("#listfile"+id+"_div_view").hide();
    $("#listfile"+id+"_div_view").val("");
    $("#element_"+id+"_hide").val("");
    $("#element_"+id+"_hide").trigger("input");
    $("#"+id+"_hide").val("");
}

function submit_type(step,onclick,type,form_id,button_element_id = '',onclick_override = '') {
    $("#form_add_"+form_id+"_submitform").find(`[name="submit_element_id"]`).val(button_element_id);
    $("#form_add_"+form_id+"_submitform").find(`[name="submit_element_type"]`).val(onclick);
    if (onclick_override.length > 0) $("#form_add_"+form_id+"_submitform").find(`[name="submit_element_type"]`).val(onclick_override);
    if (type == "exit")
        {
            if (onclick != "") window.location = onclick;
            else window.location = PATHFILE;
        }
    else if (type == 'submit_captcha')
        {
            var status = true;
            $("#form_add_result").html("");
            var s1 = $(".steps_"+form_id).val();
            $(".steps_"+form_id).val(s1+","+step+",");
            status = this["required_"+form_id+"_"+step]();
            if  (status == true) $("#captcha_modal").modal("show");
            $("#captcha_submit_btn").on("click", () => {
                if (status) {
                    clearInterval(window?.countDownTimerInterval);
                    if ($("#form_timer").length) $("#form_timer").text("- - : - - : - -");
                    $("#onclick_"+form_id).val(onclick);
                    $("#type_"+form_id).val(type);
                    $("#form_add_"+form_id+"_submitform").submit();
                    $(`.step_${form_id}[data-disabled-step=t]`).find(".form_button_elements").attr("style", "");
                }
            })
        }
    else
        {
            var status = true;
            $("#form_add_result").html("");
            var s1 = $(".steps_"+form_id).val();
            $(".steps_"+form_id).val(s1+","+step+",");
            status = this["required_"+form_id+"_"+step]();
            if  (status == true)
                {
                    clearInterval(window?.countDownTimerInterval);
                    if ($("#form_timer").length) $("#form_timer").text("- - : - - : - -");
                    $("#onclick_"+form_id).val(onclick);
                    $("#type_"+form_id).val(type);
                    $("#form_add_"+form_id+"_submitform").submit();
                    $(`.step_${form_id}[data-disabled-step=t]`).find(".form_button_elements").attr("style", "");
                }
        }
}

function preview_form(form_id,page,set,required) {
    step(form_id, page, set, required,true);
}

function view_step(form_id,set) {
    step(form_id, set, set);
    $("[data-type]").parent(":not(.form_button_elements_preview)").css({
        "opacity": "",
        "pointer-events": "",
        "user-select": "",
        "-webkit-user-select": "",
        "-moz-user-select": "",
        "-ms-user-select": "",
        "cursor": "",
    });
    if ($("[data-type]").parents(".file-drop-area").length) $("[data-type]").parents(".file-drop-area").parent().css({
        "opacity": "",
        "pointer-events": "",
        "user-select": "",
        "-webkit-user-select": "",
        "-moz-user-select": "",
        "-ms-user-select": "",
        "cursor": "",
    })
    $(`.step_${form_id}[data-disabled-step=f]`).find(".form_button_elements").css({"display": ""});
    $(`.step_${form_id}[data-disabled-step=f]`).find(".form_button_elements_preview").attr('style', 'display: none !important');
}

function view(path) {
    window.open(path, "", "width=500,height=500,resizable=yes,scrollbars=yes");
}

function location_show(id,token) {
    $.ajax({
        url: PATHFILE+"execute/form/add/location",
        data:"id="+id+"&token="+token,cache:"false",type:"Post",
        success:function(html){$("#content_set_"+id).html(html);initialize();}
    });
}

function related_show(form_id,form_element_id) {
    option_id = $("#element_"+form_element_id+"_1").val();
    $.ajax({
        url: PATHFILE+"execute/form/add/related",
        data:"form_id="+form_id+"&form_element_id="+form_element_id+"&option_id="+option_id+"&token="+token,cache:"false",type:"Post",
        success:function(html){
            if (html != "")
                {
                    $("#element_"+form_element_id+"_2").html(html);
                    $(".div_"+form_element_id).show();
                }
            else
                {
                    $(".div_"+form_element_id).hide();
                }
        }
    });
}

function back(form_id,page) {
    set = $("#step_back_"+page).val();
    step(form_id,set,set,"f");
}

function show_snackbar() {
    var x = document.querySelector(".snackbar");
    x.className = "show";
    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 3000);
}

function multifile_modal_image(e,form_element_id) {
    $(".multi_image_"+form_element_id).attr("src", e.getAttribute("src"));
}

/* Widgets Code Start */
var BCDataBackPage = "0";
var BCBreadcrumb = [
    {
        text: "خدمات من",
        id: "0",
    },
]
function initWidgets() {
    let parentIds = BCDataBackPage.split(",")
    $(document).ready(function() {
        const backPageWidget = $(".widget_item.category_back")
        $(".widget_item[data-id]").each(function () {
            if (!$(this).hasClass("c_0")) $(this).hide(0)
            else $(this).show(0)
        })
        BCDataBackPage = "0"
        backPageWidget.hide(0)
    
        // When any widget clicked
        $(".widget_item[data-id]").on("click", function (event) {
            let widgetId = $(this).attr("data-id")
            // Check if clicked widget has any children?
            let hasChildren = false
            $(`.widget_item[data-id]`).each(function () {
                if ($(this).hasClass(`c_${widgetId}`) && $(this).attr("data-id") !== widgetId) {
                    hasChildren = true
                }
            })
            if (!hasChildren) return
            $(`.widget_item[data-id]`).each(function () {
                if ($(this).hasClass(`c_${widgetId}`) && $(this).attr("data-id") !== widgetId) {
                    $(this).show(400)
                    const backPageValue = BCDataBackPage.split(",")
                    if (!backPageValue.includes(widgetId)) {
                        BCDataBackPage = backPageValue + "," + widgetId
                        backPageWidget.show(400)
                    }
                } else {
                    $(this).hide(0)
                }
            })
        })
        /* Widgets Code End */
    
        /* BreadCrumb Code Start */
    
        $(".widget_item[data-id]").click(function (event) {
            const widgetId = $(this).attr("data-id")
    
            // Check if clicked widget has any children?
            let hasChildren = false
            $(`.widget_item[data-id]`).each(function () {
                if ($(this).hasClass(`c_${widgetId}`) && $(this).attr("data-id") !== widgetId) {
                    hasChildren = true
                }
            })
            if (!hasChildren) return
            const text = $(this).attr("data-title")
            if (!BCBreadcrumb.find((b) => b.text === text)) {
                BCBreadcrumb.push({
                    text,
                    id: $(this).attr("data-id"),
                })
            }
    
            generateBreadcrumb()
        })

        $(".breadcrumb").on("click", "a", function (e) {
            e.preventDefault()
            const text = $(this).text()
            const index = BCBreadcrumb.findIndex((b) => b.text === text)
            const id = BCBreadcrumb[index].id
            if (id) {
                BCBreadcrumb.splice(index + 1, BCBreadcrumb.length)
                BCDataBackPage = BCBreadcrumb.map((b) => b.id).join(",")
                if (BCDataBackPage === "0") backPageWidget.hide()
                $(`.widget_item[data-id]`).each(function () {
                    if ($(this).hasClass(`c_${id}`) && $(this).attr("data-id") !== id) {
                        $(this).show(400)
                    } else {
                        $(this).hide()
                    }
                })
            }
            generateBreadcrumb()
        })
    })
    generateBreadcrumb()

    function generateBreadcrumb() {
        let html = ""
        BCBreadcrumb.map((item, index) => {
            html += `<li><a href="#">${item.text}</a></li>`
        })
        $(".breadcrumb ul").html(html)
    }

    /* BreadCrumb Code End */
    return {generateBreadcrumb, parentIds}
}

function searchWidgets(searchId) {
    $("#"+searchId).on("input", function () {
        // Retrieve the input field text and reset the count to zero
        var filter = $(this).val().trim()
        if (filter.length > 0) {
            $(".widget_item[data-id]").stop().hide(200)
            $(".widget_item[data-title*='"+filter+"']").stop().show(200)
            // Loop through the comment list
            // $(".widget_item[data-id]").each(function () {
            //     // If the list item does not contain the text phrase fade it out
            //     if ($(this).attr("data-title")?.search(new RegExp(filter, "i")) < 0) {
            //         $(this).hide(400)
            //         // Show the list item if the phrase matches and increase the count by 1
            //     } else {
            //         $(this).show(400)
            //         count++
            //     }
            // })
        } else {
            const lastParentId = BCDataBackPage.split(",").slice(-1)[0]
            $(".widget_item[data-id]").stop().hide(200)
            $(`.widget_item.c_${lastParentId}[data-id]`).stop().show(200)
            // $(`.widget_item[data-id]`).each(function () {
            //     if ($(this).hasClass(`c_${lastParentId}`)) {
            //         $(this).show(400)
            //     } else {
            //         $(this).hide(400)
            //     }
            // })
        }
    })
}

function searchWidgets(searchId) {
    const $searchInput = $("#" + searchId);
    const $widgetItems = $(".widget_item[data-id]");

    $searchInput.on("input", function () {
        const filter = $(this).val().trim().toLowerCase(); // Normalize filter text
        const lastParentId = BCDataBackPage.split(",").slice(-1)[0];

        if (filter.length > 0) {
            // Escape special characters in the filter
            const escapedFilter = filter.replace(/[!"#$%&'()*+,.\/:;<=>?@[\\\]^`{|}~]/g, "\\$&");

            // Loop through all widgets and update visibility based on the filter
            $widgetItems.each(function () {
                const $widget = $(this);
                const matchesFilter = $widget.attr("data-title").toLowerCase().includes(filter);

                if (matchesFilter && $widget.is(":hidden")) {
                    $widget.stop(true, true).show(200); // Show if it matches and is hidden
                } else if (!matchesFilter && $widget.is(":visible")) {
                    $widget.stop(true, true).hide(200); // Hide if it doesn't match and is visible
                }
            });
        } else {
            // If no filter, show items belonging to the last parent and hide others
            $widgetItems.each(function () {
                const $widget = $(this);
                const belongsToLastParent = $widget.hasClass(`c_${lastParentId}`);

                if (belongsToLastParent && $widget.is(":hidden")) {
                    $widget.stop(true, true).show(200); // Show if it belongs to the last parent and is hidden
                } else if (!belongsToLastParent && $widget.is(":visible")) {
                    $widget.stop(true, true).hide(200); // Hide if it doesn't belong to the last parent and is visible
                }
            });
        }
    });
}

function searchWidgets(searchId) {
    const $searchInput = $("#" + searchId);
    const widgetItems = Array.from(document.querySelectorAll(".widget_item[data-id]")).map((widget) => ({
        id: widget.getAttribute("data-id"),
        dataTitle: widget.getAttribute("data-title"),
        dataSearch: widget.getAttribute("data-search"),
        classes: Array.from(widget.classList),
    }));

    const worker = new Worker("/assets/workers/filterWidgetsWorker.js");

    worker.onmessage = function (event) {
        const { visibleIds, hiddenIds } = event.data;

        // Hide widgets that should be hidden
        hiddenIds.forEach((id) => {
            const $widget = $(`.widget_item[data-id="${id}"]`);
            if ($widget.is(":visible")) {
                $widget.stop(true, true).hide(200);
            }
        });

        // Show widgets that should be visible
        visibleIds.forEach((id) => {
            const $widget = $(`.widget_item[data-id="${id}"]`);
            if ($widget.is(":hidden")) {
                $widget.stop(true, true).show(200);
            }
        });
    };

    $searchInput.on("input", debounce(function () {
        const filter = $(this).val().trim().toLowerCase();
        const lastParentId = BCDataBackPage.split(",").slice(-1)[0];

        worker.postMessage({ filter, widgetItems, lastParentId });
    }, 200));
}

function searchInTable(inputId, tableId, searchAttribute) {
    const $input = $(`#${inputId}`);
    const $table = $(`#${tableId}`);
    const $rows = $table.find(`tr[${searchAttribute}]`);
    const $noResultsRow = $table.find('.no-results-row');

    if ($noResultsRow.length === 0) {
        $table.find("tbody").append(`
      <tr class="no-results-row" style="display: none;">
        <td colspan="100%" class="text-center py-3">هیچ نتیجه ای یافت نشد.</td>
      </tr>
    `);
    }

    const handleSearch = debounce(function() {
        const searchTerm = $input.val().toLowerCase().trim();
        let hasVisibleRows = false;

        $table.find('.no-results-row').hide();

        const rows = $rows.get();

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const searchText = $(row).attr(searchAttribute).toLowerCase();
            const isVisible = searchText.includes(searchTerm);

            row.style.display = isVisible ? '' : 'none';
            if (isVisible) hasVisibleRows = true;
        }

        if (!hasVisibleRows && searchTerm !== '') {
            $table.find('.no-results-row').show();
        }
    }, 200);

    $input.on('input', handleSearch);
    $input.on('keydown', function(e) {
        if (e.key === 'Escape') {
            $input.val('').trigger('input');
        }
    });
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function searchDivs(searchId, parentId, attribute) {
    $("#"+searchId).on("input", function () {
        var filter = $(this).val().trim()
        if (filter.length > 0) {
            $(`#${parentId} [${attribute}]`).stop().hide(400).addClass("d-none")
            $(`#${parentId} [${attribute}*='`+filter+`']`).stop().show(400).removeClass("d-none")
        } else {
            $(`#${parentId} [${attribute}]`).stop().show(400).removeClass("d-none")
        }
    })
}

function makeDropdownFrom(wrapperSelector, targetTogglerSelector, align = false, onSelect = () => {}) {
    $(`${wrapperSelector}`).find(`${targetTogglerSelector}`).html($(`${wrapperSelector}`).find(`${wrapperSelector}-dropdown-item.active`).html())
    $(`${wrapperSelector}`).on("click", `${targetTogglerSelector}`, function() {
        $(this).parent(`${wrapperSelector}`).toggleClass("show")
    })

    $(`${wrapperSelector}`).find(`${wrapperSelector}-dropdown-item`).each(function() {
        $(this).click(function() {
            onSelect(this)
            $(this).addClass("active").siblings().removeClass("active")
            $(`${wrapperSelector}`).find(`${targetTogglerSelector}`).html($(`${wrapperSelector}`).find(`${wrapperSelector}-dropdown-item.active`).html())
        })
    })
    
    if (align) {
        $(document).ready(function () {
            dropDownAlign(`${wrapperSelector} ${wrapperSelector}-dropdown`);
            $(window).on("scroll", function () {
                dropDownAlign(`${wrapperSelector} ${wrapperSelector}-dropdown`);
            });
            $(".media-sidebar").on("scroll", function () {
                dropDownAlign(`${wrapperSelector} ${wrapperSelector}-dropdown`);
            });
        });    
    }

    $(document).on("click", function (event) {
        // If the target is not the container or a child of the container, then process
        // the click event for outside of the container.
        if ($(event.target).closest(`${wrapperSelector}`).length === 0) {
            $(`${wrapperSelector}`).removeClass("show")
        }
    });
}

function dropDownAlign(selector) {
    var parentScrollTop = $(window).scrollTop();
    var dropdownElements = document.querySelectorAll(selector);
    dropdownElements.forEach((dropdownElement, index) => {
        var dropdownRect = dropdownElement.getBoundingClientRect();
        var dropdownTop = dropdownRect.top + parentScrollTop;
        var dropdownBottom = dropdownRect.bottom + parentScrollTop;
        var parentHeight = $(window).outerHeight(true) + parentScrollTop;
        var dropdownHeight = dropdownBottom - dropdownTop;
        if (dropdownBottom >= parentHeight - (dropdownHeight/2)) {
            if (!$(selector).hasClass("dropup")) {
                $(selector).addClass("dropup");
            }
        } else {
            if ($(selector).hasClass("dropup")) {
                $(selector).removeClass("dropup");
            }
        }
    })
}

function print_form(form_id)
    {
        var id_hash = $("#id_hash").val();
        window.location = PATHFILE + 'form/print/'+form_id+'/'+id_hash        
    }

async function register(title,title_key,link)
    {
        let search = new URLSearchParams(window.location.search)
        let type = search.get("login_platform") ?? 'my';
        switch(type) {
            case 'my':
                // snackbar("element_1894324", title, "info", {isConfirmed: true,hasIcon: true,duration: 15000,textStyles: {fontWeight: "bold"},acceptText: title_key,cancelText: "انصراف"}).then(function (result) {
                //     if (result.isConfirmed)
                //         {
                //             link_transfer(link,"direct");
                //         }
                // });
                snackbar("ita_auth_modal", `
                    <div style="text-align: right; line-height: 1.8;">
                        <h3 class="mb-2 text-first-darker">🔐 احراز هویت در میز خدمت الکترونیکی</h3>
                        <p class="mb-1">${title}</p>
                    </div>
                `, "info", {
                    isConfirmed: true,
                    hasIcon: true,
                    duration: 15000,
                    textStyles: {fontWeight: "bold", textAlign: "right", fontSize: "14px"},
                    acceptText: title_key,
                    cancelText: "انصراف",
                    customHTML: true,
                    buttonStyles: {
                        accept: {borderRadius: "6px", fontSize: "14px", fontWeight: "bold"},
                        cancel: {padding: "12px 25px", borderRadius: "6px", fontSize: "14px"}
                    }
                }).then(function (result) {
                    if (result.isConfirmed)
                        {
                            link_transfer(link,"direct");
                        }
                });
                break;
            case 'eitaa':
                const auth = new EitaaAuth();
                auth.loginLink = link;
                window.appAuth = auth;
                break;
            default:
                snackbar("ita_auth_modal", `
                    <div style="text-align: right; line-height: 1.8;">
                        <h3 class="mb-2 text-first-darker">🔐 احراز هویت در میز خدمت الکترونیکی</h3>
                        <p class="mb-1">${title}</p>
                    </div>
                `, "info", {
                    isConfirmed: true,
                    hasIcon: true,
                    duration: 15000,
                    textStyles: {fontWeight: "bold", textAlign: "right", fontSize: "14px"},
                    acceptText: title_key,
                    cancelText: "انصراف",
                    customHTML: true,
                    buttonStyles: {
                        accept: {borderRadius: "6px", fontSize: "14px", fontWeight: "bold"},
                        cancel: {padding: "12px 25px", borderRadius: "6px", fontSize: "14px"}
                    }
                }).then(function (result) {
                    if (result.isConfirmed)
                        {
                            link_transfer(link,"direct");
                        }
                });
        }
    }
function initVerifyInputs(inputs, form = null) {
    $(document).ready(() => {
        if (inputs.length > 0) {
            inputs[inputs.length - 1].focus();
        }
    })

    inputs.forEach((input, index) => {
        input.addEventListener('input', (e) => {
            input.value = input.value.replace(/[^0-9]/g, '');
            if (input.value.length > 0 && index > 0) {
                inputs[index - 1].focus();
            }
            if (form && Array.from(inputs).filter(i => i.value.length).length == inputs.length) form.submit();
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace') {
                if (!input.value && index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
            }
        });

        input.addEventListener('focus', () => {
            setTimeout(() => {
                input.setSelectionRange(input.value.length, input.value.length);
            }, 0);
        });
    });

    $(document).on("paste", (e) => {
        const pastedValue = e.originalEvent.clipboardData.getData("text");
        if (parseInt(pastedValue)) {
            inputs.forEach((input, i) => {
                if (pastedValue?.[(pastedValue.length - 1) - i]) {
                    input.value = pastedValue?.[(pastedValue.length - 1) - i]
                    input.dispatchEvent(new Event("keydown", { bubbles: true, cancelable: true }));
                    input.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
                }
            })
        }
    })
}

function setPaneToParser(parser, map) {
    let bounds = L.latLngBounds();

    // Add each feature's coordinates to the bounds
    parser.features.forEach(feature => {
        // Assuming Polygon; you may need to adjust if using other geometry types
        function processLatLng(latLng, callback = () => {}) {
            if (Array.isArray(latLng) && Array.isArray(latLng[0])) {
                latLng.forEach(latLngs => processLatLng(latLngs, callback));
            } else {
                callback(latLng)
            }
        }
        processLatLng(feature.geometry.coordinates, (latlng) => {
            if (latlng?.length)
                bounds.extend(L.latLng(latlng[1], latlng[0]));
        })
    });
    if (!Object.keys(bounds).length) return;
    // Pan to the center of the bounds
    map.fitBounds(bounds);
}

var seatGeoJsons = {}
let initializedSeatMaps = [];
var seatMap;
let seatGeoJsonLayer;
var timeoutPopup;
var layersPopup = {};
var areaSelectionPopup;
var areaParsers = {};
let lastClickedOnSeats;
var lastClickedSeatId = null;
function initSeatMap(id, isInitMap, lat, lng, zoom, type = 'seat', token = "", ticket_node_id = "", ticket_node_sans_id = "", defaultItem = {
    position_target: null,
    seat_id: null
}, seat_type = '', title = '' , users_id = '' , charts_id = '' , groups_id = ''){
    var cs = getComputedStyle(document.querySelector("body"));
    if (isInitMap) {
        if (type == 'seat' && defaultItem.position_target) {
            function setPlaces() {
                const backBtn = $("#back-btn")
                gId = id;
                backBtn.show()
                $("#position").hide()
                $(`[data-position-target=${defaultItem.position_target}]`).show()
            }
            setPlaces()
        }
        if (!initializedSeatMaps.includes(`seat_map_set_${id}`)) {
            initializedSeatMaps.push(`seat_map_set_${id}`);
            seatMap = L.map(id ? `seat_map_set_${id}` : "seat_map_set", {
                measureControl: true,
                zoomControl: false,
                zoomsliderControl: false,
                attributionControl: false,
            }).setView([lat, lng], zoom);
        }
        for (var key in window["app_config"]["_map_types"]) {
            const options = window["app_config"]["_map_types"][key]["option"]
            window[window["app_config"]["_map_types"][key]["var_name"]] = L.tileLayer(window["app_config"]["_map_types"][key]["url"], options);
        }
        primaryTile.addTo(seatMap).bringToBack();
        $("#change-layer").change(function () {
            if ($("#change-layer").is(":checked")) {
                seatMap.removeLayer(primaryTile);
                sateliteTile.addTo(seatMap);
                $("#change-layer-box > img").attr("src", PATHFILE + "/assets/images/map/osm-layer.png");
                if (getCookie("theme_mode")?.length) {
                    if (getCookie("theme_mode") === themeCustomDarkClass) {
                        $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
                    } else {
                        $(".leaflet-map-pane").css("filter", "none");
                    }
                }
            } else {
                if (getCookie("theme_mode")?.length) {
                    if (getCookie("theme_mode") === themeCustomDarkClass) {
                        $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
                    } else {
                        $(".leaflet-map-pane").css("filter", "none");
                    }
                    seatMap.removeLayer(sateliteTile);
                    primaryTile.addTo(seatMap);
                }
                $("#change-layer-box > img").attr("src", PATHFILE + "/assets/images/map/google-layer.png");
            }
        });
        
        if (getCookie("theme_mode") === themeCustomDarkClass) {
            $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
        } else {
            $(".leaflet-map-pane").css("filter", "none");
        }

        $(document).on("themeChanged", function (e, { themeName }) {
            if (themeName === themeCustomDarkClass) {
                $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
            } else {
                $(".leaflet-map-pane").css("filter", "none");
            }
        });
    }

    if (type == 'seat') {
        /* Adding the default selected items start */
        L.geoJSON(seatJsons[id]).eachLayer(function (layer) {
            if(layer.feature.properties?.con?.length && !eval(layer.feature.properties.con)) {
                layer.feature.properties.status = "space";
            }
            if (layer.feature.properties.TxtMemo && layer.feature.properties.status === "selected") {
                $(document).trigger("seatAdded", {
                    row: layer.feature.properties.row,
                    column: layer.feature.properties.column,
                    price: layer.feature.properties.price,
                    element: layer.feature
                })
            }
        })
        /* Adding the default selected items end */
    
        function setParsers() {
            var timeoutPopup;
            seatGeoJsons["location_" + id] = L.vectorGrid
                .slicer(seatJsons[id], {
                    maxZoom: 22,
                    minNativeZoom: 0,
                    rendererFactory: L.canvas.tile,
                    vectorTileLayerStyles: {
                        sliced: function (properties, zoom) {
                            if (properties.TxtMemo != null && properties.status === "empty") {
                                return {
                                    color: `rgb(${cs.getPropertyValue("--rgb-green-500")})`,
                                    fillColor: `rgb(${cs.getPropertyValue("--rgb-green-500")})`,
                                    weight: 3,
                                    opacity: 1,
                                    fillOpacity: 0.7,
                                    fill: true,
                                };
                            } else if (properties.TxtMemo != null && properties.status === "reserved") {
                                return {
                                    color: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                    fillColor: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                    weight: 3,
                                    opacity: 1,
                                    fillOpacity: 0.7,
                                    fill: true,
                                };
                            } else if (properties.TxtMemo != null && properties.status === "space") {
                                return {
                                    color: `rgb(${cs.getPropertyValue("--rgb-slate-400")})`,
                                    fillColor: `rgb(${cs.getPropertyValue("--rgb-slate-400")})`,
                                    weight: 3,
                                    opacity: 1,
                                    fillOpacity: 0.7,
                                    fill: true,
                                };
                            } else if (properties.TxtMemo != null && properties.status === "selected") {
                                return {
                                    color: `rgb(${cs.getPropertyValue("--rgb-blue-500")})`,
                                    fillColor: `rgb(${cs.getPropertyValue("--rgb-blue-500")})`,
                                    weight: 3,
                                    opacity: 1,
                                    fillOpacity: 0.7,
                                    fill: true,
                                };
                            } else if (properties.TxtMemo != null && properties.status === "selled") {
                                return {
                                    color: `rgb(${cs.getPropertyValue("--rgb-red-500")})`,
                                    fillColor: `rgb(${cs.getPropertyValue("--rgb-red-500")})`,
                                    weight: 3,
                                    opacity: 1,
                                    fillOpacity: 0.7,
                                    fill: true,
                                };
                            } else if (properties.TxtMemo != null && properties.status === "locked") {
                                return {
                                    color: `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`,
                                    fillColor: `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`,
                                    weight: 3,
                                    opacity: 1,
                                    fillOpacity: 0.7,
                                    fill: true,
                                };
                            } else {
                                return {
                                    color: false,
                                    fillColor: false,
                                    opacity: 0,
                                    fillOpacity: 0,
                                    weight: 0,
                                    stroke: false,
                                    fill: false,
                                };
                            }
                        },
                    },
                    interactive: true,
                    preferCanvas: false,
                    getFeatureId: function (feature) {
                        if (feature.properties.TxtMemo) {
                            return feature.properties.TxtMemo.toString();
                        } else return feature.properties.Shape_Area.toString() + feature.properties.Shape_Leng.toString();
                    },
                })
                .on("mouseover", function (e) {
                    if (timeoutPopup) clearTimeout(timeoutPopup)
                    var layer = e.layer;
                    var latlng = e.latlng;
                    if (layer.properties.TxtMemo !== null) {
                        var TxtMemo = layer.properties.TxtMemo
                        if (!layersPopup[layer.properties.TxtMemo.toString()]) {
                            layersPopup[layer.properties.TxtMemo.toString()] = L.popup({ offset: [0, 5] })
                                .setContent("جایگاه "+ TxtMemo)
                                .setLatLng(latlng)
                                .openOn(seatMap)
                        } else {
                            layersPopup[layer.properties.TxtMemo.toString()]
                                .setLatLng(latlng)
                                .openOn(seatMap)
                        }
                    }
                })
                .on("mouseout", function (e) {
                    timeoutPopup = setTimeout(() => {
                        seatMap.closePopup();
                        if (timeoutPopup) clearTimeout(timeoutPopup)
                    }, 100)
                })
                .on("click", async function (e) {
                    if (Date.now() - lastClickedOnSeats < 50) {
                        lastClickedOnSeats = Date.now()
                        return;
                    } else {
                        lastClickedOnSeats = Date.now()
                    }
                    var layer = e.layer;
                    var properties = e.layer.properties;
                    if (properties.TxtMemo != null) {
                        lastClickedSeatId = properties.TxtMemo.toString();
                        if (properties.TxtMemo != null) {
                            var status;
                            if([`rgb(${cs.getPropertyValue("--rgb-green-500")})`, `rgb(${cs.getPropertyValue("--rgb-amber-500")})`].includes(layer.options.color)) {
                                status = "new";
                            } else if(layer.options.color === `rgb(${cs.getPropertyValue("--rgb-blue-500")})`) {
                                status = "remove";
                            } else if([`rgb(${cs.getPropertyValue("--rgb-slate-400")})`, `rgb(${cs.getPropertyValue("--rgb-red-500")})`, `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`].includes(layer.options.color)) {
                                return;
                            }
                            var pattern_sub_id = id
                            if(seat_type == 'position') pattern_sub_id = '1';
                            var data_ditails = await setSelected(status,properties.price,lastClickedSeatId,pattern_sub_id, title);
                            var result  = JSON.parse(data_ditails);
                            if(result.status == "selected" && layer.options.color != `rgb(${cs.getPropertyValue("--rgb-blue-500")})`)
                                {
                                    total_price += result.price;
                                    var ticket_string_price = total_price.toString();
                                    var result_price = commafy(ticket_string_price);
                                    if(total_price > 0) {
                                        $("#totalPrice").text(result_price + " ریال  ");
                                    } else {
                                        $("#totalPrice").text("") 
                                    }
                                    if (!document.getElementById(`small_ticket_${result.number}`)) {
                                        var ticket_name = title?.length ? `بخش ${title} - ردیف 1 - جایگاه ${result.number}` : `ردیف 1 - جایگاه ${result.number}`;
                                        $("#reservedPositions").append(`<div class="tag-item-box" id="small_ticket_${result.number}">${ticket_name}<button onclick="deleteSeat(${result.number})"><i class="fa-regular fa-xmark"></i></button></div>`)
                                        $("#displayTickets").append(`<div class="tag-item-box" id="small_ticket_${result.number}">${ticket_name}<button onclick="deleteSeat(${result.number})" type="button"><i class="fa-regular fa-xmark"></i></button></div>`)
                                    }
                                    $(".submit_seats").attr("data-disabled" , "false");
                                    $(".submit_seats").removeAttr("disabled");

                                    seatGeoJsons["location_" + id].setFeatureStyle(result.number, {
                                        color: `rgb(${cs.getPropertyValue("--rgb-blue-500")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-blue-500")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    });
                                    layer.properties.status = "selected"
                                    setLayerStatus(e.layer, "selected")
                                }
                            else if(result.status == "reserved")
                                {
                                    seatGeoJsons["location_" + id].setFeatureStyle(result.number, {
                                        color: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    });
                                    layer.properties.status = "reserved";
                                }
                            else if(result.status == "l")
                                {
                                    seatGeoJsons["location_" + id].setFeatureStyle(result.number, {
                                        color: `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    });
                                    layer.properties.status = "locked";
                                }
                            else if(result.status == "selled")
                                {
                                    layer.properties.status = "selled";
                                }
                            else if(result.status == "removed" && layer.options.color != `rgb(${cs.getPropertyValue("--rgb-green-500")})`)
                                {
                                    if (status == "new") {
                                        snackbar("map_snackbar_18394829", "این جایگاه از قبل انتخاب شده بوده و شما از حالت انتخاب خارج نمودید.", "danger", {
                                            hasIcon: true,
                                        });
                                        return;
                                    }
                                    document.querySelectorAll("#small_ticket_"+result.number).forEach(el => el.remove())
                                    total_price -= result.price
                                    var ticket_string_price = total_price.toString();
                                    var result_price = commafy(ticket_string_price);
                                    $("#totalPrice").text(result_price + " ریال  ");
                                    if(total_price ==  0)
                                        {
                                            $("#totalPrice").text("هنوز بلیطی را انتخاب نکرده اید!");
                                            $(".submit_seats").attr("data-disabled" , "true");
                                            $(".submit_seats").attr("disabled" , "disabled");
                                        }

                                    seatGeoJsons["location_" + id].setFeatureStyle(result.number, {
                                        color: `rgb(${cs.getPropertyValue("--rgb-green-500")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-green-500")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    });
                                    $(this).attr("data-position-delete", properties.position);
                                    layer.properties.status = "empty"
                                    setLayerStatus(e.layer, "empty")
                                    lastClickedSeatId = null;
                                }    
                            else if(result.status == "error")
                                {
                                    snackbar("element_2301",result.message, "danger", {
                                        duration: 3000,
                                        hasIcon: true
                                    })
                                    return;
                                }

                            if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-green-500")})`) {

                            } else if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-blue-500")})`) {

                            } else if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-amber-500")})`) {
                                areaParsers[`innerParser_${id}`].setFeatureStyle(result.number, {
                                    color: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                    fillColor: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                    weight: 3,
                                    opacity: 1,
                                    fillOpacity: 0.7,
                                    fill: true,
                                });
                                snackbar("map_snackbar_18394829", "این جایگاه از قبل رزرو شده است و غیر قابل انتخاب می باشد.", "danger", {
                                    hasIcon: true,
                                });
                            } else if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-slate-400")})`) {
                                snackbar("map_snackbar_18394829", "این جایگاه فضای خالی بوده و غیر قابل انتخاب می باشد.", "danger", {
                                    hasIcon: true,
                                });
                            } else if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`) {
                                snackbar("map_snackbar_18394829", "این جایگاه قفل بوده و غیر قابل انتخاب می باشد.", "danger", {
                                    hasIcon: true,
                                });
                            } else if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-red-500")})`) {
                                areaParsers[`innerParser_${id}`].setFeatureStyle(result.number, {
                                    color: `rgb(${cs.getPropertyValue("--rgb-red-500")})`,
                                    fillColor: `rgb(${cs.getPropertyValue("--rgb-red-500")})`,
                                    weight: 3,
                                    opacity: 1,
                                    fillOpacity: 0.7,
                                    fill: true,
                                });
                                snackbar("map_snackbar_18394829", "این جایگاه فروخته شده است و غیر قابل انتخاب می باشد.", "danger", {
                                    hasIcon: true,
                                });
                            }
                        }
                    }
                })
                if (isInitMap) {
                    seatGeoJsons["location_" + id].addTo(seatMap).bringToFront();
                    if (defaultItem.seat_id) {
                        var sliceVar = {...seatJsons[id]}
                            sliceVar.features = sliceVar.features.filter(f => f.properties.TxtMemo == defaultItem.seat_id)
                            if (sliceVar.features.length)
                                setPaneToParser(sliceVar, seatMap)
                            else setPaneToParser(seatJsons[id], seatMap)
                            sliceVar = undefined
                    } else {
                        setPaneToParser(seatJsons[id], seatMap)
                    }
                }
                function setLayerStatus(layer, status) {
                    layer.properties.status = status
                    seatJsons[id].features.map(feature => {
                        if (feature.properties.TxtMemo === layer.properties.TxtMemo) {
                            feature.properties.status = status
                        }
                        return feature
                    })
                }
        }

        setParsers()

        return {
            setParsers,
            setPlaces
        }
    } else if (type == 'area') {
        if (isInitMap) {
            // $(document).on("themeChanged", async function (e) {
            //     initializedSeatMaps = initializedSeatMaps.filter(i => i !== "seat_map_set")
            //     const {setParsers} = initSeatMap(id, isInitMap, lat, lng, zoom, type, token, ticket_node_id, ticket_node_sans_id)
            //     setParsers(id, var_name, color_name);
            //     if (areaParsers[id]) areaParsers[id].removeFrom(seatMap);
            //     await scriptLoader.loadScriptsSequentially(app_config["_map_area_selection_layers"]["area_item_1"]["scripts"]);
            //     app_config["_map_area_selection_layers"]["area_item_1"]?.var_name.forEach((var_name, index) => {
            //         if (areaParsers[id]) {
            //             areaParsers[id].removeFrom(seatMap);
            //             // Check if is last item
            //             if (app_config["_map_area_selection_layers"]["area_item_1"]?.var_name.length == index + 1)
            //                 setParsers(id, var_name, color_name);
            //         }
            //     })
            // });
        }
        var lastPosition;
        /* Selection Area Geo Json Start */
        function setParsers(id, var_name, color_name = '--rgb-gray-500') {
            if (apiResult.options.length == 1) {
                lastPosition = apiResult.options[0]
                let position = apiResult.options[0]
                setPlaces(position.id, position.json_id, id, {lat:"",lng:""})
                return;
            }

            if (seatMap) window[id] = seatMap.createPane(id);
            areaParsers[id] = L.vectorGrid
                .slicer(window[var_name], {
                    maxZoom: 22,
                    minNativeZoom: 0,
                    rendererFactory: L.canvas.tile,
                    pane: seatMap ? id : '',
                    vectorTileLayerStyles: {
                        sliced: function (properties, zoom) {
                            let position = apiResult.options.find(o => o.id == properties.Id)
                            if (position) 
                                return {
                                    fillColor: `rgb(${cs.getPropertyValue(`--rgb-${position.fillColor}` || color_name)})`,
                                    color: `rgb(${cs.getPropertyValue(`--rgb-${position.fillColor}` || color_name)})`,
                                    weight: 3,
                                    opacity: 1,
                                    fillOpacity: 0.7,
                                    fill: true,
                                    interactive: true
                                };
                            else
                                return {
                                    color: false,
                                    fillColor: false,
                                    opacity: 0,
                                    fillOpacity: 0,
                                    weight: 0,
                                    stroke: false,
                                    fill: false,
                                    interactive: false,
                                };
                        },
                    },
                    interactive: true,
                    preferCanvas: false,
                    getFeatureId: function (feature) {
                        return feature.properties.Id.toString()
                    },
                })
            if (isInitMap) {
                areaParsers[id]
                .on("mouseover", function (e) {
                    if (timeoutPopup) clearTimeout(timeoutPopup)
                    const properties = e.layer.properties
                    const position = apiResult.options.find(o => o.id == properties.Id)
                    if (position) e.layer.properties.Name = position.name
                    var layer = e.layer;
                    var latlng = e.latlng;
                    onAreaSelectionFeature(layer, layer, e.latlng, [0, 5])
                })
                .on("mouseout", function (e) {
                    timeoutPopup = setTimeout(() => {
                        seatMap.closePopup();
                        if (timeoutPopup) clearTimeout(timeoutPopup)
                    }, 100)
                })
                .on("click", async function (e) {
                    const properties = e.layer.properties
                    const latlng = e.latlng
                    const position = apiResult.options.find(o => o.id == properties.Id)
                    if (position) {
                        e.layer.properties.name = position.name
                        lastPosition = position
                        setPlaces(position.id, position.json_id, id, latlng)
                    }
                })
                .addTo(seatMap).bringToFront();
                setPaneToParser(window[var_name], seatMap)
                handlePaneClick(window[id])
                const handleResetBtn = function () {
                    $("#resetBtn").unbind('click', handleResetBtn)
                
                    for(var key in areaParsers) {
                        if (areaParsers[key]) {
                            areaParsers[key].removeFrom(seatMap)
                        }
                    }
                    $("#resetBtn").addClass('hide')
                    setParsers(id, var_name, color_name);
                }
                $("#resetBtn").unbind('click')
                $("#resetBtn").on('click', handleResetBtn)
                // const handleThemeChanged = async function (e) {
                //     $(document).unbind("themeChanged", handleThemeChanged);
                //     initializedSeatMaps = initializedSeatMaps.filter(i => i !== "seat_map_set")
                //     const {setParsers} = initSeatMap(id, isInitMap, lat, lng, zoom, type, token, ticket_node_id, ticket_node_sans_id, title)
                //     setParsers(id, var_name, color_name);
                //     if (areaParsers[id]) areaParsers[id].removeFrom(seatMap);
                //     await scriptLoader.loadScriptsSequentially(app_config["_map_area_selection_layers"]["area_item_1"]["scripts"]);
                //     app_config["_map_area_selection_layers"]["area_item_1"]?.var_name.forEach((var_name, index) => {
                //         if (areaParsers[id]) {
                //             areaParsers[id].removeFrom(seatMap);
                //             // Check if is last item
                //             if (app_config["_map_area_selection_layers"]["area_item_1"]?.var_name.length == index + 1)
                //                 setParsers(id, var_name, color_name);
                //         }
                //     })
                // }
                // $(document).on("themeChanged", handleThemeChanged);
            }
        }

        async function setPlaces(id, var_name, parentId = null, latlng = {lat: '', lng: ''}, defaultItem = {
            slice_id: null, 
            color_name: '--rgb-gray-500',
            json_id: '',
            id: 'random'
        }) {
            await new Promise(async (resolve) => {
                /** Call api start */
                const position = apiResult.options.find(o => o.id == id)
                const type = 'map_block'
                if (!position) return;
                var totalSeatsCapacity = 0;
                await $.ajax({
                    type:"Post",
                    url: PATHFILE+"execute/ticket/reserve/sen_sub",
                    data:"token="+token+"&ticket_node_id="+ticket_node_id+"&ticket_node_sans_id="+ticket_node_sans_id+"&ticket_pattern_sub_id="+ticket_node_sans_id+"&lat="+latlng.lat+"&lng="+latlng.lng+"&ticket_pattern_sub_id="+position.id+"&ticket_pattern_json_id="+position.json_id+"&type="+type,
                    cache:"false",
                    success: function(data) {
                        data = JSON.parse(data)
                        var statusObject = {
                            reserved: data?.reserved || [],
                            selled: data?.selled || [],
                            empty: data?.empty || [],
                            space: data?.space || [],
                            selected: data?.selected || []
                        }
                        window[position.json_id] = L.geoJSON(window[position.json_id]).eachLayer(function (layer) {
                            // layer.feature.properties.price = 100000
                            layer.feature.properties.status = "empty"
                            for (var key in statusObject) {
                                if (layer.feature.properties?.con?.length) {
                                    if(!eval(layer.feature.properties.con)) {
                                        layer.feature.properties.status = "space";
                                    } else {
                                        if (statusObject[key].map(i => i.toString()).includes(layer.feature.properties.TxtMemo?.toString())) {
                                            layer.feature.properties.status = key
                                        }
                                    }
                                } else {
                                    if (statusObject[key].map(i => i.toString()).includes(layer.feature.properties.TxtMemo?.toString())) {
                                        layer.feature.properties.status = key
                                    }
                                }
                            }
                            totalSeatsCapacity++;
                        }).toGeoJSON()
                        $("#hall_count").text(totalSeatsCapacity);
                    }
                })
                /** Call api end */
                if (isInitMap) {
                    if (parentId && areaParsers[parentId]) {
                        areaParsers[parentId]?.removeFrom(seatMap)
                        $("#resetBtn").removeClass("hide")
                    }
                    if (defaultItem.json_id?.length) {
                        const handleResetBtn = function () {
                            $("#resetBtn").unbind('click', handleResetBtn)
                            for(var key in areaParsers) {
                                if (areaParsers[key]) {
                                    areaParsers[key].removeFrom(seatMap)
                                }
                            }
                            $("#resetBtn").addClass('hide')
                            setParsers(defaultItem.id, defaultItem.json_id, defaultItem.color_name);
                        }
                        $("#resetBtn").unbind('click')
                        $("#resetBtn").on('click',handleResetBtn)
                    }
                    window[`pane_${id}`] = seatMap.createPane(`pane_${id}`);
                }
                areaParsers[`innerParser_${id}`] = L.vectorGrid
                    .slicer(window[var_name], {
                        maxZoom: 22,
                        minNativeZoom: 0,
                        rendererFactory: L.canvas.tile,
                        pane: id ? `pane_${id}` : '',
                        vectorTileLayerStyles: {
                            sliced: function (properties, zoom) {
                                if (properties.TxtMemo != null && properties.status === "empty") {
                                    return {
                                        color: `rgb(${cs.getPropertyValue("--rgb-green-500")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-green-500")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    };
                                } else if (properties.TxtMemo != null && properties.status === "reserved") {
                                    return {
                                        color: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    };
                                } else if (properties.TxtMemo != null && properties.status === "space") {
                                    return {
                                        color: `rgb(${cs.getPropertyValue("--rgb-slate-400")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-slate-400")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    };
                                } else if (properties.TxtMemo != null && properties.status === "selected") {
                                    return {
                                        color: `rgb(${cs.getPropertyValue("--rgb-blue-500")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-blue-500")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    };
                                } else if (properties.TxtMemo != null && properties.status === "selled") {
                                    return {
                                        color: `rgb(${cs.getPropertyValue("--rgb-red-500")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-red-500")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    };
                                } else if (properties.TxtMemo != null && properties.status === "locked") {
                                    return {
                                        color: `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    };
                                } else {
                                    return {
                                        color: false,
                                        fillColor: false,
                                        opacity: 0,
                                        fillOpacity: 0,
                                        weight: 0,
                                        stroke: false,
                                        fill: false,
                                    };
                                }
                            },
                        },
                        interactive: true,
                        preferCanvas: false,
                        getFeatureId: function (feature) {
                            if (feature.properties.TxtMemo) {
                                return feature.properties.TxtMemo.toString();
                            } else return feature.properties.Shape_Area.toString() + feature.properties.Shape_Leng.toString();
                        },
                    })

                if (isInitMap) 
                    areaParsers[`innerParser_${id}`]
                    .on("mouseover", function (e) {
                        if (timeoutPopup) clearTimeout(timeoutPopup)
                        var layer = e.layer;
                        var latlng = e.latlng;
                        if (layer.properties.TxtMemo) {
                            var TxtMemo = layer.properties.TxtMemo
                            if (!layersPopup[layer.properties.TxtMemo.toString()]) {
                                layersPopup[layer.properties.TxtMemo.toString()] = L.popup({ offset: [0, 5] })
                                    .setContent("جایگاه "+ TxtMemo)
                                    .setLatLng(latlng)
                                    .openOn(seatMap)
                            } else {
                                layersPopup[layer.properties.TxtMemo.toString()]
                                    .setLatLng(latlng)
                                    .openOn(seatMap)
                            }
                        }
                    })
                    .on("mouseout", function (e) {
                        timeoutPopup = setTimeout(() => {
                            seatMap.closePopup();
                            if (timeoutPopup) clearTimeout(timeoutPopup)
                        }, 100)
                    })
                    .on("click", async function (e) {
                        if (Date.now() - lastClickedOnSeats < 50) {
                            lastClickedOnSeats = Date.now()
                            return;
                        } else {
                            lastClickedOnSeats = Date.now()
                        }
                        var layer = e.layer;
                        var properties = e.layer.properties;
                        if (properties.TxtMemo != null) {
                            lastClickedSeatId = properties.TxtMemo.toString();
                            if (properties.TxtMemo != null) {
                                var status;
                                if([`rgb(${cs.getPropertyValue("--rgb-green-500")})`, `rgb(${cs.getPropertyValue("--rgb-amber-500")})`].includes(layer.options.color)) {
                                    status = "new";
                                } else if(layer.options.color === `rgb(${cs.getPropertyValue("--rgb-blue-500")})`) {
                                    status = "remove";
                                } else if([`rgb(${cs.getPropertyValue("--rgb-slate-400")})`, `rgb(${cs.getPropertyValue("--rgb-red-500")})`, `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`].includes(layer.options.color)) {
                                    return;
                                }
                                var data_ditails = await setSelected(status,properties.price,lastClickedSeatId,id, lastPosition?.name || title);
                                var result  = JSON.parse(data_ditails);
                                if(result.status == "selected" && layer.options.color != `rgb(${cs.getPropertyValue("--rgb-blue-500")})`)
                                    {
                                        total_price += result.price;
                                        var ticket_string_price = total_price.toString();
                                        var result_price = commafy(ticket_string_price);
                                        if(result_price.length) {
                                            $("#totalPrice").text(result_price + " ریال  ");
                                        } else {
                                            $("#totalPrice").text("")
                                        }
                                        if (!document.getElementById(`small_ticket_${result.number}`)) {
                                            var ticket_name = (lastPosition?.name || title) ? `${lastPosition?.name || title} - ردیف 1 - جایگاه ${result.number}` : `ردیف 1 - جایگاه ${result.number}`;
                                            $("#reservedPositions").append(`<div class="tag-item-box" id="small_ticket_${result.number}">${ticket_name}<button onclick="deleteSeat(${result.number},'area', ${lastPosition?.id})"><i class="fa-regular fa-xmark"></i></button></div>`)
                                            $("#displayTickets").append(`<div class="tag-item-box" id="small_ticket_${result.number}">${ticket_name}<button onclick="deleteSeat(${result.number},'area', ${lastPosition?.id})" type="button"><i class="fa-regular fa-xmark"></i></button></div>`)
                                        }
                                        $(".submit_seats").attr("data-disabled" , "false");
                                        $(".submit_seats").removeAttr("disabled");

                                        areaParsers[`innerParser_${id}`].setFeatureStyle(result.number, {
                                            color: `rgb(${cs.getPropertyValue("--rgb-blue-500")})`,
                                            fillColor: `rgb(${cs.getPropertyValue("--rgb-blue-500")})`,
                                            weight: 3,
                                            opacity: 1,
                                            fillOpacity: 0.7,
                                            fill: true,
                                        });
                                        layer.properties.status = "selected"
                                        setLayerStatus(e.layer, "selected")

                                    }
                                else if(result.status == "reserved")
                                    {
                                        layer.properties.status = "reserved";
                                        areaParsers[`innerParser_${id}`].setFeatureStyle(result.number, {
                                            color: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                            fillColor: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                            weight: 3,
                                            opacity: 1,
                                            fillOpacity: 0.7,
                                            fill: true,
                                        });
                                    }
                                else if(result.status == "l")
                                    {
                                        layer.properties.status = "locked";
                                        areaParsers[`innerParser_${id}`].setFeatureStyle(result.number, {
                                            color: `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`,
                                            fillColor: `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`,
                                            weight: 3,
                                            opacity: 1,
                                            fillOpacity: 0.7,
                                            fill: true,
                                        });
                                    }
                                else if(result.status == "selled")
                                    {
                                        layer.properties.status = "selled";
                                        areaParsers[`innerParser_${id}`].setFeatureStyle(result.number, {
                                            color: `rgb(${cs.getPropertyValue("--rgb-red-500")})`,
                                            fillColor: `rgb(${cs.getPropertyValue("--rgb-red-500")})`,
                                            weight: 3,
                                            opacity: 1,
                                            fillOpacity: 0.7,
                                            fill: true,
                                        });
                                    }
                                else if(result.status == "removed" && layer.options.color != `rgb(${cs.getPropertyValue("--rgb-green-500")})`)
                                    {
                                        if (status == "new") {
                                            snackbar("map_snackbar_18394829", "این جایگاه از قبل انتخاب شده بوده و شما از حالت انتخاب خارج نمودید.", "danger", {
                                                hasIcon: true,
                                            });
                                            return;
                                        }
                                        document.querySelectorAll("#small_ticket_"+result.number).forEach(el => el.remove())
                                        total_price -= result.price
                                        var ticket_string_price = total_price.toString();
                                        var result_price = commafy(ticket_string_price);
                                        $("#totalPrice").text(result_price + " ریال  ");
                                        if(total_price ==  0)
                                            {
                                                $("#totalPrice").text("هنوز بلیطی را انتخاب نکرده اید!");
                                                $(".submit_seats").attr("data-disabled" , "true");
                                                $(".submit_seats").attr("disabled" , "disabled");
                                            }

                                        areaParsers[`innerParser_${id}`].setFeatureStyle(result.number, {
                                            color: `rgb(${cs.getPropertyValue("--rgb-green-500")})`,
                                            fillColor: `rgb(${cs.getPropertyValue("--rgb-green-500")})`,
                                            weight: 3,
                                            opacity: 1,
                                            fillOpacity: 0.7,
                                            fill: true,
                                        });
                                        $(this).attr("data-position-delete", properties.position);
                                        layer.properties.status = "empty"
                                        setLayerStatus(e.layer, "empty")
                                        lastClickedSeatId = null;
                                    }    
                                else if(["error",'auth'].includes(result.status))
                                    {
                                        snackbar("element_2301",result.message, "danger", {
                                            duration: 3000,
                                            hasIcon: true
                                        })
                                        return;
                                    }    

                                if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-green-500")})`) {

                                } else if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-blue-500")})`) {

                                } else if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-amber-500")})`) {
                                    areaParsers[`innerParser_${id}`].setFeatureStyle(result.number, {
                                        color: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-amber-500")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    });
                                    snackbar("map_snackbar_18394829", "این جایگاه از قبل رزرو شده است و غیر قابل انتخاب می باشد.", "danger", {
                                        hasIcon: true,
                                    });
                                } else if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-slate-400")})`) {
                                    snackbar("map_snackbar_18394829", "این جایگاه فضای خالی بوده و غیر قابل انتخاب می باشد.", "danger", {
                                        hasIcon: true,
                                    });
                                } else if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-yellow-700")})`) {
                                    snackbar("map_snackbar_18394829", "این جایگاه قفل بوده و غیر قابل انتخاب می باشد.", "danger", {
                                        hasIcon: true,
                                    });
                                } else if (layer.options.color === `rgb(${cs.getPropertyValue("--rgb-red-500")})`) {
                                    areaParsers[`innerParser_${id}`].setFeatureStyle(result.number, {
                                        color: `rgb(${cs.getPropertyValue("--rgb-red-500")})`,
                                        fillColor: `rgb(${cs.getPropertyValue("--rgb-red-500")})`,
                                        weight: 3,
                                        opacity: 1,
                                        fillOpacity: 0.7,
                                        fill: true,
                                    });
                                    snackbar("map_snackbar_18394829", "این جایگاه فروخته شده است و غیر قابل انتخاب می باشد.", "danger", {
                                        hasIcon: true,
                                    });
                                }
                            }
                        }
                    })
                    .addTo(seatMap).bringToFront();

                if (isInitMap) {
                    handlePaneClick(window[`pane_${id}`])
                    var sliceVar;
                    if (defaultItem.slice_id) {
                        sliceVar = {...window[var_name]}
                        sliceVar.features = sliceVar.features.filter(f => f.properties.TxtMemo == defaultItem.slice_id)
                        if (sliceVar.features.length)
                            setPaneToParser(sliceVar, seatMap)
                        else setPaneToParser(window[var_name], seatMap)
                        sliceVar = undefined
                    } else {
                        setPaneToParser(window[var_name], seatMap)
                    }
                    // const handleThemeChanged = function (e) {
                    //     $(document).unbind("themeChanged", handleThemeChanged);
                    //     if (areaParsers[`innerParser_${id}`]) areaParsers[`innerParser_${id}`].removeFrom(seatMap)
                    // }
                    // $(document).on("themeChanged", handleThemeChanged);
                }

                function setLayerStatus(layer, status) {
                    layer.properties.status = status
                    window[var_name].features.map(feature => {
                        if (feature.properties.TxtMemo === layer.properties.TxtMemo) {
                            feature.properties.status = status
                        }
                        return feature
                    })
                }
                resolve()
            })
        }

        async function onAreaSelectionFeature(feature, layer, latlng, offset = [0, 0]) {
            if (feature.properties) {
                const create_div = document.createElement("div");
                create_div.className = "d-flex flex-column";

                // info-box
                const create_div_info = document.createElement("div");
                create_div_info.className = "d-flex flex-column mt-2 mb-2";

                var i = 1;
                if (app_config["_map_area_selection_layers"]["area_item_1"]?.["scripts"]) {
                    await scriptLoader.loadScriptsSequentially(app_config["_map_area_selection_layers"]["area_item_1"]?.["scripts"]);
                }
                for (var key in app_config["_map_area_selection_layers"]["area_item_1"]["fields"]) {
                    if (!feature.properties[key]) continue;
                    window["create_div_info_box_"+i] = document.createElement("div");
                    window["create_div_info_box_"+i].className = "d-flex flex-row justify-content-between align-items-center my-1 gap-2";
                    window["create_div_info_box_"+i+"_head"] = document.createElement("span");
                    window["create_div_info_box_"+i+"_head"].className = "fs-14 fw-500";
                    window["create_div_info_box_"+i+"_head"].innerHTML = app_config["_map_area_selection_layers"]["area_item_1"]["fields"][key];
                    window["create_div_info_box_"+i+"_body"] = document.createElement("span");
                    window["create_div_info_box_"+i+"_body"].className = "fs-13 text-darkest fw-400";
                    window["create_div_info_box_"+i+"_body"].innerHTML = feature.properties[key] ?? "--";
                    window["create_div_info_box_"+i].appendChild(window["create_div_info_box_"+i+"_head"]);
                    window["create_div_info_box_"+i].appendChild(window["create_div_info_box_"+i+"_body"]);
                    create_div_info.appendChild(window["create_div_info_box_"+i]);
                    i++;
                }

                if (i > 1)
                {
                    create_div.appendChild(create_div_info);
                    areaSelectionPopup = L.popup({ offset })
                        .setContent(create_div)
                        .setLatLng(latlng)
                        .openOn(seatMap)
                        .on("remove", function () {
                            
                        });
                }
            }
        }
        /* Selection Area Geo Json End */
        return {
            setParsers,
            setPlaces,
            onAreaSelectionFeature
        }
    }
}

function isWebView() {
    const userAgent = navigator.userAgent;
    const isAndroidWebView = /wv/.test(userAgent);
    const isIOSWebView = /(iPhone|iPod|iPad).*AppleWebKit(?!.*Safari)/.test(userAgent);
    const isLegacyAndroidWebView = /Version\/[\d.]+.*Chrome/.test(userAgent);
    const isFaragardWebview = userAgent.includes('FaragardWebView');
    const isAndroid = typeof Android != 'undefined' || typeof FaragardInterface != 'undefined';
    return isAndroidWebView || isIOSWebView || isLegacyAndroidWebView || isAndroid || isFaragardWebview;
}

function checkBrowserVersion(link = "") {
    if (isWebView() || getCookie("check_browser_ver") == "true") return;
    const userAgent = navigator.userAgent;
    let browserName, version;

    if (userAgent.indexOf("Chrome") > -1) {
        browserName = "Chrome";
        version = userAgent.match(/Chrome\/(\d+)/)[1];
    } else if (userAgent.indexOf("Firefox") > -1) {
        browserName = "Firefox";
        version = userAgent.match(/Firefox\/(\d+)/)[1];
    } else if (userAgent.indexOf("Safari") > -1) {
        browserName = "Safari";
        version = userAgent.match(/Version\/(\d+)/)[1];
    } else if (userAgent.indexOf("Edge") > -1) {
        browserName = "Edge";
        version = userAgent.match(/Edge\/(\d+)/)[1];
    } else {
        console.warn("مرورگر شناسایی نشده است.")
        return;
    }

    const latestVersions = {
        Chrome: 140.0,
        Firefox: 142.0,
        Safari: 23.0,
        Edge: 140.0,
    };

    if (latestVersions[browserName] && parseInt(version) < latestVersions[browserName] && getCookie("check_browser_ver") != "true") {
        setCookie("check_browser_ver", "true");
        snackbar("element_snackbar_18535934", `لطفاً مرورگر خود را به آخرین نسخه ${browserName} ${latestVersions[browserName]} به‌روز کنید.`, "warning", {
            duration: null,
            isConfirmed: true,
            hasIcon: true,
            acceptText: "بله",
            cancelText: "نه، فعلا!",
            textStyles: {
                fontWeight: "bold",
                textAlign: "right"
            },
            iconStyles: {
                color: "rgb(var(--rgb-darkest))"
            }
        })
            .then((data) => {
                if (data.isConfirmed) {
                    if (link.length) window.location.href = link
                }
            })
    }
}
$(document).ready(() => checkBrowserVersion("https://soft98.ir/internet/web-browser/"))

function startTabRotation(navTabId, delay = 10000) {
    let tabIndex = 0;
    let userInteracted = false;
    let timeout;
    let resetTimeout;

    const navTab = document.getElementById(navTabId);
    const tabs = navTab.querySelectorAll('li > button');

    document.addEventListener("mousemove", () => {
        userInteracted = true;
        clearTimeout(resetTimeout);
        clearTimeout(timeout);

        resetTimeout = setTimeout(() => {
            userInteracted = false;
            rotateTabs();
        }, delay);
    });

    const rotateTabs = () => {
        if (userInteracted) return;
        tabs[tabIndex].click();
        tabIndex = (tabIndex + 1) % tabs.length;
        timeout = setTimeout(rotateTabs, delay);
    };

    rotateTabs();

    function clear() {
        clearTimeout(timeout);
        clearTimeout(resetTimeout);
    }

    return { clear };
}

class ClickAndDragHandler {
    constructor(element) {
        this.element = element;
        this.drag = false;
        this.startX = 0;
        this.startY = 0;
        this.scrollLeft = 0;
        this.startDragging = false;
        this.dragThreshold = 5; // Threshold to distinguish between click and drag

        this.element.addEventListener('pointerdown', this.handleDown.bind(this), false);
        this.element.addEventListener('pointermove', this.handleMove.bind(this), false);
        this.element.addEventListener('pointerup', this.handleUp.bind(this), false);
        this.element.addEventListener('click', this.handleClick.bind(this), false);
    }

    handleDown(e) {
        this.drag = false;
        this.startDragging = true;

        // Start moving
        e.stopPropagation();
        e.preventDefault();

        this.startX = e.clientX;
        this.startY = e.clientY;
        this.scrollLeft = this.element.scrollLeft;
    }

    handleMove(e) {
        if (!this.startDragging) return;

        const moveX = e.clientX - this.startX;
        const moveY = e.clientY - this.startY;

        if (Math.abs(moveX) > this.dragThreshold || Math.abs(moveY) > this.dragThreshold) {
            this.drag = true;
        }

        if (this.drag) {
            e.stopPropagation();
            e.preventDefault();
            const x = e.pageX - this.element.offsetLeft;
            const scroll = x - this.startX;
            this.element.scrollLeft = this.scrollLeft - scroll;
        }
    }

    handleUp(e) {
        this.startDragging = false;

        if (this.drag) {
            // Handle drag behavior
            e.stopPropagation();
            e.preventDefault();
        }
    }

    handleClick(e) {
        if (this.drag) {
            e.stopPropagation();
            e.preventDefault();
        } else {
            // Handle click behavior
            console.log('Element clicked!');
        }
    }
}
/*
class DragManager {
    draggableSelector;
    constructor(draggableSelector = '.ui-draggable') {
        this.draggableSelector = draggableSelector;
        this.observer = null;
        // this.initObserver();
        this.setupExistingElements();
    }
  
    initObserver() {
        this.observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if ($(node).is(this.draggableSelector)) {
                        this.setupDrag(node)
                    } else if (node.nodeType === 1) {
                        $(node).find(this.draggableSelector).each((i, el) => this.setupDrag(el));
                    }
                });
            });
        });
    
        this.observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
  
    setupExistingElements() {
        $(this.draggableSelector).each((i, el) => this.setupDrag(el));
    }
  
    setupDrag(element) {
    //   const $element = $(element);
    //   console.log($element)
    //   if ($element.data('drag-enabled')) return;
  
    //   $element
    //     .attr('draggable', 'true')
    //     .css({ 'touch-action': 'none', 'user-select': 'none' })
    //     .data('drag-enabled', true);
  
    //   $element.on('mousedown touchstart', (e) => {
    //     e.preventDefault();
    //     this.startDrag(e, $element);
    //   });
  
    //   $element.on('dragstart', (e) => e.preventDefault());
    }
  
    startDrag(e, $element) {
      const isTouch = e.type === 'touchstart';
      const clientX = isTouch ? e.touches[0].clientX : e.clientX;
      const clientY = isTouch ? e.touches[0].clientY : e.clientY;
  
      const rect = $element[0].getBoundingClientRect();
      const offsetX = clientX - rect.left;
      const offsetY = clientY - rect.top;
  
      const onMove = (moveEvent) => {
        moveEvent.preventDefault();
        const moveX = isTouch ? moveEvent.touches[0].clientX : moveEvent.clientX;
        const moveY = isTouch ? moveEvent.touches[0].clientY : moveEvent.clientY;
  
        $element.css({
          position: 'absolute',
          left: `${moveX - offsetX}px`,
          top: `${moveY - offsetY}px`,
          zIndex: 1000
        });
      };
  
      const onEnd = () => {
        $(document).off(isTouch ? 'touchmove' : 'mousemove', onMove);
        $(document).off(isTouch ? 'touchend' : 'mouseup', onEnd);
        $element.css('zIndex', '');
      };
  
      $(document).on(isTouch ? 'touchmove' : 'mousemove', onMove);
      $(document).on(isTouch ? 'touchend' : 'mouseup', onEnd);
    }
}
*/

class DragManager {
    constructor(draggableSelector = '.ui-draggable') {
      this.draggableSelector = draggableSelector;
      this.setupExistingElements();
    //   this.initObserver();
    }

    initObserver() {
        this.observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if ($(node).is(this.draggableSelector)) {
                        if (!$(node).hasClass("dragging-setup")) this.setupDrag(node)
                    } else if (node.nodeType === 1) {
                        $(node).find(this.draggableSelector).each((i, el) => {
                            if (!$(node).hasClass("dragging-setup")) this.setupDrag(el);
                        });
                    }
                });
            });
        });
    
        this.observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
  
    setupExistingElements() {
      $(this.draggableSelector).each((i, el) => this.setupDrag(el));
    }
  
    setupDrag(element) {
        const $element = $(element);
        $element.addClass("dragging-setup");
        if ($element.data('drag-enabled')) return;
        var startDragging = (e) => {
            this.startDrag(e, $element);
        };
        // $element.off('mousedown touchstart', startDragging);
        $element
            .css({ 'touch-action': 'none', 'user-select': 'none' })
            .data('drag-enabled', true);

        $element.on('mousedown touchstart', startDragging);
    }
  
    startDrag(e, $element) {
        const isTouch = e.type === 'touchstart';
        const getEvent = (event) => (isTouch && event.touches ? event.touches?.[0] : event);
    
        const startEvent = getEvent(e);
        const rect = $element[0].getBoundingClientRect();
        const offsetX = startEvent.clientX - rect.left;
        const offsetY = startEvent.clientY - rect.top;
    
        const startX = startEvent.clientX;
        const startY = startEvent.clientY;
    
        let dragged = false;
    
        const onMove = (moveEvent) => {
            const evt = getEvent(moveEvent);
            const deltaX = Math.abs(evt.clientX - startX);
            const deltaY = Math.abs(evt.clientY - startY);
    
            if (deltaX > 5 || deltaY > 5) dragged = true;
    
            moveEvent.preventDefault();
    
            $element.css({
                position: 'absolute',
                left: `${evt.clientX - offsetX}px`,
                top: `${evt.clientY - offsetY}px`,
                zIndex: 9999
            });
        };
    
        const onEnd = (endEvent) => {
            $(document).off('mousemove touchmove', onMove);
            $(document).off('mouseup touchend', onEnd);
            $element.css('zIndex', '');
    
            if (isTouch && !dragged) {
            // simulate click if it was a tap
            const clickEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            $element[0].dispatchEvent(clickEvent);
            }
        };
    
        $(document).on('mousemove touchmove', onMove);
        $(document).on('mouseup touchend', onEnd);
    }
  }
  
// (function($) {
//     if (!$.ui || !$.ui.draggable) {
//         console.error("jQuery UI Draggable not loaded");
//         return;
//     }

//     const mouseProto = $.ui.mouse.prototype;

//     // Store original methods
//     const _mouseInit = mouseProto._mouseInit;
//     const _mouseDestroy = mouseProto._mouseDestroy;

//     mouseProto._touchStart = function(event) {
//         if (event.touches.length > 1) return;
//         this._touchMoved = false;
    
//         const touch = event.touches[0];
//         const simulatedEvent = new MouseEvent("mousedown", {
//             bubbles: true,
//             cancelable: true,
//             view: window,
//             screenX: touch.screenX,
//             screenY: touch.screenY,
//             clientX: touch.clientX,
//             clientY: touch.clientY
//         });
    
//         event.target.dispatchEvent(simulatedEvent);
//         event.preventDefault();
//     };
    
//     mouseProto._touchMove = function(event) {
//         if (event.touches.length > 1) return;
//         this._touchMoved = true;
    
//         const touch = event.touches[0];
//         const simulatedEvent = new MouseEvent("mousemove", {
//             bubbles: true,
//             cancelable: true,
//             view: window,
//             screenX: touch.screenX,
//             screenY: touch.screenY,
//             clientX: touch.clientX,
//             clientY: touch.clientY
//         });
    
//         event.target.dispatchEvent(simulatedEvent);
//     };
    
//     mouseProto._touchEnd = function(event) {
//         const touch = event.changedTouches[0];
//         const simulatedEvent = new MouseEvent("mouseup", {
//             bubbles: true,
//             cancelable: true,
//             view: window,
//             screenX: touch.screenX,
//             screenY: touch.screenY,
//             clientX: touch.clientX,
//             clientY: touch.clientY
//         });
    
//         event.target.dispatchEvent(simulatedEvent);
//     };
    

//     mouseProto._mouseInit = function() {
//         const self = this;

//         this.element[0].addEventListener("touchstart", this._touchStart.bind(this), { passive: false });
//         this.element[0].addEventListener("touchmove", this._touchMove.bind(this), { passive: false });
//         this.element[0].addEventListener("touchend", this._touchEnd.bind(this), { passive: false });

//         _mouseInit.call(this); // call the original method
//     };

//     mouseProto._mouseDestroy = function() {
//         this.element[0].removeEventListener("touchstart", this._touchStart);
//         this.element[0].removeEventListener("touchmove", this._touchMove);
//         this.element[0].removeEventListener("touchend", this._touchEnd);

//         _mouseDestroy.call(this);
//     };
// })(jQuery);  
  
    


function setActiveList() {
    const listItems = $("#scrollableTabs").children("li")
    listItems.each(function() {
        if ($(this).children(".active").hasClass("active")) {
            $(this).css('order', -10).siblings().removeAttr("style")
        }
    })
}

/* Polygon helper start */
function extractLatLngs(arr, result = []) {
    for (const item of arr) {
        if (Array.isArray(item)) {
            extractLatLngs(item, result);
        } else {
            result.push(arr);
            break;
        }
    }
    result = result.map(([lat,lng]) => ([lng, lat]))
    return result;
}

function pointInPolygon(point, polygon) {
    let x = point[0], y = point[1];
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      let xi = polygon[i][0], yi = polygon[i][1];
      let xj = polygon[j][0], yj = polygon[j][1];
      let intersect = ((yi > y) != (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
}
/* Polygon helper end */

/**
 * Map Bus start 
 */
function initBusMap(id, lat, lng, zoom, location_address_type, location_address_field, isExternal = false, map_search, dissabled, path_file, mapLoadedCallback = () => {}, preventReinit = false) {
    var map;
    if (preventReinit) {
        if (initializedMaps.includes(`map_set_${id}`)) return;
        // if isn't initialized...
        initializedMaps.push(`map_set_${id}`);
    }
    map = L.map(`map_set_${id}`, {
        measureControl: true,
        zoomControl: false,
        zoomsliderControl: false,
        attributionControl: false,
    }).setView([lat, lng], zoom);
    var bmapContent = $('.bmap-content')
    bmapContent.on('mouseenter', function () {
        map.dragging.disable();
        map.scrollWheelZoom.disable();
        map.doubleClickZoom.disable();
        map.touchZoom.disable();
        map.boxZoom.disable();
        map.keyboard.disable();
        map.options.interactive = false;
    });
    bmapContent.on('mouseleave', function () {
        map.dragging.enable();
        map.scrollWheelZoom.enable();
        map.doubleClickZoom.enable();
        map.touchZoom.enable();
        map.boxZoom.enable();
        map.keyboard.enable();
        map.options.interactive = true;
    });
    bmapContent.on('touchstart', function () {
        map.dragging.disable();
        map.scrollWheelZoom.disable();
        map.doubleClickZoom.disable();
        map.touchZoom.disable();
        map.boxZoom.disable();
        map.keyboard.disable();
        map.options.interactive = false;
    });
    bmapContent.on('touchend', function () {
        map.dragging.enable();
        map.scrollWheelZoom.enable();
        map.doubleClickZoom.enable();
        map.touchZoom.enable();
        map.boxZoom.enable();
        map.keyboard.enable();
        map.options.interactive = true;
    });
    mapLoadedCallback(map)
    for (var key in window["app_config"]["_map_types"]) {
        const options = window["app_config"]["_map_types"][key]["option"]
        window[window["app_config"]["_map_types"][key]["var_name"]] = L.tileLayer(window["app_config"]["_map_types"][key]["url"], options);
    }
    primaryTile.addTo(map).bringToBack();
    $("#change-layer_" + id).change(function () {
        if ($("#change-layer_" + id).is(":checked")) {
            map.removeLayer(sateliteTile);
            primaryTile.addTo(map).bringToBack();
            $("#change-layer-box_" + id + " > img").attr("src", path_file + "assets/images/map/google-layer.png");
            if (getCookie("theme_mode")?.length) {
                if (getCookie("theme_mode") === themeCustomDarkClass) {
                    $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
                } else {
                    $(".leaflet-map-pane").css("filter", "none");
                }
            }
        } else {
            map.removeLayer(primaryTile);
            sateliteTile.addTo(map).bringToBack();
            $("#change-layer-box_" + id + " > img").attr("src", path_file + "assets/images/map/osm-layer.png");
            if (getCookie("theme_mode")?.length) {
                if (getCookie("theme_mode") === themeCustomDarkClass) {
                    $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
                } else {
                    $(".leaflet-map-pane").css("filter", "none");
                }
            }
        }
    });
    // fullscreen
    var mapFullScreen = L.control.fullscreen({ position: window["app_config"]["_direction"] == "ltr" ? "bottomright" : "bottomleft" }).addTo(map);
    if (dissabled == "f") {
        $(`.map_search_live_input_${id}`).on("input", function (e) {
            var searchInput = $(this).val();
            var raw = JSON.stringify({
                text: searchInput,
                $filter: map_search,
            });
            var requestOptions = {
                method: "POST",
                headers: {
                    "x-api-key": API_TOKEN,
                    "Content-Type": "application/json",
                },
                body: raw,
                redirect: "follow",
            };
            var addresses = document.querySelector(`.map_search_live_result_${id}`);
            addresses.innerHTML = `
                                        <li>
                                            <a href="javascript:void(0);">
                                                <div class="title loading_title line3 loading-animation"></div>
                                                <div class="description loading_desc line3 loading-animation"></div>
                                            </a>
                                        </li>
                                        `;
            fetch("https://map.ir/search/v2/autocomplete", requestOptions)
                .then((res) => {
                    if (res.status == 200) {
                        return res.json();
                    } else {
                        addresses.innerHTML = `
                                    <li>
                                        <a href="javascript:void(0);">
                                            <div class="title loading_title line3 loading-animation"></div>
                                            <div class="description loading_desc line3 loading-animation"></div>
                                        </a>
                                    </li>
                                    `;
                    }
                    return new Error("Error :/");
                })
                .then((data) => {
                    if (data.value?.length) {
                        addresses.innerHTML = "";
                        data.value.forEach((address, index) => {
                            addresses.insertAdjacentHTML(
                                "beforeend",
                                `<li tabindex="${index + 1}">
                                            <a href="javascript:void(0);" class="search-page-places-item d-flex flex-row align-items-center gap-4 px-4 py-2" data-lat="${address.geom.coordinates[0]}" data-lng="${address.geom.coordinates[1]}">
                                                <i class="fa-regular fa-location-dot fs-16"></i>
                                                <span>
                                                    <h6 class="title">${address.title}</h6>
                                                    <p class="description m-0">${address.title}</p>
                                                </span>
                                            </a>
                                        </li>
                                        `
                            );
                        });
                        $(`ul.map_search_live_result_${id} .search-page-places-item`).click(function (e) {
                            var search_page_lat = $(this).attr("data-lat");
                            var search_page_lng = $(this).attr("data-lng");
                            map.setView([search_page_lng, search_page_lat], 16);
                            $(this).parents(".search-result").removeClass("show");
                            // Fill input value with selected item text
                            $(`.map_search_live_input_${id}`).val($(this).find("span .title").text());

                            set_marker(search_page_lat, search_page_lng);
                            $(`#location_internal_latlng_${id}`).html(search_page_lat + "-" + search_page_lng);
                            if (isExternal) {
                                $(`#foreign_location_${id}`).val(search_page_lat + "-" + search_page_lng);
                            }
                        });
                        if ($(`#search_result_${id}`).hasClass("show")) {
                            /* Implement key up and down select start */
                            const list = document.querySelector(`ul.map_search_live_result_${id}`);
                            const items = list.getElementsByTagName("li");
                            let selectedItem = null;
                            document.addEventListener("keydown", function (event) {
                                if (event.key === "ArrowDown") {
                                    event.preventDefault();
                                    if (selectedItem === null) {
                                        items[0].focus();
                                        selectedItem = items[0];
                                    } else {
                                        const index = Array.prototype.indexOf.call(items, selectedItem);
                                        if (index < items.length - 1) {
                                            items[index + 1].focus();
                                            selectedItem = items[index + 1];
                                        }
                                    }
                                } else if (event.key === "ArrowUp") {
                                    event.preventDefault();
                                    if (selectedItem === null) {
                                        items[items.length - 1].focus();
                                        selectedItem = items[items.length - 1];
                                    } else {
                                        const index = Array.prototype.indexOf.call(items, selectedItem);
                                        if (index > 0) {
                                            items[index - 1].focus();
                                            selectedItem = items[index - 1];
                                        }
                                    }
                                } else if (event.key === "Enter") {
                                    event.preventDefault();
                                    if (selectedItem !== null) {
                                        // Do something with the selected item
                                        selectedItem.querySelector("a").click();
                                    }
                                }
                            });

                            for (let i = 0; i < items.length; i++) {
                                items[i].addEventListener("click", function () {
                                    selectedItem = this;
                                });
                            }
                            /* Implement key up and down select end */
                        }
                    } else {
                        addresses.innerHTML = `
                                        <li>
                                            <a href="javascript:void(0);">
                                                <div class="title loading_title line3 loading-animation"></div>
                                                <div class="description loading_desc line3 loading-animation"></div>
                                            </a>
                                        </li>
                                        `;
                    }
                });
        });
        
        $(`#location_internal_latlng_${id}`).html(map.getCenter().lat + " , " + map.getCenter().lng);
        map.on("dragend", function (e) {
            set_marker(map.getCenter().lat, map.getCenter().lng);
            $(`#location_internal_latlng_${id}`).html(map.getCenter().lat + " , " + map.getCenter().lng);
            if (isExternal) {
                $(`#foreign_location_${id}`).val(map.getCenter().lat + " , " + map.getCenter().lng);
            }
            if (location_address_type != "none" && location_address_field != "") {
                if (location_address_type == "big_address") {
                    fetch("https://map.ir/reverse?lat=" + map.getCenter().lat + "&lon=" + map.getCenter().lng, {
                        method: "GET",
                        headers: {
                            "x-api-key": API_TOKEN,
                        },
                    })
                        .then((res) => {
                            if (res.status == 200) {
                                return res.json();
                            }
                            return new Error("Error :/");
                        })
                        .then((data) => {
                            full_address = data.postal_address;
                            $("#" + location_address_field).val(data.address);
                        });
                } else {
                    fetch("https://map.ir/fast-reverse?lat=" + map.getCenter().lat + "&lon=" + map.getCenter().lng, {
                        method: "GET",
                        headers: {
                            "x-api-key": API_TOKEN,
                        },
                    })
                        .then((res) => {
                            if (res.status == 200) {
                                return res.json();
                            }
                            return new Error("Error :/");
                        })
                        .then((data) => {
                            full_address = data.postal_address;
                            $("#" + location_address_field).val(data.postal_address);
                        });
                }
            }
        });
        var timeoutLocation;
        var location_button = document.querySelector(`#location_button_${id}`);
        location_button?.addEventListener("click", function (e) {
            e.preventDefault();
            map.locate({ setView: true, maxZoom: 16 });
            if (timeoutLocation) clearTimeout(timeoutLocation);
            timeoutLocation = setTimeout(() => {
                location_button.classList.add("locate-loader")
                map.on("locationfound", function (e) {
                    location_button.classList.remove("locate-loader")
                    map.setView(e.latlng, 14);
                });
                map.on("locationerror", function (e) {
                    location_button.classList.remove("locate-loader")
                    snackbar("map_snackbar_18394829", "موقعیت مکانی شما یافت نشد.", "danger", {
                        hasIcon: true,
                    });
                });
            }, 200);
        });
    } else {
        map.dragging.disable();
        map.touchZoom.disable();
        map.doubleClickZoom.disable();
        map.scrollWheelZoom.disable();
        map.boxZoom.disable();
        map.keyboard.disable();
        if (map.tap) map.tap.disable();
        document.getElementById(`map_set_${id}`).style.cursor = "default";
    }

    // Theme changed handle start
    if (getCookie("theme_mode")?.length) {
        if (getCookie("theme_mode") === themeCustomDarkClass) {
            $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
        } else {
            $(".leaflet-map-pane").css("filter", "none");
        }
    }
    $(document).on("themeChanged", function (e, { themeName }) {
        if (themeName === themeCustomDarkClass) {
            $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
        } else {
            $(".leaflet-map-pane").css("filter", "none");
        }
    });

    function set_marker(lat, lon) {
        $(`#element_${id}_lat`).val(lat);
        $(`#element_${id}_lan`).val(lon);
        $(`#element_${id}`).val(lat + "," + lon);
        $(`#element_${id}`).trigger("input");
    }

    return map
}

function createBusRoute(id, map, routeData, onStationClick, featureStyle = {}, featureHighlightStyle = {}) {
    const routePaneId = `${id}_overlay`;
    let routeLayer, lastClickedFeatureId;
    const pane = map.createPane(routePaneId);

    function drawRoute() {
        routeLayer = L.vectorGrid.slicer(routeData, {
            maxZoom: 22,
            minNativeZoom: 0,
            rendererFactory: L.canvas.tile,
            pane: routePaneId,
            vectorTileLayerStyles: {
                sliced: (properties, zoom) => ({
                    color: "rgb(75, 0, 130)",
                    fillColor: "rgb(75, 0, 130)",
                    weight: 5,
                    opacity: 0.9,
                    fillOpacity: 0.7,
                    fill: true,
                    smoothFactor: 1,
                    ...featureStyle,
                }),
            },
            interactive: true,
            preferCanvas: false,
            getFeatureId: feature => feature.properties.Id ? feature.properties.Id.toString() : null,
        })
            .on("click", handleRouteClick)
            .on("loading", () => $(".street_layer").addClass("is-loading"))
            .on("load", () => $(".street_layer").removeClass("is-loading"))
            .addTo(map)
            .bringToFront();
    }

    function handleRouteClick(e) {
        const layer = e.layer;
        if (lastClickedFeatureId) resetLastClickedStyle();
        const featureId = layer.properties.Id;
        applyHighlightStyle(featureId);
        lastClickedFeatureId = featureId;

        if (onStationClick) onStationClick(layer, e.latlng);
    }

    function resetLastClickedStyle() {
        routeLayer.setFeatureStyle(lastClickedFeatureId, {
            color: "rgb(75, 0, 130)",
            fillColor: "rgb(75, 0, 130)",
            weight: 5,
            opacity: 0.9,
            fillOpacity: 0.7,
            ...featureStyle,
        });
    }

    function applyHighlightStyle(featureId) {
        routeLayer.setFeatureStyle(featureId, {
            color: "rgb(55, 0, 100)",
            fillColor: "rgb(55, 0, 100)",
            fillOpacity: 1,
            opacity: 1,
            weight: 5,
            ...featureHighlightStyle,
        });
    }

    function clearRoute() {
        if (routeLayer) map.removeLayer(routeLayer);
        lastClickedFeatureId = null;
    }

    function redrawRoute(newRouteData = routeData) {
        clearRoute();
        routeData = newRouteData;
        drawRoute();
    }

    drawRoute();

    return {
        clearRoute,
        redrawRoute,
        applyHighlightStyle,
        resetLastClickedStyle,
    };
}

async function fetchTitleAndDescription(url, titleId = "", descriptionId = "") {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        const title = doc.querySelector("title")?.innerText || "بدون عنوان";
        const description =
            doc.querySelector('meta[name="description"]')?.content ||
            "بدون توضیحات";
        if (titleId?.length) document.getElementById(titleId).innerText = title;
        if (descriptionId?.length) document.getElementById(descriptionId).innerText = description
        return { title, description };
    } catch (error) {
        console.error("Error fetching title and description:", error);
        return null;
    }
}

function virtualKeyboard(containerId, targetedInputId) {
    const container = document.getElementById(containerId),
        targetedInput = document.getElementById(targetedInputId);
    const numberKeys = Array.from(container.children);
    const numberValues = numberKeys.map((key, i) => key.innerText || i);
    function shuffle(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    function updateButtonEvents(button, value) {
        button.innerText = value;
        button.onclick = function () {
            targetedInput.value += value;
            targetedInput.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
            targetedInput.focus();
        };
    }

    var backspaceBtn = document.createElement("button")
    backspaceBtn.className = "btn btn-first shadow-sm fw-semibold fs-14";
    backspaceBtn.innerHTML = `<i class="fa-regular fa-backspace"></i>`;
    backspaceBtn.onclick = () => {
        targetedInput.value = targetedInput.value.slice(0, targetedInput.value.length - 1)
        targetedInput.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
        targetedInput.focus();
    }
    container.children[3].insertAdjacentElement("afterend", backspaceBtn)
    var eraserBtn = document.createElement("button")
    eraserBtn.className = "btn btn-first shadow-sm fw-semibold fs-14";
    eraserBtn.innerHTML = `<i class="fa-regular fa-eraser"></i>`;
    eraserBtn.onclick = () => {
        targetedInput.value = ""
        targetedInput.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
        targetedInput.focus();
    }
    container.children[7].insertAdjacentElement("afterend", eraserBtn)

    const shuffledNumbers = shuffle(numberValues);

    numberKeys.forEach((key, index) => {
        updateButtonEvents(key, shuffledNumbers[index]);
    });

    return {
        closePopup: () => {
            $(container).parents(".checkout-popup").removeClass("active")
            targetedInput.setAttribute("inputmode", "numeric")
        },
        openPopup: () => {
            $(container).parents(".checkout-popup").addClass("active")
            targetedInput.setAttribute("inputmode", "none")
        },
        togglePopup: () => {
            $(container).parents(".checkout-popup").toggleClass("active")
            if ($(container).parents(".checkout-popup").hasClass("active"))
                targetedInput.setAttribute("inputmode", "none") 
            else 
                targetedInput.setAttribute("inputmode", "numeric")
        },
    }
}

function activableDiv(id, ignoredSelectors = [], notIgnoredSelectors = [], activeClass = "active") {
    const container = document.getElementById(id);

    $(document).on("click", function (event) {
        if (
            (
                ignoredSelectors.every(v => {
                    return $(event.target).closest(v).length === 0
                }) && 
                $(event.target).closest(`#${id}`).length === 0
            ) || 
            notIgnoredSelectors.some(v => {
                return $(event.target).closest(v).length !== 0
            })
        ) {
            $(container).removeClass(activeClass)
        }
    });

    return {
        close: () => {
            $(container).removeClass(activeClass)
        },
        open: () => {
            $(container).addClass(activeClass)
        },
        toggle: () => {
            $(container).toggleClass(activeClass)
        }
    }
}

function startCountdown(duration, display, onFinished = () => {}, onProgress = () => {}) {
    let timer = duration, hours, minutes, seconds, interval;
    
    const countDown = () => {
        onProgress(timer);
        hours = Math.floor(timer / 3600);
        minutes = Math.floor((timer % 3600) / 60);
        seconds = timer % 60;
        if (display.hours) display.hours.textContent = hours < 10 ? "0" + hours : hours;
        if (display.minutes) display.minutes.textContent = minutes < 10 ? "0" + minutes : minutes;
        if (display.seconds) display.seconds.textContent = seconds < 10 ? "0" + seconds : seconds;
        if (--timer < 0) {
            clearInterval(interval);
            onFinished();
        }
    };
    
    countDown();
    interval = setInterval(countDown, 1000);
    return interval;
}

function audioPlayer(url) {
    let audio;
    if (!url) return {};
    var onChangeCallback;

    function setChangeCallback(callback) {
        if (typeof callback === 'function') {
            onChangeCallback = callback;
        } else {
            console.error("onChange must be a function");
        }
    }

    function isAudioPlaying(audioElement) {
        return !audioElement.paused && !audioElement.ended;
    }

    function loadAudio() {
        if (!audio) {
            audio = new Audio(url);
            audio.addEventListener('play', () => {
                if (onChangeCallback) onChangeCallback(isAudioPlaying(audio));
            });
            audio.addEventListener('pause', () => {
                if (onChangeCallback) onChangeCallback(isAudioPlaying(audio));
            });
            // audio.addEventListener('ended', () => {
            //     if (onChangeCallback) onChangeCallback(isAudioPlaying(audio));
            // });
        }
        return audio
    }

    return {
        play: () => {
            audio = loadAudio();
            audio.play()
                .then(() => {
                    console.log("Audio is playing...");
                })
                .catch((error) => {
                    console.error("Error playing audio:", error);
                });
        },
        change: setChangeCallback,
        pause: () => {
            if (audio) audio.pause();
        },
        stop: () => {
            if (audio) {
                audio.pause();
                audio.currentTime = 0;
            }
        },
        toggle: () => {
            audio = loadAudio();
            if (!isAudioPlaying(audio)) {
                audio.play();
            } else {
                audio.pause();
                audio.currentTime = 0;
            }
        },
        audio,
        loadAudio,
    };
}

var mutedAllAudios = false,
    soundsPlayed = false
function toggleMuteAudios(self) {
    const btn = $(self)

    if (!mutedAllAudios) {
        mutedAllAudios = true
        soundsPlayed = false
        if (currentlyPlayingAudio) {
            currentlyPlayingAudio.pause();
            currentlyPlayingAudio.currentTime = 0;
            currentlyPlayingAudio = null
        }
        btn.removeClass("tooltip-btn-success")
        btn.addClass("tooltip-btn-danger")
        btn.html(`
            <i class="fa fa-volume-xmark"></i>
            <span>صدا دار کردن</span>
        `)
    } else {
        btn.removeClass("tooltip-btn-danger")
        btn.addClass("tooltip-btn-success")
        soundsPlayed = true
        mutedAllAudios = false
        btn.html(`
            <i class="fa fa-volume-up"></i>
            <span>بی صدا کردن</span>
        `)
    }
}

let lastFocusedElementId,
    currentlyPlayingAudio = null,
    isQueueProcessing = false,
    isFirstPlayingOfStep = true;
const audioQueue = [];
const audioPlayerStepFields = {}
function audioPlayerField(id, url, step = 0) {
    const btn = $(`#sound_${id}`);
    if (!url?.length) {
        btn.hide();
        $(`#sound_mute_${id}`).hide();
        return {
            run: () => {}
        };
    }

    if (mutedAllAudios) {
        $(`#sound_mute_${id}`).removeClass("tooltip-btn-success")
            .addClass("tooltip-btn-danger")
            .html(`
                <i class="fa fa-volume-xmark"></i>
                <span>صدا دار کردن</span>
            `);
    } else {
        $(`#sound_mute_${id}`).removeClass("tooltip-btn-danger")
            .addClass("tooltip-btn-success")
            .html(`
                <i class="fa fa-volume-up"></i>
                <span>بی صدا کردن</span>
            `);
    }

    if (!audioPlayerStepFields[step]) audioPlayerStepFields[step] = [];
    audioPlayerStepFields[step].push(id);

    let { play, change, stop, toggle, audio, loadAudio } = audioPlayer(url);
    let resetAudioCtx = () => {};

    btn.on("click", () => {
        if (mutedAllAudios) {
            snackbar("audio_snackbar_39843", "لطفا حالت صدا دار کردن را فعال کرده ، تا امکان پخش صدا فراهم گردد!", "warning", { hasIcon: true });
            return;
        }
        toggle();
        lastFocusedElementId = id;
    });

    change((isPlaying) => {
        audio = loadAudio();
        if (isPlaying) {
            if (currentlyPlayingAudio && currentlyPlayingAudio !== audio) {
                currentlyPlayingAudio.pause();
                currentlyPlayingAudio.currentTime = 0;
            }
            currentlyPlayingAudio = audio;
            const { reset } = handleAudioContext(audio);
            resetAudioCtx = reset;
            btn.html(`
                <i class="fa fa-pause"></i>
                <span>متوقف صدا</span>
            `);
        } else {
            resetAudioCtx();
            btn.html(`
                <i class="fa fa-volume"></i>
                <span>پخش صدا</span>
            `);
            processQueue();
            if (currentlyPlayingAudio === audio) {
                currentlyPlayingAudio = null;
            }
        }
    });

    document.addEventListener("focusin", (event) => {
        if (event.target.tagName == 'CANVAS' || event.target.id || event.target.getAttribute("class") || event.target.parentElement.getAttribute("class") || event.target.getAttribute("for")) {
            if (
                (
                    event.target.getAttribute("for")?.split('_').includes(`${id}`) ||
                    event.target.id?.split('_').includes(`${id}`) ||
                    event.target.getAttribute("for") == id ||
                    event.target.getAttribute("class")?.split('_').includes(`${id}`) ||
                    event.target.getAttribute("name")?.split('_').includes(`${id}`) ||
                    event.target.parentElement.getAttribute("class")?.split('_').includes(`${id}`) ||
                    event.target.parentElement.id?.split('_').includes(`${id}`) ||
                    event.target.parentElement.getAttribute("for")?.split('_').includes(`${id}`) ||
                    event.target.id == id
                ) &&
                event.target.id != `sound_${id}` &&
                event.target.id != `sound_mute_${id}`
            ) {
                if (lastFocusedElementId != id) {
                    // if (mutedAllAudios) {
                    //     snackbar("audio_snackbar_39843", "لطفا حالت صدا دار کردن را فعال کرده ، تا امکان پخش صدا فراهم گردد!", "warning", { hasIcon: true });
                    //     return;
                    // }
                    if (soundsPlayed && !isFirstPlayingOfStep) {
                        play();
                    } else {
                        if (!audio) audio = loadAudio();
                        addToQueue(audio);
                    }
                }
                lastFocusedElementId = id;
            }
        }
    });

    let audioContext;
    let mediaSource;
    let analyser;

    function handleAudioContext(audio) {
        const playButton = document.getElementById(`sound_${id}`);

        if (!audioContext) {
            audioContext = new (window.AudioContext)();
        }
        if (!mediaSource) {
            try {
                mediaSource = audioContext.createMediaElementSource(audio);
            } catch (error) {
                console.error("MediaSource error:", error.message);
                return;
            }
        }

        if (!analyser) {
            analyser = audioContext.createAnalyser();
            mediaSource.connect(analyser);
            analyser.connect(audioContext.destination);
            analyser.fftSize = 256;
        }

        visualize(analyser, audio, playButton);

        return {
            reset: () => {
                playButton.style.boxShadow = null;
                audioContext.resume();
            },
            stop: () => {
                if (mediaSource) {
                    try {
                        mediaSource.disconnect();
                    } catch (error) {
                        console.warn("Error disconnecting mediaSource:", error);
                    }
                    mediaSource = null;
                }
                if (audioContext) {
                    try {
                        audioContext.close();
                    } catch (error) {
                        console.warn("Error closing audioContext:", error);
                    }
                    audioContext = null;
                }
            }
        };
    }

    return {
        play,
        change,
        stop,
        toggle,
        audio,
        run: () => {
            audio = loadAudio();
            audioQueue.unshift(audio);
            if (mutedAllAudios) {
                $(`#sound_mute_${id}`).removeClass("tooltip-btn-success")
                    .addClass("tooltip-btn-danger")
                    .html(`
                        <i class="fa fa-volume-xmark"></i>
                        <span>صدا دار کردن</span>
                    `);
                audioQueue.shift();
                return;
            } else {
                $(`#sound_mute_${id}`).removeClass("tooltip-btn-danger")
                    .addClass("tooltip-btn-success")
                    .html(`
                        <i class="fa fa-volume-up"></i>
                        <span>بی صدا کردن</span>
                    `);
            }
            processQueue();
        }
    };
}

function addToQueue(audio) {
    audioQueue.push(audio);
    isQueueProcessing = false;
    // processQueue();
}

async function processQueue() {
    await new Promise((resolve) => {
        var interval = setInterval(() => {
            // clearInterval(interval);
            if (soundsPlayed) resolve();
        }, 50);
    });

    if (isQueueProcessing || audioQueue.length === 0) return;

    isQueueProcessing = true;
    const nextAudio = audioQueue.shift();
    if (mutedAllAudios) return;

    const playNextAudio = () => {
        if (!nextAudio) return;
        nextAudio.play().then(() => {
            nextAudio.addEventListener("pause", () => {
                isFirstPlayingOfStep = false;
                isQueueProcessing = false;
                processQueue();
            });
            nextAudio.addEventListener("ended", () => {
                isFirstPlayingOfStep = false;
                isQueueProcessing = false;
                processQueue();
            });
        }).catch((error) => {
            console.error("Error playing audio:", error);
            isFirstPlayingOfStep = false;
            isQueueProcessing = false;
            processQueue();
        });
    };

    playNextAudio();
}

function checkFormHasSound() {
    for(let step in audioPlayerStepFields) if (audioPlayerStepFields[step].length > 0) return true 
    return false
}

function showLoader(loaderId) {
    var loader = document.getElementById("element_" + loaderId + "_loader");
    loader.style.display = "block";
}

function hideLoader(loaderId) {
    var loader = document.getElementById("element_" + loaderId + "_loader");
    loader.style.display = "none";
}
function singleFile(id) {
    let $droparea = $("#element_" + id + "_drop_area");
    const fileInput = document.getElementById("element_" + id + "_file");
    const filePreview = document.getElementById("element_" + id + "_preview");
    const fileName = document.getElementById("element_" + id + "_filename");
    const $fileDelete = $("#element_" + id + "_file_delete");
    const $result = $("#single_file_result_" + id);

    let files = fileInput.files;
    let filesCount = files.length;

    if (filesCount === 1) {
        showLoader(id);
        var filePath = fileInput.value;
        var extensions = fileInput.getAttribute("accept");
        var extensionsArray = extensions.split(",");
        var file_extension = filePath.split(".");
        if (!extensionsArray.includes("." + file_extension[file_extension.length - 1]?.toLowerCase())) {
            snackbar("element_6598465131", "پسوند فایل مجاز نمی باشد", type = "danger", duration = 3000);
            fileInput.value = "";
            return false;
        } else {
            $droparea.hide();
            const formData = new FormData();
            formData.append("file", files[0]);
            const processFile = new Promise((resolve, reject) => {
                setTimeout(() => {
                    resolve({ name: "user-panel-too-mutch-long-name-it-has.png", url: "../assets/images/user-panel.png" });
                }, 2000);
            });
            processFile
                .then((data) => {
                    filePreview.setAttribute("src", data.url);
                    fileName.innerText = data.name;
                    $result.show();
                    $(document).ready(function () {
                        if (window["lightGallery_listfile_"+id]) window["lightGallery_listfile_"+id].destroy();
                        singleFileGallery = lightGallery(document.getElementById(`gallery_${id}`), {
                            plugins: [lgThumbnail, lgZoom, lgFullscreen, lgShare, lgRotate, lgAutoplay],
                            download: true,
                            controls: true,
                            mobileSettings: {
                                showCloseIcon: true,
                            },
                            thumbWidth: 100,
                            thumbHeight: 100,
                            showZoomInOutIcons: true,
                            actualSize: false,
                        });
                    });
                })
                .finally(() => {
                    hideLoader(id);
                });
            // $.ajax({
            //     url  : PATHFILE+"execute/form/add/upload_file",
            //     type : "POST",
            //     data : formData,
            //     processData: false,
            //     contentType: false,
            //     success : function(data) {
            //         // $("#single_file_result_"+id).html(data);
            //         console.log(data)
            //     },
            //     complete: function() {
            //         hideLoader();
            //     }
            // });
        }
        $fileDelete.on("click", function () {
            $fileInput.val(null);
            $result.hide();
            $droparea.show();
        });
    } else if (filesCount === 0) {
    }
}

function closeAd(el) {
    el.parentElement.parentElement.remove()
}

/** Highcharts */
if (window?.Highcharts) {
    Highcharts.theme = {
        colors: ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572', '#FF9655', '#FFF263', '#6AF9C4'],
        chart: {
            backgroundColor: 'transparent',
            style: {
                direction: 'rtl'
            }
        },
        title: {
            style: {
                color: 'rgb(var(--rgb-darkest))',
                font: 'bold 16px "IRANSans"'
            }
        },
        subtitle: {
            style: {
                color: 'rgb(var(--rgb-light-dark))',
                font: 'bold 12px "IRANSans"'
            }
        },
        xAxis: {
            style: {
                color: 'rgb(var(--rgb-light-dark))',
            },
            gridLineColor: 'rgb(var(--rgb-light-dark),0.1)',
            gridLineWidth: 1,
            lineColor: 'rgb(var(--rgb-light))',
            tickColor: 'rgb(var(--rgb-light))',
            tickLength: 5,
            labels: {
                style: {
                    color: 'rgb(var(--rgb-light-dark))',
                    font: 'bold 8px "IRANSans"'
                }
            }
        },
        yAxis: {
            style: {
                color: 'rgb(var(--rgb-light-dark))',
            },
            gridLineColor: 'rgb(var(--rgb-light-dark),0.1)',
            gridLineWidth: 1,
            lineColor: 'rgb(var(--rgb-light))',
            tickColor: 'rgb(var(--rgb-light))',
            tickLength: 5,
            labels: {
                style: {
                    color: 'rgb(var(--rgb-light-dark))',
                    font: 'normal 10px "IRANSans"',
                    direction: 'ltr'
                }
            }
        },
        legend: {
            reversed: true,
            itemStyle: {
                font: '9px "IRANSans"',
                color: 'rgb(var(--rgb-light-dark))'
            },
            itemHoverStyle:{
                color: 'rgb(var(--rgb-light-dark))'
            },
            labelFormatter: function() {
                return `<div class="text-end mb-1">${this.name}</div>`
            }
        },
        tooltip: {
            backgroundColor: 'rgb(var(--rgb-ninth-lighter))',
            color: 'rgb(var(--rgb-darkest))',
            style: {
                fontSize: '10px',
                fontFamily: 'IRANSans',
                direction: 'rtl',
                color: 'rgb(var(--rgb-darkest))',
            },
            shadow: {
                color: 'rgba(var(--rgb-darkest),0.2)',
                width: 10,
                offsetX: 0,
                offsetY: 2
            },
        },
        plotOptions: {
            series: {
                dataLabels: {
                    color: 'rgb(var(--rgb-darkest))',
                    fill: 'rgb(var(--rgb-darkest))',
                    style: {
                        fontWeight: 'bold',
                        fontSize: '12px',
                        textOutline: '0px rgb(var(--rgb-darkest))'
                    }
                }
            }
        }
    };
    // Apply the theme
    Highcharts.setOptions(Highcharts.theme);
}

class ScriptLoader {
    constructor() {
        this.loadedScripts = new Set();
    }
    async loadScript(src, callback = () => {}) {
        if (document.readyState === 'loading') {
            await new Promise((resolve) => {
                document.addEventListener('DOMContentLoaded', resolve);
            });
        } else if (document.readyState != 'complete') await new Promise((resolve) => setTimeout(resolve, 200));

        if (this.loadedScripts.has(src)) {
            if (callback) callback();
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.async = true;

            script.onload = () => {
                this.loadedScripts.add(src);
                if (callback) callback();
                resolve();
            };

            script.onerror = () => {
                console.error(`Failed to load script "${src}".`);
                reject(new Error(`Failed to load script "${src}".`));
            };

            document.body.appendChild(script);
        });
    }

    async loadScriptsSequentially(scripts, callback) {
        if (document.readyState === 'loading') {
            await new Promise((resolve) => {
                document.addEventListener('DOMContentLoaded', resolve);
            });
        } else if (document.readyState != 'complete') await new Promise((resolve) => setTimeout(resolve, 200));
        let promiseChain = Promise.resolve();

        scripts.forEach(src => {
            promiseChain = promiseChain.then(() => this.loadScript(src));
        });

        if (callback) {
            promiseChain.then(callback);
        }

        return promiseChain;
    }
}
const scriptLoader = new ScriptLoader();


// Voice Recorder
function createVoiceRecorder(formElementId, options, elements_id = '') {
    const constraints = { audio: true };
    let mediaRecorder;
    let chunks = [];
    let flagRecording = false;
    let flagDelete = true;
    let offset = 0;
    let paused = true;

    const elements = {
        startBtn: $(`#start_${formElementId}`),
        hideInput: $(`#element_${formElementId}_hide`),
        seconds: $(`#s_seconds_${formElementId}`),
        minutes: $(`#s_minutes_${formElementId}`),
        btns: $(`#btns_${formElementId}`),
        voiceContainer: $(`.palyer_voice_container_${formElementId}`),
        loaderSection: $(`#loader_section_${formElementId}`),
    };

    function removePlayerContainer() {
        elements.hideInput.val("");
        elements.hideInput.trigger("input");
        elements.seconds.text("00");
        elements.minutes.text("00");
        elements.btns.removeClass("d-none");
        elements.voiceContainer.html("");
    }

    function startStopwatch() {
        if (paused) {
            paused = false;
            offset -= Date.now();
            render();
        }
    }

    function stopStopwatch() {
        if (!paused) {
            paused = true;
            offset += Date.now();
        }
    }

    function resetStopwatch() {
        if (paused) {
            offset = 0;
            render();
        } else {
            offset = -Date.now();
        }
    }

    function render() {
        const value = paused ? offset : Date.now() + offset;
        elements.seconds.text(format(value, 1000, 60, 2));
        elements.minutes.text(format(value, 60000, 60, 2));

        if (format(value, 60000, 60, 1) === "2") {
            stopStopwatch();
            mediaRecorder.stop();
            return;
        }

        if (!paused) {
            requestAnimationFrame(render);
        }
    }

    function voice_player(id, url, form_element_id)
    {
        var cs = getComputedStyle(document.querySelector("body"));
        var DEFAULTS = {
            borderColor: `rgb(${cs.getPropertyValue("--rgb-seventh-lighter")})`,
            playedColor: `rgb(${cs.getPropertyValue("--rgb-lightest")})`,
            backgroundColor: `rgb(${cs.getPropertyValue("--rgb-seventh")})`,
            iconColor: `rgb(${cs.getPropertyValue("--rgb-lightest")})`,
            borderWidth: 1,
            size: 18,
            className: "circle-audio-player cursor-pointer",
        };

        // reused values
        var pi = Math.PI;
        var doublePi = pi * 2;
        var arcOffset = -pi / 2;
        var animTime = 200;
        var loaderTime = 1800;

        var CircleAudioPlayer = function (options) {
            options = options || {};
            for (var property in DEFAULTS) {
                this[property] = options[property] || DEFAULTS[property];
            }

            // create some things we need
            this._canvas = document.createElement("canvas");
            this._canvas.setAttribute("class", this.className + " is-loading");
            this._canvas.addEventListener(
                "mousedown",
                function () {
                    if (this.playing) {
                        this.pause();
                    } else {
                        this.play();
                    }
                }.bind(this)
            );
            this._ctx = this._canvas.getContext("2d");

            // set up initial stuff
            this.setAudio(options.audio);
            this.setSize(this.size);

            // redraw loop
            (function cAPAnimationLoop(now) {
                // check if we need to update anything
                if (this.animating) {
                    this._updateAnimations(now);
                }
                if (this._forceDraw || this.playing || this.animating || this.loading) {
                    this._draw();
                    this._forceDraw = false;
                }

                requestAnimationFrame(cAPAnimationLoop.bind(this));
            }).call(this, new Date().getTime());
        };
        CircleAudioPlayer.prototype = {
            // private methods
            _animateIcon: function (to, from) {
                // define a few things the first time
                this._animationProps = {
                    animStart: null,
                    from: from,
                    to: to,
                };
                if (from) {
                    this.animating = true;
                } else {
                    this._animationProps.current = this._icons[to].slice();
                    this.draw();
                }
            },

            _updateAnimations: function (now) {
                this._animationProps.animStart = this._animationProps.animStart || now;
                var deltaTime = now - this._animationProps.animStart;
                var perc = 1 - Math.cos(((deltaTime / animTime) * pi) / 2);
                if (deltaTime >= animTime) {
                    this.animating = false;
                    perc = 1;
                    this._animationProps.current =
                        this._icons[this._animationProps.to].slice();
                    this.draw();
                } else {
                    var from = this._icons[this._animationProps.from];
                    var current = [];
                    for (var i = 0; i < from.length; i++) {
                        current.push([]);
                        for (var j = 0; j < from[i].length; j++) {
                            current[i].push([]);
                            var to = this._icons[this._animationProps.to][i][j];
                            current[i][j][0] = from[i][j][0] + (to[0] - from[i][j][0]) * perc;
                            current[i][j][1] = from[i][j][1] + (to[1] - from[i][j][1]) * perc;
                        }
                    }
                    this._animationProps.current = current;
                }
            },
            _updateTimerDisplay: function () {
                if (this.audio && this.audio.duration) {
                    var currentTime = Math.floor(this.audio.currentTime);
                    // var duration = Math.floor(this.audio.duration);
                    var form_id = id.getAttribute("id").split("_");
                    var duration =
                        $("#s_minutes_" + form_id[1]).text() * 60 +
                        $("#s_seconds_" + form_id[1]).text();
                    var remainingTime = duration >= currentTime ? duration - currentTime : currentTime - duration;
                    // Format the time as "MM:SS"
                    var minutes = Math.floor(remainingTime / 60 / 100);
                    var seconds = remainingTime % 60;
                    var formattedTime = minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
                    document.querySelector(`.player_sound_timer${form_element_id}`).textContent = formattedTime;
                }
            },
            _draw: function (progress) {
                // common settings
                var form_id = id.getAttribute("id").split("_");
                var duration =
                    $("#s_minutes_" + form_id[1]).text() * 60 +
                    $("#s_seconds_" + form_id[1]).text();
                if (isNaN(progress)) {
                    progress = this.audio.currentTime / duration || 0;
                    // progress = this.audio.currentTime / this.audio.duration || 0;
                }
                // clear existing
                this._ctx.clearRect(0, 0, this.size, this.size);

                // draw bg
                this._ctx.beginPath();
                this._ctx.arc(
                    this._halfSize,
                    this._halfSize,
                    this._halfSize - this.borderWidth / 2,
                    0,
                    doublePi
                );
                this._ctx.closePath();
                this._ctx.fillStyle = this.backgroundColor;
                this._ctx.fill();

                // draw border
                // our active path is already the full circle, so just stroke it
                this._ctx.lineWidth = this.borderWidth;
                this._ctx.strokeStyle = this.borderColor;
                this._ctx.stroke();

                // play progress
                if (progress > 0) {
                    this._ctx.beginPath();
                    this._ctx.arc(
                        this._halfSize,
                        this._halfSize,
                        this._halfSize - this.borderWidth / 2,
                        arcOffset,
                        arcOffset + doublePi * progress
                    );
                    this._ctx.strokeStyle = this.playedColor;
                    this._ctx.stroke();
                }

                // icons
                this._ctx.fillStyle = this.iconColor;
                if (this.loading) {
                    var loaderOffset =
                        -Math.cos(((new Date().getTime() % loaderTime) / loaderTime) * pi) *
                        doublePi -
                        pi / 3 -
                        pi / 2;
                    this._ctx.beginPath();
                    this._ctx.arc(
                        this._halfSize,
                        this._halfSize,
                        this._halfSize / 3,
                        loaderOffset,
                        loaderOffset + (pi / 3) * 2
                    );
                    this._ctx.strokeStyle = this.iconColor;
                    this._ctx.stroke();
                } else {
                    this._ctx.beginPath();
                    var icon =
                        (this._animationProps && this._animationProps.current) ||
                        this._icons.play;
                    for (var i = 0; i < icon.length; i++) {
                        this._ctx.moveTo(icon[i][0][0], icon[i][0][1]);

                        for (var j = 1; j < icon[i].length; j++) {
                            this._ctx.lineTo(icon[i][j][0], icon[i][j][1]);
                        }
                    }

                    // this._ctx.closePath();
                    this._ctx.fill();
                    // stroke to fill in for retina
                    this._ctx.strokeStyle = this.iconColor;
                    this._ctx.lineWidth = 2;
                    this._ctx.lineJoin = "miter";
                    this._ctx.stroke();
                    this._updateTimerDisplay();
                }
            },
            _setState: function (state) {
                this.playing = false;
                this.loading = false;
                if (state === "playing") {
                    this.playing = true;
                    this._animateIcon("pause", "play");
                } else if (state === "loading") {
                    this.loading = true;
                } else if (this.state !== "loading") {
                    this._animateIcon("play", "pause");
                } else {
                    this._animateIcon("play", null);
                }
                this.state = state;
                this._canvas.setAttribute("class", this.className + " is-" + state);
                this.draw();
            },
            // public methods
            draw: function () {
                this._forceDraw = true;
            },
            setSize: function (size) {
                this.size = size;
                this._halfSize = size / 2; // we do this a lot. it"s not heavy, but why repeat?
                this._canvas.width = size;
                this._canvas.height = size;
                // set icon paths
                var iconSize = 20;
                var pauseGap = iconSize / 10;
                var playLeft = Math.cos((pi / 3) * 2) * (iconSize / 2) + this._halfSize;
                var playRight = iconSize / 2 + this._halfSize;
                var playHalf = (playRight - playLeft) / 2 + playLeft;
                var top = this._halfSize - Math.sin((pi / 3) * 2) * (iconSize / 2);
                var bottom = this.size - top;
                var pauseLeft = this._halfSize - iconSize / 3;
                var pauseRight = this.size - pauseLeft;
                this._icons = {
                    play: [
                        [
                            [playLeft, top],
                            [playHalf, (this._halfSize - top) / 2 + top],
                            [playHalf, (this._halfSize - top) / 2 + this._halfSize],
                            [playLeft, bottom],
                        ],
                        [
                            [playHalf, (this._halfSize - top) / 2 + top],
                            [playRight, this._halfSize],
                            [playRight, this._halfSize],
                            [playHalf, (this._halfSize - top) / 2 + this._halfSize],
                        ],
                    ],
                    pause: [
                        [
                            [pauseLeft, top + pauseGap],
                            [this._halfSize - pauseGap, top + pauseGap],
                            [this._halfSize - pauseGap, bottom - pauseGap],
                            [pauseLeft, bottom - pauseGap],
                        ],
                        [
                            [this._halfSize + pauseGap, top + pauseGap],
                            [pauseRight, top + pauseGap],
                            [pauseRight, bottom - pauseGap],
                            [this._halfSize + pauseGap, bottom - pauseGap],
                        ],
                    ],
                };

                if (this._animationProps && this._animationProps.current) {
                    this._animateIcon(this._animationProps.to);
                }
                if (!this.playing) {
                    this.draw();
                }
            },
            setAudio: function (audioUrl) {
                this.audio = new Audio(audioUrl);
                this.audio.preload = "metadata"
                this._setState("loading");

                this.audio.addEventListener(
                    "canplaythrough",
                    function () {
                        this._setState("paused");
                    }.bind(this)
                );
                this.audio.addEventListener(
                    "play",
                    function () {
                        this._setState("playing");
                    }.bind(this)
                );
                this.audio.addEventListener(
                    "pause",
                    function () {
                        // reset when finished
                        if (this.audio.currentTime === this.audio.duration) {
                            this.audio.currentTime = 0;
                        }
                        this._setState("paused");
                    }.bind(this)
                );
            },
            appendTo: function (element) {
                element.appendChild(this._canvas);
            },
            play: function () {

                this.audio.play();
            },
            pause: function () {

                this.audio.pause();
            },
        };

        // now init one as an example
        var cap = new CircleAudioPlayer({
            audio: url,
            size: 60,
            borderWidth: 4,
        });
        cap.appendTo(id);

        return {audio: cap.audio}
    }

    function init() {
        elements.startBtn.on("click", function () {
            if (document.location.protocol === "http:") {
                snackbar("element_1894324", "برای فعال شدن دکمه ضبط باید مجدد صفحه بارگزاری شود ", "warning", {
                    isConfirmed: true,
                    hasIcon: true,
                    duration: null,
                    textStyles: { fontWeight: "bold" },
                    acceptText: "بله انجام شود !",
                    cancelText: "نه، منصرف شدم!"
                }).then((result) => {
                    if (result.isConfirmed) {
                        link_transfer(document.location.href.replace("http://", "https://"));
                    }
                });
                return;
            }

            if (!flagRecording) {
                navigator.mediaDevices.getUserMedia(constraints).then((stream) => {
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.start();
                    chunks = [];

                    elements.startBtn.addClass("recording");
                    $(`.voice_timer${formElementId}`).addClass("active");

                    mediaRecorder.addEventListener("dataavailable", (e) => {
                        chunks.push(e.data);
                    });

                    resetStopwatch();
                    startStopwatch();

                    mediaRecorder.addEventListener("stop", () => {
                        stream.getTracks().forEach((track) => track.stop());
                        elements.btns.addClass("d-none");
                        elements.startBtn.removeClass("recording");
                        $(`.voice_timer${formElementId}`).removeClass("active");

                        elements.loaderSection.show().html(`<svg class="spinner my-2" width="52" height="52"><circle class="circle" fill="none" stroke-width="6" stroke-linecap="round" cx="33" cy="33" r="30"></circle></svg>`);

                        const blob = new Blob(chunks, { type: "audio/ogg; codecs=opus" });
                        const formData = new FormData();
                        formData.append("file", blob);
                        formData.append("token", options.token);
                        formData.append("form_id", options.formId);
                        formData.append("id", formElementId);
                        formData.append("type", "audio/mpeg");
                        formData.append("file_old", elements.hideInput.val());
                        formData.append("show_name", "");
                        if (elements_id?.length) formData.append("elements",$(`#${elements_id}`).val());

                        $.ajax({
                            url: options.uploadUrl,
                            type: "POST",
                            data: formData,
                            processData: false,
                            contentType: false,
                            success: function (data) {
                                const soundData = JSON.parse(data);
                                elements.loaderSection.html("");
                                elements.voiceContainer.show().append(`
                                    <div class="d-flex align-items-center justify-content-center gap-2">
                                        <div class="d-flex align-items-center gap-2">
                                            <span class="fs-15 fw-500 text-light-dark text-center player_sound_timer${formElementId}"></span>
                                            <div style="height: 60px" id="playerContainer_${formElementId}"></div>
                                        </div>
                                        <button type="button" class="d-flex border-0 justify-content-center remove_playContainer_${formElementId} p-2 rounded-circle bg-danger">
                                            <i class="fa-regular fa-trash-can fs-15 text-white"></i>
                                        </button>
                                    </div>`);

                                document.querySelector(`.remove_playContainer_${formElementId}`).addEventListener("click", removePlayerContainer);
                                const playerContainer = document.getElementById(`playerContainer_${formElementId}`);
                                elements.hideInput.val(soundData.name);
                                elements.hideInput.trigger("input");
                                voice_player(playerContainer, soundData.url, formElementId);
                            }
                        });
                    });

                    flagRecording = true;
                    flagDelete = true;
                }).catch((e) => console.log(e));
            } else {
                stopStopwatch();
                mediaRecorder.stop();
                flagRecording = false;
            }
        });
    }

    init();

    return {
        removePlayerContainer,
        elements,
        voice_player
    }
}

function handleResetFormWithTokenInput(event) {
    setTimeout(() => {
        $(event.target).find("input").each(function() {
            if ($(this).data("tokenInputObject")) $(this).tokenInput("clear");
        });
    },10);
}

function addGeojsonLayer(var_name, map, options = {}) {
    var cs = getComputedStyle(document.querySelector("body"));
    L.vectorGrid
        .slicer(var_name, {
            maxZoom: 22,
            minNativeZoom: 0,
            rendererFactory: L.canvas.tile,
            vectorTileLayerStyles: {
                sliced: function (properties, zoom) {
                    return {
                        color: `rgb(${cs.getPropertyValue("--rgb-first")})`,
                        fillColor: `rgb(${cs.getPropertyValue("--rgb-first")})`,
                        weight: 3,
                        opacity: 1,
                        fillOpacity: 0.4,
                        fill: true,
                    };
                },
            },
            interactive: false,
            preferCanvas: false
        }).addTo(map).bringToFront();

    map.on("dragend", function() {
        L.geoJSON(var_name).eachLayer(async function (layer) {
            const polygon = extractLatLngs(layer.feature.geometry.coordinates)
            var lat = map.getCenter().lat;
            var lng = map.getCenter().lng;
            const point = [parseFloat(lat), parseFloat(lng)];
            const result = pointInPolygon(point, polygon);
            if (result) {
                var dataPlaced = false;
                if (options.geo_data_1_field?.length && options.geo_data_1?.length)
                    [$(`#${options.geo_data_1_field}`).val(layer.feature.properties[options.geo_data_1]), $(`#${options.geo_data_1_field}`).trigger("input"), dataPlaced = true];
                if (options.geo_data_2_field?.length && options.geo_data_2?.length)
                    [$(`#${options.geo_data_2_field}`).val(layer.feature.properties[options.geo_data_2]), $(`#${options.geo_data_2_field}`).trigger("input"), dataPlaced = true];
                if (options.geo_data_3_field?.length && options.geo_data_3?.length)
                    [$(`#${options.geo_data_3_field}`).val(layer.feature.properties[options.geo_data_3]), $(`#${options.geo_data_3_field}`).trigger("input"), dataPlaced = true];
                if (dataPlaced) {snackbar("element_geo_84394", "داده ای از این لایه دریافت شده و در فیلد مورد نظر قرار گرفت!", "success", {hasIcon: true})}
            }
        })
    })
}

async function imageUrlToBase64(url) {
    const response = await fetch(url);
    const blob = await response.blob();

    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

function htmlToCanvas(divId = 'image-content') {
    const el = document.getElementById(divId);
    if (!el) {
        snackbar("element_84394", "هیچ محتوایی برای ذخیره سازی، یافت نشد.", "warning", {hasIcon: true})
        return;
    }
    captureDesktopRatioScreenshot(el,{
        targetWidth: 1920,
        useCORS: true, // tells html2canvas to attempt using CORS
        logging: true,  // enable logging for debugging
    }).then(function (canvas) {
        const now = new Date();
        const formatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {year: 'numeric', month: '2-digit', day: '2-digit'});
        const datePart = formatter.format(now);
        const timePart = now.toLocaleTimeString('fa-IR', {hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'});
        const dateTime = datePart.replace(/\//g, '-') + ' ' + timePart;

        var anchorTag = document.createElement("a");
        document.body.appendChild(anchorTag);
        anchorTag.download = dateTime;
        anchorTag.href = canvas.toDataURL();
        anchorTag.target = "_blank";
        anchorTag.click();
    });
}

async function captureDesktopRatioScreenshot(element, options = {}) {
    const defaultOptions = {
        targetWidth: 1600,
        scale: window.devicePixelRatio || 1
    };

    const config = {...defaultOptions, ...options};
    const iframe = document.createElement('iframe');
    let canvas = null;

    try {
        // Setup iframe
        iframe.style.cssText = `
            position: fixed;
            left: -9999px;
            top: -9999px;
            width: ${config.targetWidth}px;
            border: none;
            visibility: hidden;
        `;
        document.body.appendChild(iframe);
        snackbar("element_84394", "در حال تلاش برای ذخیره سازی تصویر...", "success", {hasIcon: true});
        // Wait for iframe to load
        const doc = await new Promise(resolve => {
            iframe.onload = () => {
                const doc = iframe.contentDocument || iframe.contentWindow.document;
                resolve(doc);
            };
            iframe.src = 'about:blank';
        });

        doc.body.classList.add(...document.body.classList.value.split(" ").filter(c => !c.includes('content') && !c.includes('body')))

        // Set iframe document
        const meta = doc.createElement('meta');
        meta.name = "viewport";
        meta.content = `width=${config.targetWidth}, initial-scale=1.0`;
        doc.head.appendChild(meta);
        const clone = element.cloneNode(true);
        doc.body.appendChild(clone);
        clone.setAttribute("dir", "rtl");

        // Clone styles
        Array.from(document.head.querySelectorAll('style, link[rel="stylesheet"]')).forEach(style => {
            doc.head.appendChild(style.cloneNode(true));
        });

        // Clone and append element
        clone.style.width = `${config.targetWidth}px`;
        clone.style.height = 'auto';
        clone.style.overflow = 'visible';

        // Create canvas
        canvas = document.createElement('canvas');
        canvas.width = config.targetWidth * config.scale;

        // First pass to measure height
        const tempCanvas = await html2canvas(clone, {
            scale: config.scale,
            width: config.targetWidth,
            logging: false,
            useCORS: true
        });

        canvas.height = tempCanvas.height;

        // Final capture
        await html2canvas(clone, {
            canvas: canvas,
            scale: config.scale,
            width: config.targetWidth,
            height: tempCanvas.height / config.scale,
            logging: false,
            useCORS: true
        });
        snackbar("element_84394", "تصویر با موفقیت ذخیره شد.", "success", {hasIcon: true,forceGenerate: true});
        return canvas;
    } finally {
        if (iframe && iframe.parentNode) {
            iframe.parentNode.removeChild(iframe);
        }
    }
}
/*
async function captureDesktopRatioScreenshot(element, options = {}) {
    const defaultOptions = {
        targetWidth: 1600,
        scale: window.devicePixelRatio || 1,
        originalStyles: {}
    };

    // Create clone and container
    const clone = element.cloneNode(true);
    const tempContainer = document.createElement('div');

    // Style the container
    tempContainer.style.cssText = `
        position: fixed;
        pointer-events: none;
        left: 0;
        top: 0;
        width: ${options.targetWidth || 1600}px;
        height: auto;
        z-index: -9999;
        overflow: visible;
    `;

    // Create a proper HTML document structure
    const doc = document.implementation.createHTMLDocument("Capture");
    const meta = doc.createElement('meta');
    meta.name = "viewport";
    meta.content = `width=${options.targetWidth || 1600}, initial-scale=1.0`;
    doc.head.appendChild(meta);

    // Clone styles from original document
    Array.from(document.head.querySelectorAll('style, link[rel="stylesheet"]')).forEach(style => {
        doc.head.appendChild(style.cloneNode(true));
    });

    // Append the cloned element
    doc.body.appendChild(clone);
    tempContainer.appendChild(doc.documentElement);
    document.body.appendChild(tempContainer);

    const config = {...defaultOptions, ...options};

    // Set clone dimensions
    clone.style.width = `${config.targetWidth}px`;
    clone.style.height = 'auto';
    clone.style.transformOrigin = '0 0';
    clone.style.overflow = 'visible';

    // Create canvas
    const canvas = document.createElement('canvas');
    canvas.width = config.targetWidth * config.scale;

    try {
        // First pass to measure height
        const tempCanvas = await html2canvas(clone, {
            scale: config.scale,
            width: config.targetWidth,
            logging: false,
            useCORS: true,
            allowTaint: true,
            scrollX: 0,
            scrollY: 0,
            windowWidth: config.targetWidth
        });

        canvas.height = tempCanvas.height;

        // Show loading message


        // Final capture
        await new Promise((resolve) => setTimeout(resolve, 1000));

        await html2canvas(clone, {
            canvas: canvas,
            scale: config.scale,
            width: config.targetWidth,
            height: tempCanvas.height / config.scale,
            logging: false,
            useCORS: true,
            allowTaint: true,
            scrollX: 0,
            scrollY: 0,
            windowWidth: config.targetWidth
        });

        snackbar("element_84394", "تصویر با موفقیت ذخیره شد.", "success", {hasIcon: true});
        return canvas;
    } catch (error) {
        console.error('Capture error:', error);
        throw error;
    } finally {
        // Clean up
        document.body.removeChild(tempContainer);
    }
}
*/
function highchartInit(id, options = {}) {
    Highcharts.chart(id, options);
}

const jsonFormatter = (id) => {
    const inputValue = $(`#${id}`).val();
    try {
        const parsedValue = JSON.parse(inputValue);
        if (typeof parsedValue !== "string") {
            $(`#${id}`).val(JSON.stringify(parsedValue, null, 4));
            return;
        }
        const formattedValue = JSON.stringify(parsedValue, null, 4);
        $(`#${id}`).val(JSON.parse(formattedValue));
    } catch (e) {
        $(`#${id}`).val("خروجی نامعتبر است");
    }
};

// Highcharts Start
// 1- column chart
function transformColumnChart(rawData, xField, seriesField, valueFields, groupColors) {
    const categories = [...new Set(rawData.map(d => d[xField]))];
    const catIndex = Object.fromEntries(categories.map((cat, i) => [cat, i]));
    const seriesMap = {};
    const fields = Array.isArray(valueFields) ? valueFields : [valueFields];

    fields.forEach(valueField => {
        rawData.forEach(row => {
            const sKey = row[seriesField];
            if (!seriesMap[sKey]) {
                seriesMap[sKey] = new Array(categories.length).fill(null);
            }
            seriesMap[sKey][catIndex[row[xField]]] = {
                name: row[xField],
                y: row[valueField],
                ...addClickEventForChartLink(row)
            };
        });
    });

    const series = Object.entries(seriesMap).map(([name, data], index) => ({ name, data, color: groupColors[index] }));

    return {
        categories,
        series
    };
}

function addClickEventForChartLink(row) {
    return {
        events: {
            click: function() {
                if (row['onclick.link']?.length) link_transfer(row['onclick.link']);
            }
        }
    };
}

// 2- Pie Chart
function transformPieChart(rawData, labelField, valueFields, groupColors) {
    const fields = Array.isArray(valueFields) ? valueFields : [valueFields];
    const defaultColors = ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572', '#FF9655', '#FFF263', '#6AF9C4'];
    const series = fields.map((valueField,index) => {
        const aggregated = {};
        rawData.forEach(row => {
            const label = row[labelField];
            const value = row[valueField] ?? 0;
            aggregated[label] = (aggregated[label] || 0) + value;
        });

        const getColor = (dataIndex) => {
            if (groupColors && groupColors[dataIndex]) return groupColors[dataIndex];
            return defaultColors[dataIndex % defaultColors.length - groupColors.length];
        };

        const data = Object.entries(aggregated).map(([name, y],index) => ({
            name,
            y,
            color: getColor(index),
            ...addClickEventForChartLink(rawData.find(row => row[labelField] === name))
        }));

        return { name: valueField, data };
    });

    return { series };
}

// 3- Variable Pie Chart
function transformVariablePieChart(rawData, labelField, yField, zField, groupColors = []) {
    const data = rawData.map(row => ({
        name: row[labelField],
        y: row[yField],
        z: row[zField],
        ...addClickEventForChartLink(row)
    }));

    return { series: [{ name: "Data", data, color: groupColors[0] }] };
}

// 4- Scatter Chart
function transformScatterChart(rawData, xField, yField, groupField = null, groupColors = []) {
    if (groupField) {
        const grouped = {};
        rawData.forEach(row => {
            const group = row[groupField];
            if (!grouped[group]) grouped[group] = [];
            grouped[group].push({
                x: row[xField],
                y: row[yField],
                ...addClickEventForChartLink(row)
            });
        });

        return { series: Object.entries(grouped).map(([name, data],index) => ({ name, data, color: groupColors[index] })) };
    } else {
        return {
            series: [{
                name: "Points",
                data: rawData.map(row => ({
                    x: row[xField],
                    y: row[yField],
                    ...addClickEventForChartLink(row)
                }))
            }]
        };
    }
}

// 5- Bubble Chart
function transformBubbleChart(rawData, xField, yField, zField, groupField = null, groupColors = []) {
    if (groupField) {
        const grouped = {};
        rawData.forEach(row => {
            const group = row[groupField];
            if (!grouped[group]) grouped[group] = [];
            grouped[group].push({
                x: row[xField],
                y: row[yField],
                z: row[zField] || 0,
                ...addClickEventForChartLink(row)
            });
        });

        return { series: Object.entries(grouped).map(([name, data],index) => ({ name, data, color: groupColors[index] })) };
    } else {
        return {
            series: [{
                color: groupColors[0],
                name: "Bubbles",
                data: rawData.map(row => ({
                    x: row[xField],
                    y: row[yField],
                    z: row[zField] || 0,
                    ...addClickEventForChartLink(row)
                }))
            }]
        };
    }
}

// 6- Line Chart Transformer
function transformLineChart(rawData, xField, yField, seriesField = null, valueFields = null, groupColors = []) {
    // Case 1: Time-series format (xField is numeric/date, seriesField groups data)
    if (valueFields?.length) {
        const categories = xField?.length ? [...new Set(rawData.map(d => d[xField]))] : null;
        const seriesMap = {};
        const fields = Array.isArray(valueFields) ? valueFields : [yField];
        
        fields.forEach(field => {
            rawData.forEach(row => {
                const seriesName = row[seriesField];
                if (!seriesMap[seriesName]) {
                    seriesMap[seriesName] = [];
                }
                seriesMap[seriesName].push({
                    x: row[xField], // Can be timestamp, date, or numeric
                    y: row[field],
                    ...addClickEventForChartLink(row)
                });
            });
        });

        return {
            categories,
            series: Object.entries(seriesMap).map(([name, data],index) => ({
                name,
                data: data.map(d => d.y),
                color: groupColors[index]
                // data: data.sort((a, b) => a.x - b.x) // Ensure chronological order
            }))
        };
    } else if (seriesField?.length) {
        const categories = xField?.length ? [...new Set(rawData.map(d => d[xField]))] : null;
        const seriesMap = {};
        const seriesName = row[seriesField];
        if (!seriesMap[seriesName]) {
            seriesMap[seriesName] = [];
        }
        seriesMap[seriesName].push({
            x: row[xField], // Can be timestamp, date, or numeric
            y: row[yField],
            ...addClickEventForChartLink(row)
        });

        return {
            categories,
            series: Object.entries(seriesMap).map(([name, data],index) => ({
                name,
                data: data.map(d => d.y),
                color: groupColors[index]
            }))
        };
    }
    // Case 2: Category-based format (xField is categorical)
    else {
        const categories = xField?.length ? [...new Set(rawData.map(d => d[xField]))] : null;
        const seriesMap = {};
        
        rawData.forEach(row => {
            const category = row[xField];
            Object.entries(row).forEach(([key, value]) => {
                if (key !== xField && typeof value === 'number') {
                    if (!seriesMap[key]) {
                        seriesMap[key] = new Array(categories.length).fill(null);
                    }
                    const index = categories.indexOf(category);
                    seriesMap[key][index] = {
                        y: value,
                        ...addClickEventForChartLink(row)
                    };
                }
            });
        });

        return {
            categories,
            series: Object.entries(seriesMap).map(([name, data],index) => ({ name, data, color: groupColors[index] }))
        };
    }
}

// 7- Area Chart Transformer
function transformAreaChart(rawData, xField, yField, seriesField = null, valueFields = null, stacking = null, groupColors = []) {
    // Case 1: Time-series format (xField is numeric/date, seriesField groups data)
    if (seriesField) {
        const seriesMap = {};
        const fields = Array.isArray(valueFields) ? valueFields : [yField];
        
        fields.forEach(field => {
            rawData.forEach(row => {
                const seriesName = row[seriesField];
                if (!seriesMap[seriesName]) {
                    seriesMap[seriesName] = [];
                }
                seriesMap[seriesName].push({
                    x: row[xField], // Can be timestamp, date, or numeric
                    y: row[field],
                    ...addClickEventForChartLink(row)
                });
            });
        });

        return {
            series: Object.entries(seriesMap).map(([name, data],index) => ({
                name,
                data: data.sort((a, b) => a.x - b.x), // Ensure chronological order
                color: groupColors[index],
                stacking: stacking // 'percent' or 'normal' if stacking needed
            }))
        };
    }
    // Case 2: Category-based format (xField is categorical)
    else {
        const categories = [...new Set(rawData.map(d => d[xField]))];
        const seriesMap = {};
        
        rawData.forEach(row => {
            const category = row[xField];
            Object.entries(row).forEach(([key, value]) => {
                if (key !== xField && typeof value === 'number') {
                    if (!seriesMap[key]) {
                        seriesMap[key] = new Array(categories.length).fill(null);
                    }
                    const index = categories.indexOf(category);
                    seriesMap[key][index] = {
                        y: value,
                        ...addClickEventForChartLink(row)
                    };
                }
            });
        });

        return {
            categories,
            series: Object.entries(seriesMap).map(([name, data]) => ({ 
                name, 
                data,
                stacking: stacking || 'normal' // 'percent' or 'normal' if stacking needed
            }))
        };
    }
}

function transformBubbleChart(rawData, xField, yField, zField, groupField = null, groupColors = []) {
    // Always return a single series with colorByPoint
    return {
        series: [{
            color: groupColors[0],
            colorByPoint: true,
            data: rawData.map(row => ({
                x: parseFloat(row[xField]),
                y: parseFloat(row[yField]),
                z: parseFloat(row[zField]) || 10,
                name: row.name || row[xField].toString(),
                ...addClickEventForChartLink(row)
            }))
        }]
    };
}

const baseHighchartsOptions = {
    chart: {
        spacingBottom: 0,
        spacingTop: 0,
        spacingLeft: 0,
        spacingRight: 0,
        marginTop: 36,
        marginBottom: 60,
        marginLeft: 60,
        marginRight: 12
    },
    title: {
        text: "",
        align: "right"
    },
    subtitle: {
        text: "",
        align: "right"
    },
    legend: {
        reversed: true,
        height: 10,
        rtl: true,
        align: "center",
        style: {
            direction: "rtl"
        },
        layout: "horizontal",
        verticalAlign: "top",
        floating: false
    },
    credits: {
        enabled: false
    },
    tooltip: {
        useHTML: true,
        formatter: function () {
            return `
            <div class="d-flex flex-column rtl">
                <div class="d-flex gap-1">
                <span>${this.series.name}:</span>
                <span class="fw-bold">${parseInt(this.y) ? Highcharts.numberFormat(this.y, -1, null, ",") : this.y}</span>
                </div>
            </div>
            `;
        }
    }
};

const chartTypeDefaults = {
    column: {
        plotOptions: {
            stacking: 'normal',
            column: {
                pointPadding: 0.1,
                borderWidth: 0,
                pointPlacement: 'on', 
                grouping: false,
            }
        }
    },
    pie: {
        plotOptions: {
            stacking: 'normal',
            pie: {
                allowPointSelect: true,
                cursor: "pointer",
                dataLabels: {
                    enabled: true,
                    format: "<b>{point.name}</b>: {point.percentage:.1f} %"
                }
            }
        }
    },
    scatter: {
        plotOptions: {
            stacking: 'normal',
            scatter: {
                marker: {
                    radius: 5,
                    states: {
                        hover: {
                            enabled: true,
                            lineColor: "rgb(100,100,100)"
                        }
                    }
                }
            }
        }
    },
    bubble: {
        plotOptions: {
            stacking: 'normal',
            bubble: {
                minSize: 3,
                maxSize: 30
            }
        }
    },
    variablepie: {
        plotOptions: {
            stacking: 'normal',
            variablepie: {
                minPointSize: 10,
                innerSize: "20%",
                zMin: 0
            }
        }
    }
};



function buildChartOptions(rawData, adminConfig, transformedSeries, categories) {
    const {
        title,
        subtitle,
        chartType,
        xAxisTitle,
        yAxisTitle,
        rtl = true,
        showLegend = true,
        tooltipTemplate = "default"
    } = adminConfig;

    const typeDefaults = chartTypeDefaults[chartType] || {};
    // Optional: Custom tooltip formatter based on template
    const tooltip = tooltipTemplate === "default"
        ? baseHighchartsOptions.tooltip
        : { /* other styles */ };

    return {
        ...baseHighchartsOptions,
        ...typeDefaults,
        chart: {
            ...baseHighchartsOptions.chart,
            type: chartType
        },
        title: {
            ...baseHighchartsOptions.title,
            text: title
        },
        subtitle: {
            ...baseHighchartsOptions.subtitle,
            text: subtitle
        },
        legend: {
            ...baseHighchartsOptions.legend,
            enabled: showLegend
        },
        xAxis: {
            title: { text: xAxisTitle },
            labels: {
                height: 10,
                style: { lineHeight: "10px", fontWeight: "bold" }
            },
            categories,
            crosshair: true,
            accessibility: {
                description: "مقادیر محور افقی"
            }
        },
        yAxis: {
            min: 0,
            title: { text: yAxisTitle },
            labels: {
                style: {
                    direction: rtl ? "rtl" : "ltr"
                }
            }
        },
        tooltip,
        series: transformedSeries,
        credits: { enabled: false }
    };
}

function transformChart(rawData, config) {
    const { chartType, seriesField, groupByField, valueField, groupColors } = config;
    var xField = groupByField;
    var yField = seriesField;
    var zField = valueField[0];
    switch (chartType) {
        case "column":
        case "bar":
            return transformColumnChart(rawData, xField, yField, valueField, groupColors);
        case "line":
            return transformLineChart(rawData, xField, yField, seriesField, valueField, groupColors);
        case "pie":
            return transformPieChart(rawData, xField, valueField, groupColors);
        case "variablepie":
            return transformVariablePieChart(rawData, xField, yField, zField, groupColors);
        case "scatter":
            return transformScatterChart(rawData, xField, yField, seriesField, groupColors);
        case "bubble":
            return transformBubbleChart(rawData, xField, yField, zField, seriesField, groupColors);
        case "area":
            return transformAreaChart(rawData, xField, yField, seriesField, valueField, config?.stacking, groupColors); // Add stacking option to admin config
        default:
            throw new Error(`Unsupported chart type: ${chartType}`);
    }
}
// Highcharts End

// Bridge from JQuery Ui Datepicker to Kendo Datepicker ap
(function($) {
    // Store original jQuery UI datepicker method
    var originalDatepicker = $.fn.datepicker;
    
    // Track connected datepickers
    var connectedPickers = {};
    
    // Override jQuery UI datepicker with Kendo UI implementation
    $.fn.datepicker = function(options, ...otherOptions) {
        // If no options provided, just initialize with defaults
        if (typeof options === 'undefined') {
            return this.each(function() {
                $(this).kendoDatePicker();
            });
        }

        // If options is a string, it's a method call
        if (typeof options === 'string') {
            var method = options;
            var args = Array.prototype.slice.call(arguments, 1);
            
            var widget = $(this).data('kendoDatePicker') || $(this).data('kendoDatePickerShamsi') || $(this).data('kendoDatePickerHijri');
            if (widget && typeof widget[method] === 'function') {
                // Map jQuery UI methods to Kendo UI methods
                switch(method) {
                    case 'destroy':
                        widget.destroy();
                        $(this).removeData('kendoDatePicker');
                        $(this).removeData('kendoDatePickerShamsi');
                        $(this).removeData('kendoDatePickerHijri');
                        delete connectedPickers[this.id];
                    break;
                    case 'option':
                        if (args.length === 1 && typeof args[0] === 'string') {
                            // Get option
                            if (args[0] === 'minDate') {
                                return widget.options.min;
                            }
                            if (args[0] === 'maxDate') {
                                return widget.options.max;
                            }
                            return widget.options[args[0]];
                        } else if (args.length === 2 || (args.length === 1 && typeof args[0] === 'object')) {
                            // Set option(s)
                            var newOptions = args.length === 1 ? args[0] : { [args[0]]: args[1] };

                            // Special handling for min/max dates
                            if (args[0] === 'minDate' || (args.length === 1 && args[0].minDate)) {
                                var minDate = args.length === 1 ? args[0].minDate : args[1];
                                if (minDate instanceof Date) {
                                    // Normalize the date to avoid timezone issues
                                    newOptions.min = new Date(minDate.getFullYear(), minDate.getMonth(), minDate.getDate());
                                }
                            }

                            if (args[0] === 'maxDate' || (args.length === 1 && args[0].maxDate)) {
                                var maxDate = args.length === 1 ? args[0].maxDate : args[1];
                                if (maxDate instanceof Date) {
                                    // Normalize the date to avoid timezone issues
                                    newOptions.max = new Date(maxDate.getFullYear(), maxDate.getMonth(), maxDate.getDate());
                                }
                            }

                            widget.setOptions(newOptions);

                            // Handle minDate/maxDate updates for connected pickers
                            if (args[0] === 'minDate' || args[0] === 'maxDate' ||
                                (args.length === 1 && (args[0].minDate || args[0].maxDate))) {
                                updateConnectedPickers(this);
                            }
                        }
                        break;
                    case 'dialog':
                        widget.open();
                        break;
                    case 'setDate':
                        widget.value(args[0]);
                        widget.trigger('change');
                        break;
                    case 'hide':
                        widget.close();
                        break;
                    case 'show':
                        widget.open();
                        break;
                    case 'isDisabled':
                        return !widget.enable();
                    case 'disable':
                        widget.enable(false);
                        break;
                    case 'enable':
                        widget.enable(true);
                        break;
                    case 'refresh':
                        widget.destroy();
                        $(this).kendoDatePicker(widget.options);
                        break;
                    case 'getDate':
                        return widget.value() || null;
                    case 'setDate':
                        var date = args[0];
                        if (date === null || date === '') {
                            widget.value(null);
                        } else if (date instanceof Date) {
                            widget.value(date);
                        } else if (typeof date === 'string') {
                            widget.value(new Date(date));
                        }
                        widget.trigger('change');
                        break;
                    default:
                        if (typeof widget[method] === 'function') {
                            return widget[method].apply(widget, args);
                        }
                }
            } else {
                var key = otherOptions[0] ?? options,
                    value = otherOptions[1];
                switch(key) {
                    case 'minDate': 
                        if (typeof value?.getDate == 'function') {
                            widget.setOptions({ min: value });
                        }
                        break;
                    case 'maxDate': 
                        if (typeof value?.getDate == 'function') {
                            widget.setOptions({ max: value });
                        }
                        break;
                    case 'getDate':
                        return widget.value() || null;
                }
            }
       
            var returnValue = this;
            
            this.each(function() {
                var widget = $(this).data('kendoDatePicker') || $(this).data('kendoDatePickerShamsi') || $(this).data('kendoDatePickerHijri');
                if (widget) {
                    if (method === 'isDisabled') {
                        returnValue = !widget.enable();
                    }
                }
            });

            return returnValue;
        }

        

        function normalizeDate(date, culture) {
            if (!(date instanceof Date)) return date;
            if (culture == 'fa-IR') {
                if (!(date instanceof JalaliDate)) {
                    var newDate = new JalaliDate();
                    newDate.setUTCFullYear(date.getFullYear(), date.getMonth(), date.getDate())
                    newDate.setJalali()
                    newDate.setDate(newDate.getDate() - 1)
                    return newDate;
                }
                return date;
            } else if (culture == 'ar-SA') {
                if (!(date instanceof HijriDate)) {
                    var newDate = new HijriDate();
                    newDate.setUTCFullYear(date.getFullYear(), date.getMonth(), date.getDate())
                    newDate.setHijri()
                    newDate.setDate(newDate.getDate() - 1)
                    return newDate;
                }
                return date;
            } else {
                return new Date(date.getFullYear(), date.getMonth(), date.getDate());
            }
        }
        
        // Map jQuery UI options to Kendo UI options
        var kendoOptions = {};
        if (options) {
            // Direct mappings
            var optionMap = {
                'culture': 'culture',
                'altField': 'altField',
                'altFormat': 'altFormat',
                'appendText': 'label.content',
                'buttonImage': null,
                'buttonImageOnly': null,
                'buttonText': null,
                'changeMonth': function(v) { return { start: v ? 'year' : 'month' }; },
                'changeYear': function(v) { return { start: v ? 'year' : 'month' }; },
                'closeText': null,
                'constrainInput': 'dateInput',
                'currentText': null,
                'dateFormat': 'format',
                'dayNames': null,
                'dayNamesMin': null,
                'dayNamesShort': null,
                'defaultDate': 'value',
                'duration': function(v) { return { animation: { open: { duration: v } } }; },
                'firstDay': null,
                'gotoCurrent': null,
                'hideIfNoPrevNext': null,
                'isRTL': 'isRTL',
                'maxDate': 'max',
                'minDate': 'min',
                'maxDate': function(v) { 
                    return { 
                        max: normalizeDate(v, options.culture)
                    }; 
                },
                'minDate': function(v) { 
                    return { 
                        min: normalizeDate(v, options.culture)
                    }; 
                },
                'monthNames': null,
                'monthNamesShort': null,
                'navigationAsDateFormat': null,
                'nextText': null,
                'numberOfMonths': null,
                'prevText': null,
                'selectOtherMonths': null,
                'shortYearCutoff': null,
                'showAnim': function(v) { 
                    return { 
                        animation: v === false ? false : { 
                            open: { effects: v === 'slideDown' ? 'slideIn:down' : 'fadeIn' },
                            close: { effects: v === 'slideUp' ? 'slideOut:up' : 'fadeOut' }
                        }
                    }; 
                },
                'showButtonPanel': null, // 'footer'
                'showCurrentAtPos': null,
                'showMonthAfterYear': null,
                'showOn': null,
                'showOptions': null,
                'showOtherMonths': null,
                'showWeek': 'weekNumber',
                'stepMonths': null,
                'weekHeader': 'messages.weekColumnHeader',
                'yearRange': function(v) { 
                    var range = v.split(':');
                    return { 
                        min: new Date(parseInt(range[0]), 0, 1), 
                        max: new Date(parseInt(range[1]), 11, 31) 
                    }; 
                },
                'yearSuffix': null,
                'beforeShow': 'open',
                'beforeShowDay': 'disableDates',
                'onChangeMonthYear': null,
                'onClose': 'close',
                'onSelect': 'change',
                'onOpen': 'open'
            };
            
            // Convert jQuery UI options to Kendo UI options
            for (var key in options) {
                if (optionMap.hasOwnProperty(key)) {
                    var mapping = optionMap[key];
                    
                    if (typeof mapping === 'function') {
                        $.extend(true, kendoOptions, mapping(options[key]));
                    } else if (mapping !== null) {
                        // Handle nested properties
                        var parts = mapping.split('.');
                        var target = kendoOptions;
                        
                        for (var i = 0; i < parts.length - 1; i++) {
                            if (!target[parts[i]]) {
                                target[parts[i]] = {};
                            }
                            target = target[parts[i]];
                        }
                        
                        target[parts[parts.length - 1]] = options[key];
                    }
                } else {
                    kendoOptions[key] = options[key];
                }
            }
            
            // Special handling for events
            if (options.beforeShowDay) {
                kendoOptions.disableDates = function(date) {
                    var result = options.beforeShowDay(date);
                    return result[0] ? false : true;
                };
            }
        }
        // My default options 
        kendoOptions.hide = false;
        kendoOptions.animation = {
            close: {
                effects: "fadeOut",
                duration: 200
            },
            open: {
                effects: "fadeIn",
                duration: 200
            }
        };
        kendoOptions.depth = "day"; // month
        if (kendoOptions.format?.length) kendoOptions.format = kendoOptions.format.replaceAll('m','M');
        // Initialize Kendo DatePicker with converted options
        return this.each(function() {
            var $this = $(this);
            var elementId = $this.attr('id');

            // If already initialized, destroy first
            if ($this.data('kendoDatePicker')) $this.data('kendoDatePicker').destroy();
            if ($this.data('kendoDatePickerShamsi')) $this.data('kendoDatePickerShamsi').destroy();
            if ($this.data('kendoDatePickerHijri')) $this.data('kendoDatePickerHijri').destroy();
            var thisdata;
            // Initialize Kendo DatePicker
            if (kendoOptions.culture == 'fa-IR') {
                thisdata = 'kendoDatePickerShamsi';
                $this.kendoDatePickerShamsi(kendoOptions);
                if (kendoOptions.min) [$this.datepicker('option', 'minDate', kendoOptions.min)];
                if (kendoOptions.max) [$this.datepicker('option', 'maxDate', kendoOptions.max)];
            } else if (kendoOptions.culture == 'ar-SA') {
                thisdata = 'kendoDatePickerHijri';
                $this.kendoDatePickerHijri(kendoOptions);
                if (kendoOptions.min) [$this.datepicker('option', 'minDate', kendoOptions.min)];
                if (kendoOptions.max) [$this.datepicker('option', 'maxDate', kendoOptions.max)];
            } else {
                thisdata = 'kendoDatePicker';
                $this.kendoDatePicker(kendoOptions);
            }

            // Store reference for connected pickers
            connectedPickers[elementId] = {
                element: $this,
                instance: $this.data(thisdata),
                minDate: options.minDate,
                maxDate: options.maxDate,
                onSelect: options.onSelect
            };

            // Map events
            var widget = $this.data(thisdata);

            if (options.onSelect) {
                widget.bind('change', function(e) {
                    var selectedDate = this.value();
                    options.onSelect.call(this, selectedDate, this);
                });
            }

            if (options.onClose) {
                widget.bind('close', function(e) {
                    options.onClose.call(this, this.value(), this);
                });
            }

            if (options.onOpen) {
                widget.bind('open', function(e) {
                    options.onOpen.call(this, this.value(), this);
                });
            }
        });
    };

    
    // Provide noConflict to restore original datepicker
    $.fn.datepicker.noConflict = function() {
        $.fn.datepicker = originalDatepicker;
        return this;
    };
})(jQuery);

/* Input validation start */
function initializeDateInputValidation(inputElement) {
    let lastValidValue = "";
    let currentPosition = 0;
    const separator = "/";

    inputElement.on("input", function(e) {
        const datePicker = inputElement.data("kendoDatePicker") || 
                          inputElement.data("kendoDatePickerShamsi") || 
                          inputElement.data("kendoDatePickerHijri");
        const format = datePicker.options.format.toLowerCase();
        const culture = datePicker.options.culture;
        let value = inputElement.val();
        
        value = value.replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d))
                    .replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));
        
        const validation = validateDateInput(value, format, culture, datePicker);
        
        if (!validation.isValid) {
            inputElement.val(lastValidValue);
            showDateError(validation.errorMessage);
            return;
        }
        const formattedValue = value;
        if (formattedValue !== value) {
            inputElement.val(formattedValue);
            value = formattedValue;
        }
        lastValidValue = value;
        if (isCompleteDate(value, format)) {
            try {
                const parsedDate = parseDate(value, format, culture);
                datePicker.value(parsedDate);
            } catch (e) {
                console.error("Date parsing failed", e);
            }
        }
    });

    function validateDateInput(value, format, culture, datePicker) {
        const formatParts = getFormatParts(format);
        const valueParts = value.split(/[^0-9]/).filter(Boolean);
        for (let i = 0; i < value.length; i++) {
            const char = value[i];
            if (char === separator && value.length<3) return {isValid: false};
            if (char === separator) continue;
            const partInfo = getCurrentPart(i, formatParts, value);
            if (!partInfo) continue;
            const { partType, partIndex, positionInPart } = partInfo;
            switch (partType) {
                case 'year':
                    if (!validateYearChar(char, positionInPart, culture, datePicker.options.min, datePicker.options.max)) {
                        return {isValid: false,errorMessage: getYearValidationError(char, positionInPart, culture)};
                    }
                    break;
                    
                case 'month':
                    if (!validateMonthChar(char, positionInPart)) {
                        return {isValid: false,errorMessage: "عدد ماه نامعتبر است"};
                    }
                    valueSplit = value.split(separator);
                    if (positionInPart == 1 && valueSplit[partIndex] > 12) {
                        return {isValid: false,errorMessage: "عدد ماه باید حداکثر ۱۲ باشد"};
                    }
                    break;
                    
                case 'day':
                    if (valueParts[0] && valueParts[1]) {
                        const maxDay = getMaxDay(parseInt(valueParts[0]), parseInt(valueParts[1]), culture);
                        if (!validateDayChar(char, positionInPart, maxDay)) {
                            return {isValid: false,errorMessage: `روز باید بین ۱ تا ${maxDay} باشد`};
                        }
                    }
                    break;
            }
        }
        
        return { isValid: true };
    }

    function validateYearChar(char, position, culture, minDate, maxDate) {
        const currentYear = new Date().getFullYear();
        const minYear = minDate ? getYear(minDate, culture) : 1300;
        const maxYear = maxDate ? getYear(maxDate, culture) : 1500;
        if (position === 0) {
            if (culture === 'fa-IR') {
                return /[1]/.test(char);
            } else if (culture === 'ar-SA') {
                return /[1]/.test(char);
            } else {
                return /[12]/.test(char);
            }
        }
        return true;
    }

    function validateMonthChar(char, position) {
        if (position === 0) {
            return /[01]/.test(char);
        }
        return true;
    }

    function validateDayChar(char, position, maxDay) {
        if (position === 0) {
            if (maxDay >= 30) return /[0-3]/.test(char);
            if (maxDay >= 20) return /[0-2]/.test(char);
            return /[0-1]/.test(char);
        }
        return true;
    }

    function getYear(date, culture) {
        if (culture === 'fa-IR' && typeof JalaliDate !== 'undefined') {
            return new JalaliDate(date).getFullYear();
        }
        if (culture === 'ar-SA' && typeof HijriDate !== 'undefined') {
            return new HijriDate(date).getFullYear();
        }
        return date.getFullYear();
    }

    function getMaxDay(year, month, culture) {
        month = parseInt(month);
        if (culture === 'fa-IR') {
            if (month <= 6) return 31;
            if (month <= 11) return 30;
            if (typeof JalaliDate !== 'undefined') {
                return new JalaliDate(year, 11, 1).isLeapYear() ? 30 : 29;
            }
            return 29;
        }
        
        if (culture === 'ar-SA') {
            const longMonths = [1, 3, 5, 7, 9, 11];
            if (longMonths.includes(month)) return 30;
            if (month === 12) {
                if (typeof HijriDate !== 'undefined') {
                    return new HijriDate(year, 11, 1).isLeapYear() ? 30 : 29;
                }
                return 29;
            }
            return 29;
        }
        
        if (month === 2) {
            return (year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)) ? 29 : 28;
        }
        return [4, 6, 9, 11].includes(month) ? 30 : 31;
    }

    function isCompleteDate(value, format) {
        const separator = format.match(/[^ymd]/)?.[0] || '/';
        const parts = value.split(separator);
        const formatParts = format.toLowerCase().split(/[^ymd]/).filter(Boolean);
        
        return parts.length === formatParts.length && 
               parts.every((part, index) => part.length === formatParts[index].length);
    }

    function parseDate(dateStr, format, culture) {
        const normalized = dateStr.replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d))
                                .replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));
        const separator = format.match(/[^ymd]/)?.[0] || '/';
        const parts = normalized.split(separator);
        const formatParts = format.toLowerCase().split(/[^ymd]/).filter(Boolean);
        let year, month, day;
        formatParts.forEach((part, index) => {
            const value = parseInt(parts[index]) || 0;
            if (part.startsWith('y')) year = value;
            if (part.startsWith('m')) month = value;
            if (part.startsWith('d')) day = value;
        });
        switch(culture) {
            case 'fa-IR': // Persian (Shamsi)
                if (typeof JalaliDate !== 'undefined') {
                    const jDate = new JalaliDate();
                    jDate.setFullYear(year, month - 1, day);
                    return jDate.toGregorian();
                }
                break;
                
            case 'ar-SA': // Hijri
                if (typeof HijriDate !== 'undefined') {
                    const hDate = new HijriDate();
                    hDate.setFullYear(year, month - 1, day);
                    return hDate.toGregorian();
                }
                break;
        }
        return new Date(year, month - 1, day);
    }

    function showDateError(message) {
        if (message?.length) snackbar("kendo_error", message, "danger", {hasIcon: true});
    }

    function getFormatParts(format) {
        const parts = [];
        let currentPart = '';
        
        for (const char of format.toLowerCase()) {
            if (['y', 'm', 'd'].includes(char)) {
                if (currentPart && !currentPart.includes(char)) {
                    parts.push({ type: currentPart[0], length: currentPart.length });
                    currentPart = '';
                }
                currentPart += char;
            } else if (currentPart) {
                parts.push({ type: currentPart[0], length: currentPart.length });
                currentPart = '';
            }
        }
        
        if (currentPart) {
            parts.push({ type: currentPart[0], length: currentPart.length });
        }
        
        return parts;
    }

    function getCurrentPart(position, formatParts, value) {
        let charCount = 0;
        let partStart = 0;
        
        for (const part of formatParts) {
            const partEnd = partStart + part.length;
            if (position >= charCount && position < charCount + part.length) {
                return {
                    partType: part.type === 'y' ? 'year' : part.type === 'm' ? 'month' : 'day',
                    partIndex: formatParts.indexOf(part),
                    positionInPart: position - charCount,
                    partLength: part.length
                };
            }
            charCount += part.length;
            if (value[charCount] === separator) {
                charCount++;
            }
            partStart = charCount;
        }
        
        return null;
    }

    function getYearValidationError(char, position, culture) {
        if (culture === 'fa-IR') {
            if (position === 0 && char !== '1') return "سال باید با ۱ شروع شود";
            return "عدد سال نامعتبر است";
        } else if (culture === 'ar-SA') {
            if (position === 0 && char !== '1') return "سال باید با ۱ شروع شود";
            return "عدد سال نامعتبر است";
        } else {
            if (position === 0 && !['1','2'].includes(char)) return "سال باید با ۱ یا ۲ شروع شود";
            return "عدد سال نامعتبر است";
        }
    }
} 
/* Input validation end */

/* Great loading bar animation */
(function($) {
    // Configuration
    const config = {
        minShowTime: 300,       // Minimum time to show loader (ms)
        excludeSelectors: [],   // URLs or parts to exclude
        animationSpeed: 300,    // Animation speed (ms)
        debug: false           // Enable console logging
    };

    // State management
    let activeRequests = 0;
    let showTimeout = null;
    let forcedVisible = false;

    // Initialize the loader element
    function initLoader() {
        if ($('.universal-loading-indicator').length === 0) {
            $('body').append(`
            <div class="universal-loading-indicator">
              <div class="loading-bar"></div>
            </div>
          `);
        }
    }

    // Show the loading indicator
    function showLoader() {
        clearTimeout(showTimeout);
        const $indicator = $('.universal-loading-indicator');

        if (forcedVisible) return;

        $indicator.addClass('active');
        $indicator.find('.loading-bar').css('transform', 'translateX(0)');

        if (config.debug) console.log('[Loader] Showing loading indicator');
    }

    // Hide the loading indicator
    function hideLoader() {
        const $indicator = $('.universal-loading-indicator');
        const $bar = $indicator.find('.loading-bar');

        if (forcedVisible) return;

        $bar.css('transform', 'translateX(100%)');

        setTimeout(() => {
            if (activeRequests === 0) {
                $indicator.removeClass('active');
                if (config.debug) console.log('[Loader] Hiding loading indicator');
            }
        }, config.animationSpeed);
    }

    // Check if request should be tracked
    function shouldTrackRequest(url) {
        if (!url) return true;

        return !config.excludeSelectors.some(exclude => {
            if (typeof exclude === 'string') {
                return url.includes(exclude);
            } else if (exclude instanceof RegExp) {
                return exclude.test(url);
            }
            return false;
        });
    }

    // Patch jQuery AJAX methods
    function patchJQueryAjax() {
        const originalAjax = $.ajax;

        $.ajax = function(options) {
            // Handle different jQuery AJAX signatures
            if (typeof options === 'string') {
                options = { url: options };
            }

            const shouldTrack = shouldTrackRequest(options.url);
            let requestCompleted = false;

            if (shouldTrack) {
                activeRequests++;
                if (activeRequests === 1) {
                    showTimeout = setTimeout(showLoader, 50);
                }
            }

            // Store original callbacks
            const originalComplete = options.complete;
            const originalSuccess = options.success;
            const originalError = options.error;

            // Add our handlers
            options.complete = function() {
                if (shouldTrack && !requestCompleted) {
                    requestCompleted = true;
                    activeRequests = Math.max(0, activeRequests - 1);
                    if (activeRequests === 0) {
                        const elapsed = Date.now() - startTime;
                        const remaining = Math.max(config.minShowTime - elapsed, 0);
                        setTimeout(hideLoader, remaining);
                    }
                }

                if (originalComplete) {
                    originalComplete.apply(this, arguments);
                }
            };

            options.success = function() {
                if (shouldTrack && !requestCompleted) {
                    requestCompleted = true;
                    activeRequests = Math.max(0, activeRequests - 1);
                    if (activeRequests === 0) {
                        const elapsed = Date.now() - startTime;
                        const remaining = Math.max(config.minShowTime - elapsed, 0);
                        setTimeout(hideLoader, remaining);
                    }
                }

                if (originalSuccess) {
                    originalSuccess.apply(this, arguments);
                }
            };

            options.error = function() {
                if (shouldTrack && !requestCompleted) {
                    requestCompleted = true;
                    activeRequests = Math.max(0, activeRequests - 1);
                    if (activeRequests === 0) {
                        const elapsed = Date.now() - startTime;
                        const remaining = Math.max(config.minShowTime - elapsed, 0);
                        setTimeout(hideLoader, remaining);
                    }
                }

                if (originalError) {
                    originalError.apply(this, arguments);
                }
            };

            const startTime = Date.now();
            return originalAjax.call($, options);
        };

        // Patch shorthand methods ($.get, $.post, etc.)
        ['get', 'post', 'getJSON', 'getScript'].forEach(method => {
            const originalMethod = $[method];

            $[method] = function(url, data, success, dataType) {
                // Handle different signatures
                if (typeof data === 'function') {
                    dataType = success;
                    success = data;
                    data = undefined;
                }

                const shouldTrack = shouldTrackRequest(url);
                let requestCompleted = false;
                const startTime = Date.now();

                if (shouldTrack) {
                    activeRequests++;
                    if (activeRequests === 1) {
                        showTimeout = setTimeout(showLoader, 50);
                    }
                }

                return originalMethod.call($, url, data, function() {
                    if (shouldTrack && !requestCompleted) {
                        requestCompleted = true;
                        activeRequests = Math.max(0, activeRequests - 1);
                        if (activeRequests === 0) {
                            const elapsed = Date.now() - startTime;
                            const remaining = Math.max(config.minShowTime - elapsed, 0);
                            setTimeout(hideLoader, remaining);
                        }
                    }

                    if (success) success.apply(this, arguments);
                }, dataType).fail(function() {
                    if (shouldTrack && !requestCompleted) {
                        requestCompleted = true;
                        activeRequests = Math.max(0, activeRequests - 1);
                        if (activeRequests === 0) {
                            const elapsed = Date.now() - startTime;
                            const remaining = Math.max(config.minShowTime - elapsed, 0);
                            setTimeout(hideLoader, remaining);
                        }
                    }
                });
            };
        });
    }

    // Public API
    $.loadingIndicator = {
        show: function() {
            forcedVisible = true;
            showLoader();
        },
        hide: function() {
            forcedVisible = false;
            activeRequests = 0;
            hideLoader();
        },
        config: function(newConfig) {
            $.extend(config, newConfig);
        },
        getActiveRequests: function() {
            return activeRequests;
        }
    };

    // Initialize
    $(document).ready(function() {
        initLoader();
        patchJQueryAjax();
    });

})(jQuery);

/* Support tiff images */
async function loadTifAsPng(url) {
    Tiff.initialize({TOTAL_MEMORY: 16777216 * 10});
    return new Promise((resolve, reject) => {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url);
        xhr.responseType = 'arraybuffer';
        xhr.onload = function (e) {
            var buffer = xhr.response;
            var tiff = new Tiff({buffer: buffer});
            for (var i = 0, len = tiff.countDirectory(); i < len; ++i) {
                tiff.setDirectory(i);
                var canvas = tiff.toCanvas();
                resolve(canvas.toDataURL())
            }
        };
        xhr.send();
    });
}

/* Print Screen */
function openAndPrint(url) {
    const iframe = document.createElement("iframe");
    iframe.style.position = "absolute";
    iframe.style.width = "0";
    iframe.style.height = "0";
    iframe.style.border = "0";
    iframe.src = url;
    snackbar("print_snackbar", "در حال تلاش برای چاپ فرم ...", "success",{hasIcon: true});
    iframe.onload = function () {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
    };
    document.body.appendChild(iframe);
}

function base64ToFile(base64, filename, mimeType) {
    var arr = base64.split(',');
    var bstr = atob(arr[1]);
    var n = bstr.length;
    var u8arr = new Uint8Array(n);
    while(n--) u8arr[n] = bstr.charCodeAt(n);
    return new File([u8arr], filename, {type: mimeType});
}

// Scrolled elements snapshots:
class ScrollManager {
    constructor(prefix = 'sm') {
        this._prefix = prefix;
        this._idCounter = 1;
    }

    _makeId() {
        return `${this._prefix}-${Date.now().toString(36)}-${this._idCounter++}`;
    }

    ensureId(el) {
        if (!el || el.nodeType !== 1) return null;
        if (el.dataset && el.dataset.scrollId) return el.dataset.scrollId;
        const id = this._makeId();
        el.setAttribute('data-scroll-id', id);
        return id;
    }

    _findScrollables(root) {
        root = root || document;
        const all = Array.from(root.querySelectorAll('*'));
        const scrollables = [];
        for (let i = 0; i < all.length; i++) {
            const el = all[i];
            if (el.scrollHeight > el.clientHeight) scrollables.push(el);
        }
        return scrollables;
    }

    stampForSave(root) {
        const els = this._findScrollables(root);
        for (const el of els) this.ensureId(el);
    }

    takeSnapshot(root) {
        root = root || document;
        const positions = {};
        const els = this._findScrollables(root);
        for (const el of els) {
            const id = this.ensureId(el);
            if (!id) continue;
            if (el.scrollTop) positions[id] = el.scrollTop;
        }
        const pageY = window.scrollY || 0;
        return { positions, pageY };
    }

    restoreSnapshot(snapshot, rootSelector) {
        if (!snapshot) return;
        const root = rootSelector ? document.querySelector(rootSelector) : null;
        const ids = Object.keys(snapshot.positions || {});
        let tries = 0;
        const maxTries = 8;

        const tryOnce = () => {
            tries++;
            const missing = [];
            for (const id of ids) {
                const sel = `[data-scroll-id="${id}"]`;
                let el = root ? root.querySelector(sel) : document.querySelector(sel);
                if (!el) el = document.querySelector(sel); // fallback global
                if (el) {
                    try { el.scrollTop = snapshot.positions[id]; } catch (err) { /* ignore */ }
                } else {
                    missing.push(id);
                }
            }
            if (typeof snapshot.pageY === 'number') window.scrollTo(0, snapshot.pageY);
            if (missing.length && tries < maxTries) {
                requestAnimationFrame(tryOnce);
            }
        };

        requestAnimationFrame(tryOnce);
    }
}

const globalScrollManager = new ScrollManager();

// Page state handling :
function savePageState(key, container) {
    const inputs = {};
    document.querySelectorAll("input, textarea, select").forEach(el => {
        if (el.id) inputs[el.id] = el.value;
    });
    let containerEl = document.querySelector(container);
    if (!containerEl) return;
    globalScrollManager.stampForSave(containerEl);
    const scrollSnapshot = globalScrollManager.takeSnapshot(containerEl);
    pageCache.set(key, {
        html: containerEl.innerHTML,
        inputs,
        container,
        scrollSnapshot,
        overlayElements
    });

    if (pageCache.size > MAX_CACHE_SIZE) {
        const firstKey = pageCache.keys().next().value;
        pageCache.delete(firstKey);
    }
}

function restorePageState(key) {
    const state = pageCache.get(key);
    if (!state || !state.html) return false;

    let containerEl = document.querySelector(state.container);

    containerEl.innerHTML = state.html;
    // containerEl.innerHTML = removeScriptsAndStylesFromHTML(state.html);
    window.overlayElements = state.overlayElements;
    // STEP 5: Restore form inputs and other elements
    for (const [id, value] of Object.entries(state.inputs)) {
        const el = document.getElementById(id);
        if (el) el.value = value;
    }

    ["span", "button", "a", "li"].forEach(tag => {
        document.querySelectorAll(tag).forEach(el => {
            el.style.pointerEvents = "";
        });
    });

    if (loadFunctionCache?.size) {
        [...loadFunctionCache.values()].filter(key => key.pathname == window.location.pathname).slice(-MAX_LOAD_FUNCTION_SIZE).reverse().forEach(key => {
            if (typeof key.function == "function") key.function();
        })
    }
    clearTimeout(window.global_snackbar_timeout)
    $(".snackbar").each(function() {$(this).remove()});
    $(".universal-loading-indicator").removeClass("active");
    $(".modal-backdrop").each(function() {if ($(this).children().length<1) $(this).remove()});
    $(".modal").css("display","");
    $(".modal.show").removeClass("show");
    $("#loading").css("display", "none");
    $("button[data-temp-disabled='1']").each(function () {$(this).prop("disabled", false).removeAttr("data-temp-disabled");});
    if (state.scrollSnapshot) globalScrollManager.restoreSnapshot(state.scrollSnapshot, state.container);
    return true;
}

window.addEventListener("popstate", e => {
    const key = e.state?.key;
    if (key && restorePageState(key)) return;
    link_transfer(location.href, 'cache')
});

$(document).ready(function() {
    if (!history.state) {
        history.replaceState({ key: "initial" }, "", location.href);
        savePageState("initial", ".date_path_set1");
    }
})

function removeScriptsAndStylesFromHTML(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const scripts = doc.querySelectorAll('script[src]');
    scripts.forEach(script => {
        script.remove();
    });
    const stylesheets = doc.querySelectorAll('link[rel="stylesheet"]');
    stylesheets.forEach(style => {
        style.remove();
    });
    const styleBlocks = doc.querySelectorAll('style');
    styleBlocks.forEach(style => {
        style.remove();
    });
    const moduleScripts = doc.querySelectorAll('script[type="module"]');
    moduleScripts.forEach(script => {
        script.remove();
    });
    return doc.body.innerHTML;
}

class MiniAppAuth {
    loginLink = '';
    platform = 'generic';
    snackbarPrefix = 'auth';
    sdkUrl = '';
    globalObjectName = '';
    userFields = {};
    
    constructor(config = {}) {
        Object.assign(this, config);
        this.init();
    }

    async init() {
        if (!this.sdkUrl || !this.globalObjectName) {
            console.error('SDK configuration not set');
            return;
        }

        await scriptLoader.loadScriptsSequentially([PATHFILE+'assets/jquery/jquery-3.7.0.min.js',this.sdkUrl]);
        this.webApp = window[this.globalObjectName]?.WebApp;
        this.isPlatform = !!this.webApp;
        if (!this.isPlatform) {
            snackbar(`${this.snackbarPrefix}_error`, `Not in ${this.platform} environment`, "error", {hasIcon: true});
            return;
        }
        
        this.webApp.ready();
        this.setupEventListeners();
        
        if (!(getCookie("CAS_ID")?.length > 0)) {
            this.setupAuth();
        }
    }

    async setupAuth() {
        try {
            const userData = this.webApp.initDataUnsafe?.user;
            const initData = this.webApp.initData;
            
            if (userData && initData) {
                await this.processPlatformAuth(userData, initData);
            }
        } catch (error) {
            snackbar(`${this.snackbarPrefix}_error`, "خطا در راه‌اندازی احراز هویت", "error", {hasIcon: true});
        }
    }

    async processPlatformAuth(userData, initData) {
        try {
            // This method should be overridden by subclasses
            throw new Error('processPlatformAuth must be implemented by subclass');
        } catch (error) {
            snackbar(`${this.snackbarPrefix}_error`, "خطا در پردازش اطلاعات کاربر: " + error.toString(), "error", {hasIcon: true});
        }
    }
    
    async validateInitDataOnServer(userData) {
        return new Promise((res, rej) => {
            window.jQuery.ajax({
                type: "Post",
                url: PATHFILE + "execute/login/optional/init",
                data: (new URLSearchParams(userData)).toString(),
                cache: "false",
                success: function(html) {
                    let json = JSON.parse(html);
                    res(json.status == "8");
                },
                error: function(err) {
                    res(false);
                }
            });
        });
    }

    async signInUser(userData) {
        const response = await fetch(PATHFILE + "execute/register/optional/signin", {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({...userData})
        });

        const result = await response.json();
        if (result.success) {
            this.onAuthSuccess(result.user, result.token);
        } else {
            snackbar("auth_error", "خطا در ورود به سیستم", "error", {hasIcon: true});
        }
    }

    signUpUser(userData) {
        getCookie("CAS_ID", null, 2);
        console.log(getCookie("CAS_ID"));
        window.jQuery.ajax({
            type: "Post",
            url: PATHFILE + "execute/login/optional",
            data: (new URLSearchParams(userData)).toString(),
            cache: "false",
            success: async function(html) {
                document.dispatchEvent(new CustomEvent('authSuccess', {}));
                window.jQuery('body').append(html);
                await snackbar(`${this.snackbarPrefix}_success`, 
                    'کاربر گرامی ورود شما با موفقیت صورت گرفته است درحال انتقال شما به صفحه ی مورد نظر هستیم', 
                    "success", {hasIcon: true});
                link_transfer(window.location.href + (window.location.pathname == '/' ? 'home' : ''), "direct");
            }.bind(this),
            error: function(err) {
                snackbar("signup_error", "خطا در ثبت نام کاربر" + JSON.stringify(err), "danger", {hasIcon: true, forceGenerate: true});
            }
        });
    }

    checkUser(userData) {
        return new Promise((res, rej) => {
            window.jQuery.ajax({
                type: "Post",
                url: PATHFILE + "execute/login/optional/check",
                data: (new URLSearchParams(userData)).toString(),
                cache: "false",
                success: async function(html) {
                    let json = JSON.parse(html);
                    res(json.exists == 't');
                },
                error: function(err) {
                    res(false);
                }
            });
        });
    }

    setupEventListeners() {
        this.webApp.onEvent('contactRequested', (event) => {
            this.onContactRequested(event);
        });

        if (this.webApp.onEvent && this.webApp.onEvent.toString().includes('writeAccessRequested')) {
            this.webApp.onEvent('writeAccessRequested', (event) => {
                this.onWriteAccessRequested(event);
            });
        }
    }

    async getPhoneNumber() {
        try {
            const result = await this.requestPhoneNumber();
            if (result.success) return result;
            this.showError('اجازه دسترسی به شماره تلفن توسط شما لغو گردید.');
            return null;
        } catch (error) {
            this.showError('خطا در دریافت شماره تلفن');
            return null;
        }
    }

    processContactData(contactData) {
        if (!contactData) return null;
        const parsedData = this.parseContactData(contactData);
        if (!parsedData) {
            this.showError('خطا در پردازش اطلاعات تماس');
            return null;
        }
        return parsedData;
    }

    showError(message) {
        snackbar(`${this.snackbarPrefix}_error`, message, "error", {hasIcon: true});
    }

    showSuccess(message) {
        snackbar(`${this.snackbarPrefix}_success`, message, "success", {hasIcon: true});
    }

    onContactRequested(event) {
        switch (event.status) {
            case 'sent':
                break;
            case 'cancelled':
                break;
        }
    }

    onWriteAccessRequested(event) {
        switch (event.status) {
            case 'allowed':
                this.showSuccess('دسترسی نوشتن تایید شد');
                break;
            case 'cancelled':
                this.showError('دسترسی نوشتن رد شد');
                break;
        }
    }

    // Abstract methods - must be overridden
    async requestPhoneNumber() {
        throw new Error('requestPhoneNumber must be implemented by subclass');
    }

    parseContactData(contactData) {
        throw new Error('parseContactData must be implemented by subclass');
    }
}

class EitaaAuth extends MiniAppAuth {
    constructor() {
        super({
            platform: 'eitaa',
            snackbarPrefix: 'eitaa',
            sdkUrl: "https://developer.eitaa.com/eitaa-web-app.js",
            globalObjectName: 'Eitaa',
            userFields: {
                id: 'id',
                firstName: 'first_name',
                lastName: 'last_name',
                languageCode: 'language_code'
            }
        });
    }

    async processPlatformAuth(userData, initData) {
        try {
            initData = `${JSON.stringify(initData).substring(1, JSON.stringify(initData).length - 1)}`;
            const urlParams = new URLSearchParams(initData);
            const isValid = await this.validateInitDataOnServer({
                device_id: urlParams.get('device_id'),
                hash: urlParams.get('hash'),
                auth_date: urlParams.get('auth_date'),
                users_id: userData.id,
                first_name: userData.first_name,
                last_name: userData.last_name,
                language_code: userData.language_code,
                token: WEB_TOKEN
            });
            
            if (!isValid) {
                this.showError("احراز هویت با خطا مواجه شد");
                return;
            }
            
            let token = WEB_TOKEN;
            let userExists = await this.checkUser({
                type: 'eitaa',
                type_value: userData.id,
                token
            });

            let signUpUser = this.signUpUser.bind(this);
            if (userExists) {
                snackbar("ita_auth_modal", this.getUserExistsModalHTML("ایتا", userData.first_name, userData.last_name), "info", {
                    isConfirmed: true,
                    hasIcon: true,
                    duration: 15000,
                    textStyles: {fontWeight: "bold", textAlign: "right", fontSize: "14px"},
                    acceptText: "ورود با ایتا",
                    cancelText: "انصراف",
                    customHTML: true,
                    buttonStyles: {
                        accept: {borderRadius: "6px", fontSize: "14px", fontWeight: "bold"},
                        cancel: {padding: "12px 25px", borderRadius: "6px", fontSize: "14px"}
                    }
                }).then(function (result) {
                    if (result.isConfirmed) {
                        signUpUser({
                            name: userData.first_name, 
                            family: userData.last_name, 
                            type_value: userData.id, 
                            type: 'eitaa', 
                            token, 
                            url_back: window.location.href
                        });     
                    }
                });
            } else {
                let data = await this.getPhoneNumber();
                if (data.success) {
                    let user = data.contactData.user;
                    snackbar("ita_auth_modal", this.getNewUserModalHTML("ایتا"), "info", {
                        isConfirmed: true,
                        hasIcon: true,
                        duration: 15000,
                        textStyles: {fontWeight: "bold", textAlign: "right", fontSize: "14px"},
                        acceptText: "ادامه با ایتا",
                        cancelText: "انصراف",
                        customHTML: true,
                        buttonStyles: {
                            accept: {borderRadius: "6px", fontSize: "14px", fontWeight: "bold"},
                            cancel: {padding: "12px 25px", borderRadius: "6px", fontSize: "14px"}
                        }
                    }).then(function (result) {
                        if (result.isConfirmed) {
                            signUpUser({
                                name: user.first_name, 
                                family: user.last_name, 
                                type_value: user.user_id, 
                                mobile: user.phone, 
                                type: 'eitaa', 
                                token: token, 
                                url_back: window.location.href
                            });
                        }
                    });
                }
            }
        } catch (error) {
            this.showError("خطا در پردازش اطلاعات کاربر: " + error.toString());
        }
    }

    async requestPhoneNumber() {
        snackbar("eitaa_loading", "در حال درخواست دریافت تلفن همراه از ایتا ...", "success", {hasIcon: true});
        return new Promise((resolve) => {
            this.webApp.requestContact((status, contactData) => {
                if (status) {
                    const parsedData = this.parseContactData(contactData);
                    resolve({success: true, status: 'sent', contactData: parsedData});
                } else {
                    snackbar("eitaa_contact_error", "خطایی در دریافت تلفن همراه شما رخ داده است", "danger", {hasIcon: true});
                    resolve({success: false, status: 'cancelled', contactData: null, rawData: null});
                }
            });
        });
    }

    parseContactData(contactData) {
        try {
            const urlParams = new URLSearchParams(contactData.response);
            const contactParam = urlParams.get('contact');
            const decodedJson = decodeURIComponent(contactParam);
            const userData = JSON.parse(decodedJson);
            const authDate = urlParams.get('auth_date');
            const hash = urlParams.get('hash');
            return {user: userData, auth_date: authDate, hash: hash};
        } catch (error) {
            snackbar("parse_error", "خطا در پردازش اطلاعات تماس", "error", {hasIcon: true});
            return null;
        }
    }

    // Helper methods for HTML templates
    getUserExistsModalHTML(platformName, firstName, lastName) {
        return `
            <div style="text-align: right; line-height: 1.8;">
                <h3 class="mb-2 text-first-darker">🔐 ورود با ${platformName}</h3>
                <p class="mb-2">برای ادامه فرآیند، نیاز به ورود از طریق اپلیکیشن ${platformName} دارید.</p>
                <p class="mb-2">و یا ادامه دادن با <a href="javascript:void(0)" onclick="link_transfer('${this.loginLink}')" class="text-second">ورود/ثبت نام</a> در سامانه</p>
                <ul class="text-light-dark">
                    <li>اطلاعات شما با امنیت کامل پردازش می‌شود</li>
                    <li>فرآیند تنها چند ثانیه طول می‌کشد</li>
                </ul>
            </div>
        `;
    }

    getNewUserModalHTML(platformName) {
        return `
            <div style="text-align: right; line-height: 1.8;">
                <h3 class="mb-2 text-first-darker">🔐 احراز هویت ${platformName}</h3>
                <p class="mb-2">برای ادامه فرآیند، نیاز به احراز هویت از طریق اپلیکیشن ${platformName} دارید.</p>
                <ul class="text-light-dark">
                    <li>اطلاعات شما با امنیت کامل پردازش می‌شود</li>
                    <li>فرآیند تنها چند ثانیه طول می‌کشد</li>
                </ul>
            </div>
        `;
    }
}

class BaleAuth extends MiniAppAuth {
    constructor() {
        super({
            platform: 'bale',
            snackbarPrefix: 'bale',
            sdkUrl: "https://tapi.bale.ai/miniapp.js?3",
            globalObjectName: 'Bale',
            userFields: {
                id: 'id',
                firstName: 'first_name',
                username: 'username'
            }
        });
    }

    async processPlatformAuth(userData, initData) {
        try {
            initData = `${JSON.stringify(initData).substring(1, JSON.stringify(initData).length - 1)}`;
            const urlParams = new URLSearchParams(initData);
            const isValid = await this.validateInitDataOnServer({
                device_id: urlParams.get('device_id'),
                hash: urlParams.get('hash'),
                auth_date: urlParams.get('auth_date'),
                users_id: userData.id,
                first_name: userData.first_name,
                username: userData.username,
                token: WEB_TOKEN
            });
            
            if (!isValid) {
                this.showError("احراز هویت با خطا مواجه شد");
                return;
            }
            let token = WEB_TOKEN;
            let userExists = await this.checkUser({
                type: 'bale',
                type_value: userData.id,
                token
            });

            let signUpUser = this.signUpUser.bind(this);
            if (userExists) {
                snackbar("bale_auth_modal", this.getUserExistsModalHTML("بله", userData.first_name, userData.username), "info", {
                    isConfirmed: true,
                    hasIcon: true,
                    duration: 15000,
                    textStyles: {fontWeight: "bold", textAlign: "right", fontSize: "14px"},
                    acceptText: "ورود با بله",
                    cancelText: "انصراف",
                    customHTML: true,
                    buttonStyles: {
                        accept: {borderRadius: "6px", fontSize: "14px", fontWeight: "bold"},
                        cancel: {padding: "12px 25px", borderRadius: "6px", fontSize: "14px"}
                    }
                }).then(function (result) {
                    if (result.isConfirmed) {
                        signUpUser({
                            name: userData.first_name, 
                            username: userData.username, 
                            type_value: userData.id, 
                            type: 'bale', 
                            token, 
                            url_back: window.location.href
                        });     
                    }
                });
            } else {
                let data = await this.getPhoneNumber();
                if (data.success) {
                    snackbar("bale_auth_modal", this.getNewUserModalHTML("بله"), "info", {
                        isConfirmed: true,
                        hasIcon: true,
                        duration: 15000,
                        textStyles: {fontWeight: "bold", textAlign: "right", fontSize: "14px"},
                        acceptText: "ادامه با بله",
                        cancelText: "انصراف",
                        customHTML: true,
                        buttonStyles: {
                            accept: {borderRadius: "6px", fontSize: "14px", fontWeight: "bold"},
                            cancel: {padding: "12px 25px", borderRadius: "6px", fontSize: "14px"}
                        }
                    }).then(function (result) {
                        if (result.isConfirmed) {
                            signUpUser({
                                name: userData.first_name, 
                                username: userData.username, 
                                type_value: userData.id, 
                                mobile: data.contactData.phone, 
                                type: 'bale', 
                                token: token, 
                                url_back: window.location.href
                            });
                        }
                    });
                }
            }
        } catch (error) {
            this.showError("خطا در پردازش اطلاعات کاربر: " + error.toString());
        }
    }

    async requestPhoneNumber() {
        snackbar("bale_loading", "در حال درخواست دریافت تلفن همراه از بله ...", "success", {hasIcon: true});
        return new Promise((resolve) => {
            this.webApp.requestContact((status, phoneNumber) => {
                if (status) {
                    resolve({
                        success: true,
                        status: 'sent',
                        contactData: { phone: phoneNumber }
                    });
                } else {
                    snackbar("bale_contact_error", "خطایی در دریافت تلفن همراه شما رخ داده است", "danger", {hasIcon: true});
                    resolve({success: false, status: 'cancelled', contactData: null});
                }
            });
        });
    }

    parseContactData(contactData) {
        // Bale returns phone number directly, no parsing needed
        return { phone: contactData };
    }

    // Helper methods for HTML templates (inherit from parent or define here)
    getUserExistsModalHTML(platformName, firstName, username) {
        return `
            <div style="text-align: right; line-height: 1.8;">
                <h3 class="mb-2 text-first-darker">🔐 ورود با ${platformName}</h3>
                <p class="mb-2">برای ادامه فرآیند، نیاز به ورود از طریق اپلیکیشن ${platformName} دارید.</p>
                <p class="mb-2">و یا ادامه دادن با <a href="javascript:void(0)" onclick="link_transfer('${this.loginLink}')" class="text-second">ورود/ثبت نام</a> در سامانه</p>
                <ul class="text-light-dark">
                    <li>اطلاعات شما با امنیت کامل پردازش می‌شود</li>
                    <li>فرآیند تنها چند ثانیه طول می‌کشد</li>
                </ul>
            </div>
        `;
    }

    getNewUserModalHTML(platformName) {
        return `
            <div style="text-align: right; line-height: 1.8;">
                <h3 class="mb-2 text-first-darker">🔐 احراز هویت ${platformName}</h3>
                <p class="mb-2">برای ادامه فرآیند، نیاز به احراز هویت از طریق اپلیکیشن ${platformName} دارید.</p>
                <ul class="text-light-dark">
                    <li>اطلاعات شما با امنیت کامل پردازش می‌شود</li>
                    <li>فرآیند تنها چند ثانیه طول می‌کشد</li>
                </ul>
            </div>
        `;
    }
}

// Trie implementation for prefix and partial search
class GeoJSONTrie {
    constructor() {
        this.root = {};
        this.features = new Map();
    }
    
    insert(text, feature) {
        const featureId = feature.id || Math.random().toString(36);
        this.features.set(featureId, feature);
        const lowerText = text.toLowerCase();
        let node = this.root;
        for (const char of lowerText) {
            if (!node[char]) node[char] = {};
            node = node[char];
        }
        if (!node.features) node.features = new Set();
        node.features.add(featureId);
        for (let i = 0; i < lowerText.length; i++) {
            node = this.root;
            for (let j = i; j < lowerText.length; j++) {
                const char = lowerText[j];
                if (!node[char]) node[char] = {};
                node = node[char];
                if (!node.containsFeatures) node.containsFeatures = new Set();
                node.containsFeatures.add(featureId);
            }
        }
    }
    
    searchPrefix(prefix) {
        let node = this.root;
        for (const char of prefix.toLowerCase()) {
            if (!node[char]) return [];
            node = node[char];
        }
        return this.getFeaturesFromSet(node.features);
    }
    
    searchContains(substring) {
        let node = this.root;
        for (const char of substring.toLowerCase()) {
            if (!node[char]) return [];
            node = node[char];
        }
        return this.getFeaturesFromSet(node.containsFeatures);
    }
    
    getFeaturesFromSet(featureSet) {
        if (!featureSet) return [];
        return Array.from(featureSet).map(id => this.features.get(id));
    }
}

// Build trie index
const buildTrieIndex = (geoJsonData, searchField) => {
    const trie = new GeoJSONTrie();
    
    geoJsonData.features.forEach(feature => {
        const value = feature.properties[searchField];
        if (value) {
            trie.insert(value.toString(), feature);
        }
    });
    
    return trie;
};

let observerForInitSYSSwipers = false;
function initSYSSwipers() {
    const sliders = document.querySelectorAll(".sys_swiper:not(.initialized)");
    sliders.forEach((slider) => {
        let options = {
            loop: slider.classList.contains("sys_swiper_loop"),
        };
        if (!slider.classList.contains("sys_swiper_no_pagination")) {
            const paginationEl = slider.querySelector(".swiper-pagination");
            if (paginationEl) {
                options.pagination = {
                    el: paginationEl,
                    clickable: true,
                };
            }
        }
        if (!slider.classList.contains("sys_swiper_no_navigation")) {
            const nextEl = slider.querySelector(".swiper-button-next");
            const prevEl = slider.querySelector(".swiper-button-prev");

            if (nextEl && prevEl) {
                options.navigation = {
                    nextEl,
                    prevEl,
                };
            }
        }
        if (slider.classList.contains("sys_swiper_autoplay")) {
            let duration = 3000;
            const durationClass = [...slider.classList].find(c => c.startsWith("sys_swiper_duration_"));
            if (durationClass) {
                const value = durationClass.split("_").pop();
                duration = parseInt(value) || 3000;
            }
            options.autoplay = { delay: duration };
        }

        new Swiper(slider, options);
        slider.classList.add("initialized");
    });

    if (!observerForInitSYSSwipers) {
        const observer = new MutationObserver(() => {
            initSYSSwipers();
        });
        observer.observe(document.body, { childList: true, subtree: true });
        observerForInitSYSSwipers = true;
    }
}
document.addEventListener("DOMContentLoaded", initSYSSwipers);
document.querySelectorAll(".modal").forEach(modal => modal.addEventListener("shown.bs.modal", initSYSSwipers));

/* A method for convert Gregorian date to Hijri format start */
function toHijri(dateformat) {
    // Split the date string into an array of numbers
    let [year, month, day] = dateformat.split("-").map(Number);
    let options = { day: "numeric", month: "long", year : "numeric"};
    // Subtract 1 from the month number, as it is zero-based in JavaScript
    let date = new Intl.DateTimeFormat("ar-TN-u-ca-islamic", options).format(new Date(year, month - 1, day - 1)).replace(/هـ$/, "")
    return date
}
/* A method for convert Gregorian date to Hijri format end */

const layerManager = {
    layers: {},
    parserLayers: {},
    panes: {},
    addLayer: function(parserId, index, layer, metadata = {}) {
        const layerKey = `${parserId}_${index}`;
        const paneKey = `${parserId}_${index}_overlay`;
        
        this.layers[layerKey] = {
            layer: layer,
            parserId: parserId,
            index: index,
            metadata: metadata,
            pane: window[paneKey]
        };
        
        if (!this.parserLayers[parserId]) {
            this.parserLayers[parserId] = [];
        }
        this.parserLayers[parserId].push(layerKey);
    },
    getLayer: function(layerKey) {
        return this.layers[layerKey];
    },
    getParserLayers: function(parserId) {
        return this.parserLayers[parserId] || [];
    },
    removeLayer: function(layerKey) {
        const layerData = this.layers[layerKey];
        if (layerData) {
            if (layerData.layer && layerData.layer.removeFrom) {
                layerData.layer.removeFrom(map);
            }
            
            if (layerData.parserId && this.parserLayers[layerData.parserId]) {
                const index = this.parserLayers[layerData.parserId].indexOf(layerKey);
                if (index > -1) {
                    this.parserLayers[layerData.parserId].splice(index, 1);
                }
                
                if (this.parserLayers[layerData.parserId].length === 0) {
                    delete this.parserLayers[layerData.parserId];
                }
            }
            
            if (layerData.pane && layerData.pane.remove) {
                layerData.pane.remove();
            }
            
            delete this.layers[layerKey];
        }
    },

    removeParserLayers: function(parserId) {
        const layerKeys = this.getParserLayers(parserId);
        layerKeys.forEach(layerKey => {
            this.removeLayer(layerKey);
        });
    },

    removeInactiveLayers: function() {
        const currentTime = Date.now();
        
        for (const layerKey in this.layers) {
            const layerData = this.layers[layerKey];
            const parserId = layerData.parserId;
            
            const switchElement = parserId?.length ? document.querySelector(`.switch_layer.${parserId}`) : false;
            
            if (!switchElement || !switchElement.classList.contains('active')) {
                const layerAge = currentTime - (layerData.metadata.createdAt || 0);
                
                if (layerAge > 30000 || !switchElement) {
                    this.removeLayer(layerKey);
                }
            }
        }
    },

    clearAll: function() {
        for (const layerKey in this.layers) {
            const layerData = this.layers[layerKey];
            if (layerData.layer && layerData.layer.removeFrom) {
                layerData.layer.removeFrom(map);
            }
        }
        this.layers = {};
        this.parserLayers = {};
    },

    getCount: function() {
        return Object.keys(this.layers).length;
    },

    hasActiveLayers: function(parserId) {
        return this.getParserLayers(parserId).length > 0;
    }
};

function getParserStyles(parserType, color = "blue", properties = {}, zoom = 10) {
    if (!color?.length) color = "blue";
    function getCSColor(shade = "400") {
        if (typeof cs !== "undefined" && cs.getPropertyValue) {
            return cs.getPropertyValue("--rgb-" + color + "-" + shade);
        }
        return "";
    }
    
    const baseStyles = {
        "polygon": {
            color: "rgb(" + getCSColor("600") + ")",
            fillColor: "rgb(" + getCSColor("400") + ")",
            weight: zoom > 15 ? 2 : 1,
            opacity: 1,
            fillOpacity: 0.7,
            fill: true,
            lineJoin: "round"
        },
        "polygon_outline": {
            color: "rgb(" + getCSColor("700") + ")",
            fillColor: false,
            weight: zoom > 15 ? 3 : 2,
            opacity: 1,
            fillOpacity: 0,
            fill: false,
            lineJoin: "round"
        },
        "polygon_transparent": {
            color: "rgb(" + getCSColor("500") + ")",
            fillColor: "rgb(" + getCSColor("400") + ")",
            weight: 1,
            opacity: 0.5,
            fillOpacity: 0.3,
            fill: true,
            lineJoin: "round"
        },
        "gradient_polygon": {
            color: "rgb(" + getCSColor("600") + ")",
            fillColor: "rgb(" + getCSColor("300") + ")",
            weight: 1,
            opacity: 0.8,
            fillOpacity: zoom > 15 ? 0.6 : 0.4,
            fill: true,
            lineJoin: "round"
        },
        "pattern_fill": {
            color: "rgb(" + getCSColor("600") + ")",
            fillColor: "rgb(" + getCSColor("500") + ")",
            weight: 2,
            opacity: 0.7,
            fillOpacity: 0.4,
            fill: true,
            lineJoin: "round",
            dashArray: (properties?.id || Math.random()) % 2 === 0 ? "5, 5" : "10, 5"
        },
        "polygon_with_hatch": {
            color: "rgb(" + getCSColor("600") + ")",
            fillColor: "transparent",
            weight: 2,
            opacity: 0.7,
            fillOpacity: 0.2,
            fill: true,
            lineJoin: "round",
            dashArray: zoom > 15 ? "8, 12" : "6, 10"
        },
        "solid_line": {
            color: "rgb(" + getCSColor("600") + ")",
            fillColor: false,
            weight: zoom > 15 ? 4 : 3,
            opacity: 0.9,
            fill: false,
            fillOpacity: 0,
            lineCap: "round",
            lineJoin: "round",
            dashArray: null,
            smoothFactor: 1
        },
        "dashed_line": {
            color: "rgb(" + getCSColor("600") + ")",
            fillColor: "rgb(" + getCSColor("600") + ")",
            weight: 5,
            opacity: 0.9,
            fillOpacity: 0.7,
            fill: true,
            smoothFactor: 1,
            dashArray: "10, 8",
            dashOffset: 5
        },
        "dotted_line": {
            color: "rgb(" + getCSColor("600") + ")",
            fillColor: false,
            weight: zoom > 15 ? 4 : 3,
            opacity: 0.8,
            fill: false,
            fillOpacity: 0,
            lineCap: "round",
            lineJoin: "round",
            dashArray: zoom > 15 ? "3, 8" : "2, 6",
            smoothFactor: 1
        }
    };
    
    const hoverStyles = {
        "polygon": {
            color: "rgb(" + getCSColor("700") + ")",
            fillColor: "rgb(" + getCSColor("500") + ")",
            weight: (zoom > 15 ? 2 : 1) + 1,
            opacity: 1,
            fillOpacity: 0.9,
            fill: true,
            lineJoin: "round"
        },
        "polygon_outline": {
            color: "rgb(" + getCSColor("800") + ")",
            fillColor: false,
            weight: (zoom > 15 ? 3 : 2) + 1,
            opacity: 1,
            fillOpacity: 0,
            fill: false,
            lineJoin: "round"
        },
        "polygon_transparent": {
            color: "rgb(" + getCSColor("600") + ")",
            fillColor: "rgb(" + getCSColor("500") + ")",
            weight: 2,
            opacity: 0.7,
            fillOpacity: 0.5,
            fill: true,
            lineJoin: "round"
        },
        "gradient_polygon": {
            color: "rgb(" + getCSColor("700") + ")",
            fillColor: "rgb(" + getCSColor("400") + ")",
            weight: 2,
            opacity: 1,
            fillOpacity: zoom > 15 ? 0.8 : 0.6,
            fill: true,
            lineJoin: "round"
        },
        "pattern_fill": {
            color: "rgb(" + getCSColor("700") + ")",
            fillColor: "rgb(" + getCSColor("600") + ")",
            weight: 3,
            opacity: 0.9,
            fillOpacity: 0.7,
            fill: true,
            lineJoin: "round",
            dashArray: (properties?.id || Math.random()) % 2 === 0 ? "5, 5" : "10, 5"
        },
        "polygon_with_hatch": {
            color: "rgb(" + getCSColor("700") + ")",
            fillColor: "rgb(" + getCSColor("100") + ")",
            weight: 3,
            opacity: 0.9,
            fillOpacity: 0.4,
            fill: true,
            lineJoin: "round",
            dashArray: zoom > 15 ? "8, 12" : "6, 10"
        },
        "solid_line": {
            color: "rgb(" + getCSColor("700") + ")",
            fillColor: false,
            weight: (zoom > 15 ? 4 : 3) + 1,
            opacity: 1,
            fill: false,
            fillOpacity: 0,
            lineCap: "round",
            lineJoin: "round",
            dashArray: null,
            smoothFactor: 1
        },
        "dashed_line": {
            fillColor: "rgb(" + getCSColor("700") + ")",
            color: "rgb(" + getCSColor("700") + ")",
            fill: true,
            fillOpacity: 1,
            opacity: 1,
            weight: 5,
            smoothFactor: 1,
            dashArray: null,
            dashOffset: 5
        },
        "dotted_line": {
            color: "rgb(" + getCSColor("700") + ")",
            fillColor: false,
            weight: (zoom > 15 ? 4 : 3) + 1,
            opacity: 1,
            fill: false,
            fillOpacity: 0,
            lineCap: "round",
            lineJoin: "round",
            dashArray: zoom > 15 ? "3, 8" : "2, 6",
            smoothFactor: 1
        }
    };
    
    const defaultStyle = baseStyles[parserType] || baseStyles["polygon"];
    const hoverStyle = hoverStyles[parserType] || hoverStyles["polygon"];
    return { default: defaultStyle, hover: hoverStyle };
}

function noti_set(id,view_id,link) {
    $("#noti_"+id).hide();
    var count  = $("#notif_count").text();
    $("#notif_count").text(--count);
    $.ajax({
        type:"Post",
        url:PATHFILE+"execute/notification_view/hide",
        data:"id="+id+"&view_id="+view_id+"&token="+WEB_TOKEN,
        cache:"false",
        success:function(html){
            $("#div_noti").html(html);
            $("#noti_"+id).remove();
        }
    });
    link_transfer(link);
}