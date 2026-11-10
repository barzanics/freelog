/* Design sidebar end */

$(document).ready(function () {
    $(document).on("click","#sideToggleBtn", function () {
        let aside = $("aside");
        toggleWithOverlay(aside, "show");
        toggleWithOverlay($(".cinema-seat"), "minimize");
    });

    $(document).on("click",".overlay", function () {
        overlayElements.forEach((item,index) => {
            item.element.removeClass(item.className);
            if (item?.element?.length) $(`#${item.element.attr("id")}`).removeClass(item.className);
            delete overlayElements[index];
            overlayElements = overlayElements.filter(e => e)
        });
        $(".overlay").removeClass("show");
    });

    $(document).on("click","#notifToggleBtn", function () {
        let notificationWrapper = $("#notification_wrapper");
        notificationWrapper.toggleClass("show");
    });
    $(document).on("click","#searchToggleBtn", function () {
        let notificationWrapper = $("#search_wrapper");
        notificationWrapper.toggleClass("show");
    });

    $(document).on("click", function (event) {
        // If the target is not the container or a child of the container, then process
        // the click event for outside of the container.
        if ($(event.target).closest("#notification_wrapper").length === 0 && $(event.target).closest("#notifToggleBtn").length === 0) {
            if ($("#notification_wrapper").hasClass("show")) {
                $("#notification_wrapper").removeClass("show");
            }
        }
        if ($(event.target).closest("#search_wrapper").length === 0 && $(event.target).closest("#searchToggleBtn").length === 0) {
            if ($("#search_wrapper").hasClass("show")) {
                $("#search_wrapper").removeClass("show");
            }
        }
    });
});

$("section.main").on("scroll", () => {
    $(window).trigger("scroll", $(this))
})

/* Main section fix the height start */
/*
$(document).ready(function () {
    mainHeightApply($(".bottom-navbar"), $(".cinema-seat"));
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

    $("section.main").css("margin-bottom", extraHeights + barHeight + "px");
    $("nav.side-navbar").css("padding-bottom", barHeight + "px");
    document.body.removeChild(tag);
}

$(window).on("resize", function () {
    mainHeightApply($(".cinema-seat"), $(".bottom-navbar"));
});

// Observer for main section resize 
$(document).ready(function() {
    const mainSection = document.querySelector("section.main");
    if (mainSection) {
        const observer = new ResizeObserver(entries => {
            // Iterate through the ResizeObserver entries
            for (let entry of entries) {
                mainHeightApply($(".cinema-seat"), $(".bottom-navbar"));
            }
        });
        observer.observe(mainSection);
    }
})
*/

/* Main section fix the height end */

/* Upload Files Script Start*/

var multiFileGallery;
var pictureId = 1;
function multifile(id) {
    var multi_fileInput = document.getElementById("element_" + id + "_file");
    var filePath = multi_fileInput.value;
    var extensions = multi_fileInput.getAttribute("accept");
    var extensionsArray = extensions.split(",");
    var file_extension = filePath.split(".");
    if (!extensionsArray.includes("." + file_extension[file_extension.length - 1])) {
        var multi_extension = document.getElementById("multi_extension_" + id);
        snackbar("element_8543258459", "فرمت فایل ارسالی نامعتبر میباشد.");
        multi_fileInput.value = "";
        return false;
    } else {
        $("#multifile" + id).show();
        $("#multifile_images_" + id).hide();
        $("#multifile" + id).append('<div id="multifile_' + id + '_loader" class="loader-listfile d-flex justify-content-center"><span></span><span></span><span></span><span></span><span></span></div>');
        var formData = new FormData();
        // formData.append("file", $("#element_"+id+"_file")[0].files[0]);
        // formData.append("token", "44d397bf0826e095db2c888cb1e0507a");
        // formData.append("form_id", "223");
        // formData.append("id", id);
        // $.ajax({
        //     url  : PATHFILE+"execute/form/add/upload_multifile",
        //     type : "POST",
        //     data : formData,
        //     processData: false,
        //     contentType: false,
        //     success : function(data) {
        //         $("#multifile_" + id + "_loader").remove();
        //         $("#multifile_images_" + id).show();
        //         $("#multifile_images_" +id).append(data);
        //         $("#element_"+id+"_file").val("");
        //     }
        // });
        new Promise((resolve, reject) => {
            setTimeout(() => {
                resolve(`
<div class="picture-box" id="picture_box_${pictureId}" href="../assets/images/user-panel.png" title="عنوان">
     <figure><img src="../assets/images/user-panel.png" alt="عنوان" title="عنوان"></figure>
     <button type="button" class="picture-box-remove" onclick="removeMultiFilePicture(event, ${pictureId} , ${id})"><i class="fa-solid fa-trash-alt"></i></button>                   
</div>
                `);
            }, 2000);
        }).then((data) => {
            $(document).ready(function () {
                pictureId++;
                if (multiFileGallery) multiFileGallery.destroy();
                multiFileGallery = lightGallery(document.getElementById(`multifile_images_${id}`), {
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
            $("#multifile_" + id + "_loader").remove();
            $("#multifile_images_" + id).show();
            $("#multifile_images_" + id).append(data);
            $("#element_" + id + "_file").val("");
            $("#element_" + id + "_file").trigger("change").trigger("input");
        });
    }
}

function removeMultiFilePicture(event, id, multiFileId) {
    event.preventDefault();
    $(`#picture_box_${id}`).remove();
    multiFileGallery.destroy();
    if (!$(`#multifile_images_${multiFileId}`).children().length) $("#multifile_images_" + multiFileId).hide();
    multiFileGallery = lightGallery(document.getElementById(`multifile_images_${multiFileId}`), {
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
}

function file_delete(id, div_id, file_name) {
    $("." + div_id).remove();
    $("#single_file_result_" + id).hide();
    $("#element_" + id + "_file").val("");
    $("#element_" + id + "_file").trigger("change").trigger("input");
    $("#single_file_" + id).show();
    var str = $("#element_" + id + "_hide").val();
    var res = str.replace("," + file_name + ",", ",");
    $("#element_" + id + "_hide").val(res);
    $("#element_" + id + "_hide").trigger("change").trigger("input");
    $.ajax({
        url: PATHFILE+"execute/form/add/delete_multifile",
        data: "id=" + id + "&file_name=" + file_name + "&token=44d397bf0826e095db2c888cb1e0507a&form_id=223",
        cache: "false",
        type: "Post",
        success: function (html) {
            $("#as").html(html);
        },
    });
}

var listFileGallery;
// function listfile_delete_edit(id, file_name) {
//     $(`#element_${id}_preview`).attr("src", "");
//     $(`#element_${id}_filename`).text(file_name);
//     $(`#single_file_result_${id}`).hide();
//     $("#element" + id + "_drop_area").show();
//     $("#element_" + id + "_hide").val("");
//     $("#" + id + "_hide").val("");
//     listFileGallery.destroy();
// }

function setArchiveFile(event, id) {
    $(`#element_${id}_drop_area`).hide();
    $(`#single_file_result_${id}`).show();
    $(`#element_${id}_preview`).attr("src", $(event.target).attr("src"));
    $(`#element_${id}_filename`).text($(event.target).attr("alt"));
    listFileGallery = lightGallery(document.getElementById(`element_${id}_figure`), {
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
}

function view(path) {
    window.open(path, "", "width=500,height=500,resizable=yes,scrollbars=yes");
}
function location_show(id) {
    $.ajax({
        url: PATHFILE+"execute/form/add/location",
        data: "id=" + id + "&token=44d397bf0826e095db2c888cb1e0507a",
        cache: "false",
        type: "Post",
        success: function (html) {
            $("#content_set_" + id).html(html);
            initialize();
        },
    });
}
function related_show(form_id, form_element_id) {
    option_id = $("#element_" + form_element_id + "_1").val();
    $.ajax({
        url: PATHFILE+"execute/form/add/related",
        data: "form_id=" + form_id + "&form_element_id=" + form_element_id + "&option_id=" + option_id + "&token=44d397bf0826e095db2c888cb1e0507a",
        cache: "false",
        type: "Post",
        success: function (html) {
            if (html != "") {
                console.log(html);
                $("#element_" + form_element_id + "_2").html(html);
                $(".div_" + form_element_id).show();
            } else {
                $(".div_" + form_element_id).hide();
            }
        },
    });
}

function multifile_modal_image(e, form_element_id) {
    $(".multi_image_" + form_element_id).attr("src", e.getAttribute("src"));
}

/* Upload Files Script End */

/* Map location start */
let initializedMaps = [];
function initLocation(id, lat, lng, zoom, location_address_type, location_address_field, isExternal = false, map_search, dissabled, path_file, mapLoadedCallback = () => {}, preventReinit = false, options = {}, cartable_view_status = true) {
    var map;
    if (preventReinit) {
        if (initializedMaps.includes(`map_set_${id}`)) return;
        // if isn't initialized...
        initializedMaps.push(`map_set_${id}`);
    }
    map = L.map(`map_set_${id}`, {
        measureControl: cartable_view_status,
        zoomControl: false,
        zoomsliderControl: false,
        attributionControl: false,
        scrollWheelZoom: cartable_view_status,
        dragging: cartable_view_status
    }).setView([lat, lng], zoom);
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
        map.on("dragend zoomend", function (e) {
            set_marker(map.getCenter().lat, map.getCenter().lng);
            $(`#location_internal_latlng_${id}`).html(map.getCenter().lat + " , " + map.getCenter().lng);
            $(`#element_${id}`).html(map.getCenter().lat + " , " + map.getCenter().lng);
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
                            $("#" + location_address_field).trigger("change").trigger("input");
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
                            $("#" + location_address_field).trigger("change").trigger("input");
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
                    var {lat,lng} = e.latlng;
                    set_marker(lat,lng)
                    $(`#location_internal_latlng_${id}`).html(lat + "-" + lng);
                    if (isExternal) {
                        $(`#foreign_location_${id}`).val(lat + "-" + lng);
                        $(`#foreign_location_${id}`).trigger("change").trigger("input");
                    }
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
        if (themeName === "dark") {
            $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
        } else {
            $(".leaflet-map-pane").css("filter", "none");
        }
    });

    function set_marker(lat, lon) {
        $(`#element_${id}_lat`).val(lat);
        $(`#element_${id}_lat`).trigger("change").trigger("input");
        $(`#element_${id}_lan`).val(lon);
        $(`#element_${id}_lan`).trigger("change").trigger("input");
        $(`#element_${id}`).val(lat + "," + lon);
        $(`#element_${id}`).trigger("change").trigger("input");
    }

    // Add Geo Json layers
    if (options?.geojson_var_name?.length) {
        addGeojsonLayer(window[options.geojson_var_name], map, {
            geo_data_1_field: options.geo_data_1_field,
            geo_data_2_field: options.geo_data_2_field,
            geo_data_3_field: options.geo_data_3_field,
            geo_data_1: options.geo_data_1,
            geo_data_2: options.geo_data_2,
            geo_data_3: options.geo_data_3,
        });
    }
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
                        color: `rgb(${cs.getPropertyValue("--rgb-blue-700")})`,
                        fillColor: `rgb(${cs.getPropertyValue("--rgb-blue-700")})`,
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
                    [$(`#${options.geo_data_1_field}`).val(layer.feature.properties[options.geo_data_1]), dataPlaced = true];
                if (options.geo_data_2_field?.length && options.geo_data_2?.length) 
                    [$(`#${options.geo_data_2_field}`).val(layer.feature.properties[options.geo_data_2]), dataPlaced = true];
                if (options.geo_data_3_field?.length && options.geo_data_3?.length) 
                    [$(`#${options.geo_data_3_field}`).val(layer.feature.properties[options.geo_data_3]), dataPlaced = true];
                if (dataPlaced) {snackbar("element_geo_84394", "داده ای از این لایه دریافت شده و در فیلد مورد نظر قرار گرفت!", "success", {hasIcon: true})}
            }
        })
    })
}
/* Map location end */

/* Draw Map location start */
let initializedDrawMaps = [];
function initLocationDraw(id, lat, lng, zoom, location_address_type, location_address_field, isExternal = false, map_search, dissabled, path_file, mapLoadedCallback = () => {}, preventReinit = false, areaInput = "", perimeterInput = "", distanceInput = "") {
    console.log(id, lat, lng, zoom, location_address_type, location_address_field, isExternal, map_search, dissabled, path_file, mapLoadedCallback, preventReinit, areaInput, perimeterInput, distanceInput)
    var map;
    if (preventReinit) {
        if (initializedDrawMaps.includes(`map_set_${id}`)) return;
        // if isn't initialized...
        initializedDrawMaps.push(`map_set_${id}`);
    }
    map = L.map(`map_set_${id}`, {
        measureControl: true,
        zoomControl: false,
        zoomsliderControl: false,
        attributionControl: false,
    }).setView([lat, lng], zoom);
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
                            $("#" + location_address_field).trigger("change").trigger("input");
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
                            $("#" + location_address_field).trigger("change").trigger("input");
                        });
                }
            }
        });
        var timeoutLocation;
        var location_button = document.querySelector(`#location_button_${id}`);
        location_button.addEventListener("click", function (e) {
            e.preventDefault();
            map.locate({ setView: true, maxZoom: 16 });
            if (timeoutLocation) clearTimeout(timeoutLocation);
            timeoutLocation = setTimeout(() => {
                location_button.classList.add("locate-loader")
                map.on("locationfound", function (e) {
                    location_button.classList.remove("locate-loader")
                    map.setView(e.latlng, 14);
                    var {lat,lng} = e.latlng;
                    set_marker(lat,lng)
                    $(`#location_internal_latlng_${id}`).html(lat + "-" + lng);
                    if (isExternal) {
                        $(`#foreign_location_${id}`).val(lat + "-" + lng);
                    }
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
        if (themeName === "dark") {
            $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
        } else {
            $(".leaflet-map-pane").css("filter", "none");
        }
    });

    function set_marker(lat, lon) {
        $(`#element_${id}_lat`).val(lat);
        $(`#element_${id}_lat`).trigger("change").trigger("input");
        $(`#element_${id}_lan`).val(lon);
        $(`#element_${id}_lan`).trigger("change").trigger("input");
        $(`#element_${id}`).val(lat + "," + lon);
        $(`#element_${id}`).trigger("change").trigger("input");
    }

    // Draw Map Start
    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    var labelGroup = new L.FeatureGroup(); // گروه جدید برای ذخیره برچسب‌ها
    map.addLayer(labelGroup);

    var drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems,
        },
        draw: {
            polygon: {
                shapeOptions: {
                    color: 'rgb(var(--rgb-first))', // رنگ مرز چندضلعی
                    weight: 4,
                    opacity: 0.8,
                    fillColor: 'rgb(var(--rgb-first))', // رنگ پر کردن چندضلعی
                    fillOpacity: 0.4
                }
            },
            polyline: {
                shapeOptions: {
                    color: 'rgb(var(--rgb-first))', // رنگ مرز چندضلعی
                    weight: 4,
                    opacity: 0.8,
                    fillColor: 'rgb(var(--rgb-first))', // رنگ پر کردن چندضلعی
                    fillOpacity: 0.4
                }
            },
            rectangle: false,
            circle: false,
            marker: false,
            circlemarker: false
        }
    });
    map.addControl(drawControl);

    // تابع برای تبدیل واحد
    function formatMetric(value, type) {
        if (type === 'area') {
            if (value > 1e6) { // بیشتر از 1 کیلومتر مربع
                return (value / 1e6).toFixed(2) + " کیلومتر مربع";
            } else {
                return value.toFixed(2) + " متر مربع";
            }
        } else if (type === 'distance') {
            if (value > 1000) { // بیشتر از 1 کیلومتر
                return (value / 1000).toFixed(2) + " کیلومتر";
            } else {
                return value.toFixed(2) + " متر";
            }
        }
        return value.toFixed(2) + " متر"; // پیش‌فرض
    }

    map.on(L.Draw.Event.CREATED, function (event) {
        console.log("created")
        var layer = event.layer;
        drawnItems.addLayer(layer);

        if (layer instanceof L.Polygon) {
            var latLngs = layer.getLatLngs()[0];
            var area = L.GeometryUtil.geodesicArea(latLngs); // مساحت به متر مربع
            var perimeter = 0;
            for (var i = 0; i < latLngs.length; i++) {
                var point1 = latLngs[i];
                var point2 = latLngs[(i + 1) % latLngs.length];
                perimeter += map.distance(point1, point2); // محیط به متر
            }

            if (document.getElementById(areaInput)) document.getElementById(areaInput).value = formatMetric(area, 'area');
            if (document.getElementById(perimeterInput)) document.getElementById(perimeterInput).value = formatMetric(perimeter, 'distance');
            if (document.getElementById(distanceInput)) document.getElementById(distanceInput).value = "";

            var center = layer.getBounds().getCenter();
            var label = L.marker(center, {
                icon: L.divIcon({
                    className: '',
                    html: `
                        <div class="leaflet-custom-label">
                            مساحت: ${formatMetric(area, 'area')}<br>محیط: ${formatMetric(perimeter, 'distance')}
                        </div>`
                })
            });
            labelGroup.addLayer(label);
            layer.label = label;

        } else if (layer instanceof L.Polyline) {
            var latLngs = layer.getLatLngs();
            var totalDistance = 0;
            layer.labels = []; // اطمینان از اینکه آرایه برچسب‌ها خالی است

            for (var i = 0; i < latLngs.length - 1; i++) {
                var point1 = latLngs[i];
                var point2 = latLngs[i + 1];
                var segmentDistance = map.distance(point1, point2);

                var middlePoint = L.latLng(
                    (point1.lat + point2.lat) / 2,
                    (point1.lng + point2.lng) / 2
                );
                var segmentLabel = L.marker(middlePoint, {
                    icon: L.divIcon({
                        className: '',
                        html: `
                            <div class="leaflet-custom-label">
                                مسافت: ${formatMetric(segmentDistance, 'distance')}
                            </div>
                        `
                    })
        
                });
                
                labelGroup.addLayer(segmentLabel);
                segmentLabel.addTo(map);

                layer.labels.push(segmentLabel);

                totalDistance += segmentDistance;
            }

            if (document.getElementById(areaInput)) document.getElementById(areaInput).value = "";
            if (document.getElementById(perimeterInput)) document.getElementById(perimeterInput).value = "";
            if (document.getElementById(distanceInput)) document.getElementById(distanceInput).value = formatMetric(totalDistance, 'distance');
        }
    });

    // رویداد حذف شکل‌ها
    map.on('draw:deleted', function (event) {
        console.log("deleted")
        if (document.getElementById(areaInput)) document.getElementById(areaInput).value = '';
        if (document.getElementById(perimeterInput)) document.getElementById(perimeterInput).value = '';
        if (document.getElementById(distanceInput)) document.getElementById(distanceInput).value = '';

        event.layers.eachLayer(function (layer) {
            if (layer.label) {
                map.removeLayer(layer.label);
                labelGroup.removeLayer(layer.label);
            }
            if (layer.labels) {
                layer.labels.forEach(function (label) {
                    map.removeLayer(label);
                    labelGroup.removeLayer(label);
                });
            }
        });
    });

    // رویداد ویرایش شکل‌ها
    map.on('draw:edited', function (event) {
        console.log("edited")
        event.layers.eachLayer(function (layer) {
            if (layer instanceof L.Polygon) {
                // محاسبه مجدد مساحت و محیط
                var latLngs = layer.getLatLngs()[0];
                var area = L.GeometryUtil.geodesicArea(latLngs); // مساحت به متر مربع
                var perimeter = 0;
                for (var i = 0; i < latLngs.length; i++) {
                    var point1 = latLngs[i];
                    var point2 = latLngs[(i + 1) % latLngs.length];
                    perimeter += map.distance(point1, point2); // محیط به متر
                }

                // به‌روزرسانی برچسب‌ها
                var center = layer.getBounds().getCenter();
                if (layer.label) {
                    layer.label.setLatLng(center);
                    layer.label.setIcon(L.divIcon({
                        className: '',
                        html: `
                            <div class="leaflet-custom-label">
                                مساحت: ${formatMetric(area, 'area')}<br>محیط: ${formatMetric(perimeter, 'distance')}
                            </div>`
                    }));
                } else {
                    var newLabel = L.marker(center, {
                        icon: L.divIcon({
                            className: '',
                            html: `
                                <div class="leaflet-custom-label">
                                    مساحت: ${formatMetric(area, 'area')}<br>محیط: ${formatMetric(perimeter, 'distance')}
                                </div>`
                        })
                    });
                    labelGroup.addLayer(newLabel);
                    layer.label = newLabel;
                }

                if (document.getElementById(areaInput)) document.getElementById(areaInput).value = formatMetric(area, 'area');
                if (document.getElementById(perimeterInput)) document.getElementById(perimeterInput).value = formatMetric(perimeter, 'distance');
            } else if (layer instanceof L.Polyline) {
                // محاسبه مجدد مسافت
                var latLngs = layer.getLatLngs();
                var totalDistance = 0;

                if (layer.labels) {
                    // پاک کردن برچسب‌های قدیمی
                    layer.labels.forEach(function (label) {
                        map.removeLayer(label);
                        labelGroup.removeLayer(label);
                    });
                    layer.labels = [];
                } else {
                    layer.labels = [];
                }

                for (var i = 0; i < latLngs.length - 1; i++) {
                    var point1 = latLngs[i];
                    var point2 = latLngs[i + 1];
                    var segmentDistance = map.distance(point1, point2);

                    totalDistance += segmentDistance;

                    // ایجاد برچسب جدید
                    var middlePoint = L.latLng(
                        (point1.lat + point2.lat) / 2,
                        (point1.lng + point2.lng) / 2
                    );
                    var newSegmentLabel = L.marker(middlePoint, {
                        icon: L.divIcon({
                            className: '',
                            html: `
                                <div class="leaflet-custom-label">
                                    مسافت: ${formatMetric(segmentDistance, 'distance')}
                                </div>
                            `
                        })
                    });
                    labelGroup.addLayer(newSegmentLabel);
                    layer.labels.push(newSegmentLabel);
                }
                if (document.getElementById(distanceInput)) document.getElementById(distanceInput).value = formatMetric(totalDistance, 'distance');
            }
        });
    });

    // Draw Map end
}
/* Draw Map location end */

/* Tabindexes for modals */
$(document).ready(function () {
    $("[data-bs-toggle='modal']").on("focus", function () {
        $(this).on("keydown", function (e) {
            if (+e.keyCode === 32) {
                e.preventDefault();
                $($(this).data("bs-target")).modal("show");
            }
        });
    });
});
// e.target.checked = !e.target.checked
function spaceToClick(e) {
    console.log(e);
    if (+e.keyCode === 32) {
        e.preventDefault();
        $(e.target).click();
        if (e.target.tagName.toLowerCase() === "label") {
            var labelFor = e.target.getAttribute("for");
            var targetEl = $("#" + labelFor);
            if (targetEl.is(":checkbox")) {
                console.log("toggling checkbox");
                targetEl.prop("checked", !targetEl.prop("checked"));
            }
        }
    }
}
function enterToClick(e) {
    console.log(e);
    if (+e.keyCode === 13) {
        e.preventDefault();
        $(e.target).click();
        if (e.target.tagName.toLowerCase() === "label") {
            var labelFor = e.target.getAttribute("for");
            var targetEl = $("#" + labelFor);
            if (targetEl.is(":checkbox")) {
                console.log("toggling checkbox");
                targetEl.prop("checked", !targetEl.prop("checked"));
            }
        }
    }
}

function toggleCheckbox(e) {
    console.log("toggling ...");
    if (e.key === "Enter") {
        e.preventDefault();
        $(e.target).click();
        if (e.target.tagName.toLowerCase() === "label") {
            var labelFor = e.target.getAttribute("for");
            var targetEl = $("#" + labelFor);
            if (targetEl.is(":checkbox")) {
                console.log("toggling checkbox");
                targetEl.prop("checked", !targetEl.prop("checked"));
            }
        }
    }
}

$(document).ready(function () {
    $("input[type='checkbox']").on("focus", function () {
        $(this).on("keydown", function () { });
    });
});

function enterOrSpaceToClick(e) {
    // space key
    if (+e.keyCode === 32) {
        e.preventDefault();
        $(e.target).click();
    }
    // enter key
    if (+e.keyCode === 13) {
        e.preventDefault();
        $(e.target).click();
    }
}

function spaceToShowLightGallery(e) {
    if (+e.keyCode === 32) {
        e.preventDefault();
        $(e.target).click();
    }
}
var full_address;

function routeHelper() {
    var origin_marker;
    var goal_marker;
    var waypoint1;
    var waypoint2;
    var distance;
    var duration;
    var routingFieldId;

    var cs = getComputedStyle(document.querySelector("body"));
    var pLineGroup = L.layerGroup();
    var coordsArray = [];
    var route_origin;
    var route_goal;
    function origin_getAddress(lat, lng) {
        fetch("https://map.ir/reverse/fast-reverse?lat=" + lat + "&lon=" + lng, {
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
                $("#origin_routing_input").val(data.postal_address);
            });
    }

    function goal_getAddress(lat, lng) {
        fetch("https://map.ir/reverse/fast-reverse?lat=" + lat + "&lon=" + lng, {
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
                $("#goal_routing_input").val(data.postal_address);
            });
    }

    function decodePolyline(encoded) {
        const points = [];
        let index = 0,
            lat = 0,
            lng = 0;

        while (index < encoded.length) {
            let b,
                shift = 0,
                result = 0;
            do {
                b = encoded.charAt(index++).charCodeAt(0) - 63;
                result |= (b & 0x1f) << shift;
                shift += 5;
            } while (b >= 0x20);
            lat += (result & 1) === 1 ? ~(result >> 1) : result >> 1;

            shift = 0;
            result = 0;
            do {
                b = encoded.charAt(index++).charCodeAt(0) - 63;
                result |= (b & 0x1f) << shift;
                shift += 5;
            } while (b >= 0x20);
            lng += (result & 1) === 1 ? ~(result >> 1) : result >> 1;

            points.push([lat * 1e-5, lng * 1e-5]);
        }

        return points;
    }

    function getRoutinColor(routingType) {
        let routingColor = "red";
        if (routingType === "route/v1/driving") {
            routingColor = "black";
        } else if (routingType === "tarh/v1/driving") {
            routingColor = "blue";
        } else if (routingType === "zojofard/v1/driving") {
            routingColor = "green";
        } else if (routingType === "bicycle/v1/driving") {
            routingColor = "brown";
        } else {
            routingColor = "purple";
        }
        return routingColor;
    }

    var routeLayerLines = [];
    var routeLayerOutLines = [];
    function route(coordsArray, origin_latlng, destination_latlng, space, origin_address, destination_address,id,addressType = "small_address") {
        if (coordsArray.length < 2) {
            $("#sidebarRoutingMapBtn").show();
            return;
        }

        let cords = "";
        coordsArray.forEach(function (coord, index) {
            cords += `${coord.lng},${coord.lat}`;
            if (index !== coordsArray.length - 1) {
                cords += `;`;
            }
        });

        // var routeColors=["#5d5ded", "#4a9aea", "#4aea5d"]
        var routeColor = "rgb(" + cs.getPropertyValue("--rgb-first") + ")";

        var driver_data = $(".routing-box-item-button").filter(".active").attr("data-driver");
        if (driver_data == undefined) driver_data = "route";
        $.ajax({
            url: `https://map.ir/routes/${driver_data}/v1/driving/${cords}`,
            data: {
                steps: true,
                alternatives: true,
            },
            beforeSend: function (request) {
                request.setRequestHeader(
                    "x-api-key", API_TOKEN
                );
            },
            success: function (data, status) {
                const routes = data.routes;
                if (data.routes) {
                    $("#sidebarRoutingMapBtn").hide();
                    waypoint1 = data.waypoints[0].name !== "" ? data.waypoints[0].name : DEFAULTTITLE;
                    waypoint2 = data.waypoints[1].name !== "" ? data.waypoints[1].name : DEFAULTTITLE;

                    $.each(routes, function (idxR, val) {
                        routeLayerOutLines[idxR] = [];
                        routeLayerLines[idxR] = [];
                        // for each route (may more than one path be available)
                        $.each(val.legs, function (idx, leg) {
                            distance = formatDistance(leg.distance);
                            duration = formatTime(leg.duration);
                            console.log("origin_latlng",origin_latlng);
                            if(origin_latlng !== '' || destination_latlng !== '' || space !== '' || origin_address !== '' || destination_address !== '')
                            {
                                $("#element_" + routingFieldId + "_origin_lan").val(data.waypoints[0].location[0]).trigger("change").trigger("input");;
                                $("#element_" + routingFieldId + "_origin_lat").val(data.waypoints[0].location[1]).trigger("change").trigger("input");;
                                $("#element_" + routingFieldId + "_destination_lan").val(data.waypoints[1].location[0]).trigger("change").trigger("input");;
                                $("#element_" + routingFieldId + "_destination_lat").val(data.waypoints[1].location[1]).trigger("change").trigger("input");;
                                if(origin_latlng !== "") $("#" + origin_latlng).val(data.waypoints[0].location[0] + "-" + data.waypoints[0].location[1]).trigger("change").trigger("input");
                                if(destination_latlng !== "") $("#" + destination_latlng).val(data.waypoints[1].location[0] + "-" + data.waypoints[1].location[1]).trigger("change").trigger("input");
                                if(space !== "") $("#" + space).val(distance).trigger("change").trigger("input");
                                console.log(addressType)
                                if (addressType == "big_address") {
                                    if(origin_address !== "") {
                                        fetch("https://map.ir/reverse?lat=" + data.waypoints[0].location[1] + "&lon=" + data.waypoints[0].location[0], {
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
                                                console.log(data)
                                                $("#" + origin_address).val(data.address);
                                                $("#" + origin_address).trigger("change").trigger("input");
                                            });
                                    }
                                    if(destination_address !== "") {
                                        fetch("https://map.ir/reverse?lat=" + data.waypoints[1].location[1] + "&lon=" + data.waypoints[1].location[0], {
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
                                                $("#" + destination_address).val(data.address);
                                                $("#" + destination_address).trigger("change").trigger("input");
                                            });
                                    }
                                } else {
                                    if(origin_address !== ""){
                                        fetch("https://map.ir/reverse?lat=" + data.waypoints[0].location[1] + "&lon=" + data.waypoints[0].location[0], {
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
                                                $("#" + origin_address).val(data.postal_address);
                                                $("#" + origin_address).trigger("change").trigger("input");
                                            });
                                    }
                                    if(destination_address !== ""){
                                    
                                        fetch("https://map.ir/reverse?lat=" + data.waypoints[1].location[1] + "&lon=" + data.waypoints[1].location[0], {
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
                                                $("#" + destination_address).val(data.postal_address);
                                                $("#" + destination_address).trigger("change").trigger("input");
                                            });
                                    }
                                }
                            }
                            $.each(leg.steps, function (idx, val) {
                                // for each line in the path
                                // Decoding line points using leaflet  geometry plugin
                                let lineLocations = decodePolyline(val.geometry);
                                // paint the lines
                                linesOption = {
                                    color: routeColor,
                                    weight: 5,
                                    opacity: 0.8,
                                    smoothFactor: 1,
                                    dashArray: "10, 10",
                                    dashOffset: 5,
                                };
                                if (idxR === 0) {
                                    var stepOutLine = L.polyline(lineLocations, { ...linesOption, opacity: 0.3, weight: 14 }).addTo(pLineGroup);
                                    var stepLine = L.polyline(lineLocations, linesOption).addTo(pLineGroup);
                                } else {
                                    var stepOutLine = L.polyline(lineLocations, { ...linesOption, opacity: 0.3, weight: 14 });
                                    var stepLine = L.polyline(lineLocations, linesOption);
                                }

                                routeLayerOutLines[idxR].push(stepOutLine);
                                routeLayerLines[idxR].push(stepLine);
                                // map.fitBounds(stepLine.getBounds())
                            });
                            // add the line to map (our map instance)
                            pLineGroup.addTo(map);
                        });
                    });
                    processRoutesEvent();
                    var startLatLng = L.latLng(coordsArray[0]);
                    var endLatLng = L.latLng(coordsArray[1]);
                    var bounds = L.latLngBounds(startLatLng, endLatLng);
                    map.fitBounds(bounds);
                    $(".route-page-places-items").find("[data-route-id]").first().addClass("active");
                }
            },
        });

        function processRoutesEvent() {
            $("[data-route-id]").on("click", function () {
                $(this).addClass("active").siblings().removeClass("active");
                var routeId = $(this).data("route-id");
                pLineGroup.removeFrom(map);
                routeLayerOutLines.forEach((layerOutLine, idx) => {
                    layerOutLine.forEach((outline) => {
                        outline.options.color = routeColor;
                        if (idx === +routeId) {
                            // outline.options.color="green"
                            outline.addTo(pLineGroup);
                        } else {
                            outline.removeFrom(pLineGroup);
                        }
                    });
                });
                routeLayerLines.forEach((layerLine, idx) => {
                    layerLine.forEach((line) => {
                        line.options.color = routeColor;
                        if (idx === +routeId) {
                            // outline.options.color="green"
                            line.addTo(pLineGroup);
                        } else {
                            line.removeFrom(pLineGroup);
                        }
                    });
                });
                pLineGroup.addTo(map);
            });

            $("[data-route-id]").on("mouseenter", function () {
                var routeId = $(this).data("route-id");
                pLineGroup.removeFrom(map);
                routeLayerOutLines.forEach((layerOutLine, idx) => {
                    layerOutLine.forEach((outline) => {
                        outline.options.color = routeColor;
                        if (idx === +routeId) {
                            // outline.options.color="green"
                            outline.addTo(pLineGroup);
                        } else {
                            outline.removeFrom(pLineGroup);
                        }
                    });
                });
                routeLayerLines.forEach((layerLine, idx) => {
                    layerLine.forEach((line) => {
                        line.options.color = routeColor;
                        if (idx === +routeId) {
                            // outline.options.color="green"
                            line.addTo(pLineGroup);
                        } else {
                            line.removeFrom(pLineGroup);
                        }
                    });
                });
                pLineGroup.addTo(map);
            });

            $("[data-route-id]").on("mouseleave", function () {
                $("[data-route-id].active").each(function () {
                    var routeId = $(this).data("route-id");
                    pLineGroup.removeFrom(map);
                    routeLayerOutLines.forEach((layerOutLine, idx) => {
                        layerOutLine.forEach((outline) => {
                            outline.options.color = routeColor;
                            if (idx === +routeId) {
                                // outline.options.color="green"
                                outline.addTo(pLineGroup);
                            } else {
                                outline.removeFrom(pLineGroup);
                            }
                        });
                    });
                    routeLayerLines.forEach((layerLine, idx) => {
                        layerLine.forEach((line) => {
                            line.options.color = routeColor;
                            if (idx === +routeId) {
                                // outline.options.color="green"
                                line.addTo(pLineGroup);
                            } else {
                                line.removeFrom(pLineGroup);
                            }
                        });
                    });
                    pLineGroup.addTo(map);
                });
            });
        }
    }

    $(document).on("themeChanged", function (event, { themeName }) {
        var routeColor = "rgb(" + cs.getPropertyValue("--rgb-first") + ")";
        if (coordsArray.length > 1) {
            var routeId = 0;
            pLineGroup.removeFrom(map);
            routeLayerOutLines.forEach((layerOutLine, idx) => {
                layerOutLine.forEach((outline) => {
                    outline.options.color = routeColor;
                    if (idx === +routeId) {
                        // outline.options.color="green"
                        outline.addTo(pLineGroup);
                    } else {
                        outline.removeFrom(pLineGroup);
                    }
                });
            });
            routeLayerLines.forEach((layerLine, idx) => {
                layerLine.forEach((line) => {
                    line.options.color = routeColor;
                    if (idx === +routeId) {
                        // outline.options.color="green"
                        line.addTo(pLineGroup);
                    } else {
                        line.removeFrom(pLineGroup);
                    }
                });
            });
            pLineGroup.addTo(map);
        }
    });

    function clearRoute() {
        if (pLineGroup) pLineGroup.removeFrom(map);
        if (origin_marker) map.removeLayer(origin_marker);
        if (goal_marker) map.removeLayer(goal_marker);
        $("#origin_routing_input").val("");
        $("#goal_routing_input").val("");
        pLineGroup = L.layerGroup();
        coordsArray = [];
    }

    function clearRouteDraw() {
        pLineGroup.removeFrom(map);
        pLineGroup = L.layerGroup();
        coordsArray = [];
    }

    function drawMarker(map, point, goal_icon) {
        if (goal_marker) map.removeLayer(goal_marker);
        goal_marker = L.marker([point.lat, point.lng], {
            icon: goal_icon,
        }).addTo(map);
        var goal_latlng = { lat: map.getCenter().lat, lng: map.getCenter().lng };
        clickMapHandler(goal_latlng);
    }

    function removeRoute() {
        pLineGroup.removeFrom(map);
        pLineGroup = L.layerGroup();
    }

    function clearMarkers() {
        app.removeMarkers({
            group: app.groups.features.markers,
        });
    }

    var pushed = false;
    var unshifted = false;
    function clickMapHandler(latlng, pushing = true,origin_latlng = '',destination_latlng = '',space = '',origin_address = '',destination_address = '',id = '',addressType = 'small_address') {
        if (coordsArray.length > 1) {
            clearRouteDraw();
        }
        // first, check the goal route is not equal to origin route!
        // if (!coordsArray.filter(c => c.lat==latlng.lat&&c.lng==latlng.lng).length) {
        if (pushing) {
            if (pushed) {
                coordsArray.pop();
                coordsArray.push(latlng);
            } else {
                coordsArray.push(latlng);
            }
            pushed = true;
            unshifted = false;
        } else {
            if (unshifted) {
                coordsArray.shift();
                coordsArray.unshift(latlng);
            } else {
                coordsArray.unshift(latlng);
            }
            unshifted = true;
            pushed = false;
        }
        // }
        route(coordsArray,origin_latlng,destination_latlng,space,origin_address,destination_address,id,addressType);
        return true;
    }

    function setGoalMarker(e,originLatlng = "",destination_latlng = "",space = "",origin_address = "",destination_address = "",id = "",addressType = "small_address") {
        var newLatLng = e.target.getLatLng();
        route_goal = { lat: newLatLng.lat, lng: newLatLng.lng };
        clearRoute();
        // process of origin route
        var origin_icon = L.icon({
            iconUrl: PATHFILE + "assets/images/maps/markers/origin-marker.png",
            iconSize: [27, 41],
        });
        if (origin_marker) {
            map.removeLayer(origin_marker);
            var existingOTooltip = origin_marker.getTooltip();
            origin_marker = L.marker(
                [route_origin.lat, route_origin.lng],
                origin_marker.options ?? {
                    icon: origin_icon,
                    draggable: true,
                }
            ).addTo(map);
            if (existingOTooltip) origin_marker.bindTooltip(existingOTooltip).openTooltip();
            origin_marker.on("dragend", (e) => setOriginMarker(e,originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType));
        }
        var origin_latlng = {
            lat: route_origin.lat,
            lng: route_origin.lng,
        };
        clickMapHandler(origin_latlng, false, originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType);
        origin_getAddress(route_origin.lat, route_origin.lng);

        // process of goal route
        var goal_icon = L.icon({
            iconUrl: PATHFILE + "assets/images/maps/markers/goal-marker.png",
            iconSize: [27, 41],
        });
        if (goal_marker) {
            map.removeLayer(goal_marker);
            var existingGTooltip = goal_marker.getTooltip();
            goal_marker = L.marker(
                [route_goal.lat, route_goal.lng],
                goal_marker.options ?? {
                    icon: goal_icon,
                    draggable: true,
                }
            ).addTo(map);
            if (existingGTooltip) goal_marker.bindTooltip(existingGTooltip).openTooltip();
            goal_marker.on("dragend", (e) => setGoalMarker(e, originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType));
        }
        var goal_latlng = { lat: route_goal.lat, lng: route_goal.lng };
        clickMapHandler(goal_latlng, true, originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType);
        goal_getAddress(route_goal.lat, route_goal.lng);
    }

    function setOriginMarker(e, originLatlng = "",destination_latlng = "",space = "",origin_address = "",destination_address = "",id = "",addressType = "small_address") {
        var newLatLng = e.target.getLatLng();
        route_origin = { lat: newLatLng.lat, lng: newLatLng.lng };
        clearRoute();
        // process of origin route
        var origin_icon = L.icon({
            iconUrl: PATHFILE + "assets/images/maps/markers/origin-marker.png",
            iconSize: [27, 41],
        });
        if (origin_marker) {
            map.removeLayer(origin_marker);
            var existingOTooltip = origin_marker.getTooltip();
            origin_marker = L.marker(
                [route_origin.lat, route_origin.lng],
                origin_marker.options ?? {
                    icon: origin_icon,
                    draggable: true,
                }
            ).addTo(map);
            if (existingOTooltip) origin_marker.bindTooltip(existingOTooltip).openTooltip();
            origin_marker.on("dragend", (e) => setOriginMarker(e,originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType));
        }
        var origin_latlng = {
            lat: route_origin.lat,
            lng: route_origin.lng,
        };
        clickMapHandler(origin_latlng, false, originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType);
        origin_getAddress(route_origin.lat, route_origin.lng);

        // process of goal route
        var goal_icon = L.icon({
            iconUrl: PATHFILE + "assets/images/maps/markers/goal-marker.png",
            iconSize: [27, 41],
        });
        if (goal_marker) {
            map.removeLayer(goal_marker);
            var existingGTooltip = goal_marker.getTooltip();
            goal_marker = L.marker(
                [route_goal.lat, route_goal.lng],
                goal_marker.options ?? {
                    icon: goal_icon,
                    draggable: true,
                }
            ).addTo(map);
            if (existingGTooltip) goal_marker.bindTooltip(existingGTooltip).openTooltip();
            goal_marker.on("dragend", (e) => setGoalMarker(e,originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType));
        }
        var goal_latlng = { lat: route_goal.lat, lng: route_goal.lng };
        clickMapHandler(goal_latlng, true, originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType);
        goal_getAddress(route_goal.lat, route_goal.lng);
    }

    function routingFromHere(e) {
        // مبدا
        // process of origin route
        if (coordsArray.length > 1) clearRoute();
        if (!$("#routing-page").hasClass("active")) {
            $("#routing-page").fadeIn().show().addClass("active").siblings().fadeOut().hide().removeClass("active");
        }
        route_origin = e.latlng;
        var origin_icon = L.icon({
            iconUrl: PATHFILE + "assets/images/maps/markers/origin-marker.png",
            iconSize: [27, 41],
        });
        if (origin_marker) map.removeLayer(origin_marker);
        origin_marker = L.marker([route_origin.lat, route_origin.lng], {
            icon: origin_icon,
            draggable: true,
        }).addTo(map);
        origin_marker.on("dragend", setOriginMarker);
        var origin_latlng = {
            lat: e.latlng.lat,
            lng: e.latlng.lng,
        };
        clickMapHandler(origin_latlng, false);
        // ["service-type", "show-alternatives", "routing-overview"].forEach(function (item, idx) {
        //     $(`#${item}`).change(function () {
        //         clearRoute()
        //         route(coordsArray)
        //     })
        // })
        origin_getAddress(route_origin.lat, route_origin.lng);
        if (coordsArray.length > 1) {
            $(".marker_center").hide();
            $(".routing-button").removeClass("active");
            $(".leaflet-control-container").show();
        } else {
            $(".marker_center").show();
            $(".routing-button").text("انتخاب مقصد");
            $(".routing-button").attr("data-status", "goal");
            $(".routing-button").addClass("active");
            $(".leaflet-control-container").hide();
        }
    }

    function routingToHere(e) {
        // مقصد
        // process of goal route
        if (coordsArray.length > 1) clearRoute();
        route_goal = e.latlng;
        var goal_icon = L.icon({
            iconUrl: PATHFILE + "assets/images/maps/markers/goal-marker.png",
            iconSize: [27, 41],
        });
        if (goal_marker) map.removeLayer(goal_marker);
        goal_marker = L.marker([route_goal.lat, route_goal.lng], {
            icon: goal_icon,
            draggable: true,
        }).addTo(map);
        goal_marker.on("dragend", setGoalMarker);
        var goal_latlng = { lat: e.latlng.lat, lng: e.latlng.lng };
        clickMapHandler(goal_latlng, true);
        if (coordsArray.length > 1) {
            // ["service-type", "show-alternatives", "routing-overview"].forEach(function (item, idx) {
            //     $(`#${item}`).change(function () {
            //         clearRoute()
            //         route(coordsArray)
            //     })
            // })
            goal_getAddress(route_goal.lat, route_goal.lng);
            $(".routing-button").attr("data-status", "origin");
            $(".route-page-places-items").text("");
            $(".marker_center").hide();
            $(".routing-button").removeClass("active");
            $(".leaflet-control-container").show();
        } else {
            $(".marker_center").show();
            $(".routing-button").text("انتخاب مبدا");
            $(".routing-button").attr("data-status", "origin");
            $(".routing-button").addClass("active");
        }
    }

    function formatDistance(meters) {
        let units = "متر";
        let kilometers = meters / 1000;

        if (kilometers > 1) {
            units = "کیلومتر";
            return `${kilometers.toFixed(2)} ${units}`;
        } else {
            return `${meters} ${units}`;
        }
    }

    function formatTime(secondsArg) {
        let units = "ثانیه";
        let seconds = Math.round(secondsArg);
        let minutes = Math.round(Math.floor(seconds / 60));
        let hours = Math.round(Math.floor(minutes / 60));
        let days = Math.round(Math.floor(hours / 24));
        let minutesZero = Math.round(minutes % 60).toString().length < 2 ? "0" : "";
        let secondsZero = Math.round(seconds % 60).toString().length < 2 ? "0" : "";
        let hoursZero = hours.toString().length < 2 ? "0" : "";

        if (days > 0) {
            units = "روز";
            return `${days} ${units}`;
        } else if (hours > 0) {
            units = "ساعت";
            return `${hoursZero + hours}:${minutesZero + Math.round(minutes % 60)}:${secondsZero + Math.round(seconds % 60)} ${units}`;
        } else if (minutes > 0) {
            units = "دقیقه";
            return `${minutesZero + minutes}:${secondsZero + Math.round(seconds % 60)} ${units}`;
        } else {
            return `${secondsZero + seconds} ${units}`;
        }
    }

    function setRoutingLink(id) {
        $(document).ready(handlerRouting)
        $(window).resize(() => handlerRouting);
        function handlerRouting() {
            var isAndroid = navigator.userAgent.toLowerCase().indexOf("android") > -1;
            var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent && !window.MSStream);
            if (isAndroid | isIOS) $("#"+id).attr("href", $("#"+id).data("mobile-href"))
            else $("#"+id).attr("href", $("#"+id).data("desktop-href"))
        }
    }

    var map;
    function routing_field(id, lat, lng, zoom,map_search, dissabled , destination_latlng,space,originLatlng,origin_address,destination_address, originRoutingLatLng = {lat: null, lng: null}, goalRoutingLatLng = {lat: null, lng: null}, addressType = "small_address"){
        routingFieldId = id
        map = L.map(`map_set_${id}`, {
            measureControl: true,
            zoomControl: false,
            zoomsliderControl: false,
            attributionControl: false,
        }).setView([lat, lng], zoom);

        for (var key in window["app_config"]["_map_types"]) {
            const options = window["app_config"]["_map_types"][key]["option"]
            // const options = window["app_config"]["_map_types"][key]["option"]
            window[window["app_config"]["_map_types"][key]["var_name"]+id] = L.tileLayer(window["app_config"]["_map_types"][key]["url"], options);
        }


        var lastTileLayer = "";
        for(var key in app_config["_map_types"]) {
            if (app_config["_map_types"][key]["default"]) {
                window[app_config["_map_types"][key]["var_name"]+id].addTo(map).bringToBack();
                lastTileLayer = key;
            }
        }

        $("#change-layer_" + id).change(function () {
            var i = 0;
            if (getCookie("theme_mode") === themeCustomDarkClass) {
                for(var key in app_config["_map_types"]) {
                    if (window["app_config"]["_map_types"][key]["id"].endsWith("dark")) {
                        if (key != lastTileLayer) {
                            map.removeLayer(window[app_config["_map_types"][lastTileLayer]["var_name"]+id])
                            window[app_config["_map_types"][key]["var_name"]+id].addTo(map).bringToBack();
                            $("#change-layer-box_" + id + " > img").attr("src", PATHFILE + app_config["_map_types"][lastTileLayer]["icon"]);
                            lastTileLayer = key
                            break;
                        } else {
                            if (window[app_config["_map_types"][key]["var_name"]+id])
                                map.removeLayer(window[app_config["_map_types"][key]["var_name"]+id]);
                        }
                    }
                }
            } else {
                for(var key in app_config["_map_types"]) {
                    if (!window["app_config"]["_map_types"][key]["id"].endsWith("dark")) {
                        if (key != lastTileLayer) {
                            map.removeLayer(window[app_config["_map_types"][lastTileLayer]["var_name"]+id])
                            window[app_config["_map_types"][key]["var_name"]+id].addTo(map).bringToBack();
                            $("#change-layer-box_" + id + " > img").attr("src", PATHFILE + app_config["_map_types"][lastTileLayer]["icon"]);
                            lastTileLayer = key
                            break;
                        } else {
                            if (window[app_config["_map_types"][key]["var_name"]+id])
                                map.removeLayer(window[app_config["_map_types"][key]["var_name"]+id]);
                        }
                    }
                }
            }
        });
        map.on("dragend", function (e) {
            set_marker(map.getCenter().lat, map.getCenter().lng);
            $(`#location_internal_latlng_${id}`).html(map.getCenter().lat + " , " + map.getCenter().lng);
        });
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

            var timeoutLocation;
            var location_button = document.querySelector(`#location_button_${id}`);
            if (location_button) {
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
            }
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
            if (themeName === "dark") {
                $(".leaflet-map-pane").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
            } else {
                $(".leaflet-map-pane").css("filter", "none");
            }
        });
        function set_marker(lat, lon) {
            $(`#element_${id}_lat`).val(lat);
            $(`#element_${id}_lat`).trigger("change").trigger("input");
            $(`#element_${id}_lan`).val(lon);
            $(`#element_${id}_lan`).trigger("change").trigger("input");
            $(`#element_${id}`).val(lat + "," + lon);
            $(`#element_${id}`).trigger("change").trigger("input");
        }
        $(`.routing_button_${id}`).click(function () {
            console.log(destination_latlng,"routing")
            if ($(this).attr("data-status") == "onlyOrigin") {
            route_origin = map.getCenter();
            var origin_icon = L.icon({
                iconUrl: PATHFILE+"assets/images/maps/markers/origin-marker.png",
                iconSize: [27, 41],
            });
            if (origin_marker) map.removeLayer(origin_marker);
            if (dissabled != "t") {
                origin_marker = L.marker([route_origin.lat, route_origin.lng], {
                    icon: origin_icon,
                    draggable: true,
                }).addTo(map);
                    origin_marker.on("dragend", (e) => setOriginMarker(e,originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType));
            } else {
                    origin_marker = L.marker([route_origin.lat, route_origin.lng], {
                        icon: origin_icon,
                        draggable: false,
                    }).addTo(map);
            }
            var origin_latlng = {
                lat: map.getCenter().lat,
                lng: map.getCenter().lng,
            };
            clickMapHandler(origin_latlng, false);
            origin_getAddress(route_origin.lat, route_origin.lng);
            if (coordsArray.length > 1) {
                $(this).attr("data-status", "origin");
                $(".route-page-places-items").text("");
                $(".marker_center").hide();
                $(this).removeClass("active");
                $(".leaflet-control-container").show();
            } else {
                $(".marker_center").show();
                $(this).text("مقصد");
                $(this).attr("data-status", "goal");
                $(this).addClass("active");
            }
            // routingToSelectedPointA(origin_latlng)
            return;
            }

            if ($(this).attr("data-status") == "origin") {

            route_origin = map.getCenter();
            var origin_icon = L.icon({
                iconUrl: PATHFILE + "assets/images/maps/markers/origin-marker.png",
                iconSize: [27, 41],
            });
            if (origin_marker) map.removeLayer(origin_marker);
            if (dissabled != "t") {
                origin_marker = L.marker([route_origin.lat, route_origin.lng], {
                    icon: origin_icon,
                    draggable: true,
                }).addTo(map);
                origin_marker.on("dragend", (e) => setOriginMarker(e,originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType));
            } else {
                    origin_marker = L.marker([route_origin.lat, route_origin.lng], {
                        icon: origin_icon,
                        draggable: false,
                    }).addTo(map);
            }
            var origin_latlng = {
                lat: map.getCenter().lat,
                lng: map.getCenter().lng,
            };
            clickMapHandler(origin_latlng, false);
            origin_getAddress(route_origin.lat, route_origin.lng);
            if (coordsArray.length > 1) {
                $(".marker_center").hide();
                $(this).removeClass("active");
                $(".leaflet-control-container").show();
            } else {
                $(".marker_center").show();
                $(this).text("انتخاب مقصد");
                $(this).attr("data-status", "goal");
                $(".routing_button").addClass("active");
            }
            } else {
            route_goal = map.getCenter();
            var goal_icon = L.icon({
                iconUrl: PATHFILE+"assets/images/maps/markers/goal-marker.png",
                iconSize: [27, 41],
            });
            if (goal_marker) map.removeLayer(goal_marker);
            if (dissabled != "t") {
                goal_marker = L.marker([route_goal.lat, route_goal.lng], {
                    icon: goal_icon,
                    draggable: true,
                }).addTo(map);
                goal_marker.on("dragend", (e) => setGoalMarker(e,originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType));
            } else {
                    goal_marker = L.marker([route_goal.lat, route_goal.lng], {
                        icon: goal_icon,
                        draggable: false,
                    }).addTo(map);
            }
            var goal_latlng = { lat: map.getCenter().lat, lng: map.getCenter().lng };
            clickMapHandler(goal_latlng, true,originLatlng,destination_latlng,space,origin_address,destination_address,id,addressType);
            goal_getAddress(route_goal.lat, route_goal.lng);
            if (coordsArray.length > 1) {
                goal_getAddress(route_goal.lat, route_goal.lng);
                $(this).hide();
                $(`.marker_center_${id}`).hide();
            } else {
                $(".marker_center").show();
                $(this).text("انتخاب مبدا");
                $(this).attr("data-status", "origin");
                $(this).addClass("active");
            }
            }
        });

        if (originRoutingLatLng.lat && originRoutingLatLng.lng && goalRoutingLatLng.lat && goalRoutingLatLng.lng) {
            $(`.routing_button_${id}`).attr("data-status", "origin")
            map.setView([originRoutingLatLng.lat, originRoutingLatLng.lng],  17)
            $(`.routing_button_${id}`).click()
            console.log(`.routing_button_${id}`)
            setTimeout(() => {
                $(`.routing_button_${id}`).attr("data-status", "goal")
                map.setView([goalRoutingLatLng.lat, goalRoutingLatLng.lng],  17)
                $(`.routing_button_${id}`).click()
            },300)
        }
    }

    return {
        routing_field
    }
}
function setStartEndTimePickers(startInputId, endInputId, options) {
    var cs = getComputedStyle(document.querySelector("body"))
    var startInput = $("#"+startInputId)
    var endInput = $("#"+endInputId)
    var initialOptions = {...options}

    var defaultOptions = {
        i18n: {
            cancelButton: "انصراف",
            okButton: "باشه",
        },
        duration: false,
        autosize: false,
        fontFamily: "IRANSans",
        colors: {
            popupHeaderBackgroundColor: `rgb(${cs.getPropertyValue("--rgb-first")})`,
            selectorColor: `rgb(${cs.getPropertyValue("--rgb-first")})`,
            buttonTextColor: `rgb(${cs.getPropertyValue("--rgb-seventh-darker")})`,
            clockFaceColor: `rgb(${cs.getPropertyValue("--rgb-tenth-lighter")})`,
            clockInnerCircleTextColor: `rgb(${cs.getPropertyValue("--rgb-darker")})`,
            hoverCircleColor: `rgb(${cs.getPropertyValue("--rgb-first-light")})`,
            clockOuterCircleTextColor: `rgb(${cs.getPropertyValue("--rgb-darkest")})`,
            clockInnerCircleUnselectableTextColor: `rgb(${cs.getPropertyValue("--rgb-light-dark")})`,
            clockOuterCircleUnselectableTextColor: `rgb(${cs.getPropertyValue("--rgb-light-dark")})`,
        },
        zIndex: options?.zIndex || 999,
        appendToBody: options?.appendToBody || false
    }
    

    setTimePickerStart()
    setTimePickerEnd()
    
    function setTimePickerStart() {
        endTime = endInput.val()
        startTime = startInput.val()
        options.maximum = endTime.length ? endTime: options.maximum; 
        startInput.clockTimePicker({
            ...defaultOptions,
            minimum: initialOptions.minimum,
            maximum: options.maximum,
            onClose: () => setTimePickerEnd(),
            defaultTime: initialOptions?.defaultStart,
        })
        if (startTime && endTime && endTime < startTime) {
            startInput.val(endTime)
        }
    }
    function setTimePickerEnd() {
        endTime = endInput.val()
        startTime = startInput.val()
        options.minimum = startTime.length ? startTime: options.minimum; 
        endInput.clockTimePicker({
            ...defaultOptions,
            minimum: options.minimum,
            maximum: initialOptions.maximum,
            onClose: () => setTimePickerStart(),
            defaultTime: initialOptions?.defaultEnd,
        })
        if (startTime && endTime && endTime < startTime) {
            endInput.val(startTime)
        }
    }
    
    $(document).on("themeChanged", function () {
        setTimePickerStart()
        setTimePickerEnd()
    })
}

/** Chat App Scripts */
function visualize(analyser, audio, element) {
    var cs = getComputedStyle(document.querySelector("body"))
    if (audio.paused) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteFrequencyData(dataArray);

    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
    }
    const average = sum / dataArray.length;

    const shadowSize = Math.max(0, Math.min(4, average / 30));
    function getRandomFloat() {
        return (Math.random() * 4) - 1;
    }
    element.style.boxShadow = `2px 0 0 ${shadowSize + getRandomFloat()}px rgba(${cs.getPropertyValue("--rgb-first-light")}, 0.3),
                                -2px 0 0 ${shadowSize + getRandomFloat()}px rgba(${cs.getPropertyValue("--rgb-first-light")}, 0.3),
                                0 2px 0 ${shadowSize + getRandomFloat()}px rgba(${cs.getPropertyValue("--rgb-first-light")}, 0.3),
                                0 -2px 0 ${shadowSize + getRandomFloat()}px rgba(${cs.getPropertyValue("--rgb-first-light")}, 0.3)`;

    requestAnimationFrame(() => visualize(analyser, audio, element));
}

function voicePlayer(id, url) {
    var cs = getComputedStyle(document.querySelector("body"))
    const wavesurferOptions = {
        "container": `#voice_player_${id}`,
        "height": 50,
        "splitChannels": false,
        "normalize": false,
        "waveColor": `rgb(${cs.getPropertyValue("--rgb-first-light")})`,
        "progressColor": `rgb(${cs.getPropertyValue("--rgb-first")})`,
        "cursorColor": "#ddd5e9",
        "cursorWidth": 0,
        "barWidth": 2,
        "barGap": 1,
        "barRadius": 3,
        "barHeight": 0.6,
        "barAlign": "",
        "minPxPerSec": 1,
        "fillParent": true,
        url,
        "mediaControls": false,
        "autoplay": false,
        "interact": true,
        "dragToSeek": true,
        "hideScrollbar": false,
        "audioRate": 1,
        "autoScroll": true,
        "autoCenter": true,
        "sampleRate": 8000
    }

    const wavesurfer = WaveSurfer.create(wavesurferOptions)
    
    wavesurfer.on('interaction', () => {
        wavesurfer.play()
    })
    
    wavesurfer.on('finish', () => {
        wavesurfer.setTime(0)
    })
    let resetAudioCtx = () => {};
    wavesurfer.on("play", () => {
        $(`#voice_player_btn_${id}`).addClass("playing")
        const {reset: resetAudioContext} = handleAudioContext(wavesurfer.media)
        resetAudioCtx = resetAudioContext
    })

    wavesurfer.on('pause', () => {
        $(`#voice_player_btn_${id}`).removeClass("playing")
        resetAudioCtx()
    })

    function isAudioPlaying(audioElement) {
        return !audioElement.paused && audioElement.currentTime > 0 && !audioElement.ended;
    }

    $(`#voice_player_btn_${id}`).click(function() {
        if (isAudioPlaying(wavesurfer.media)) {
            wavesurfer.pause()
        } else {
            wavesurfer.play()
        }
    });
    let audioContext;
    let mediaSource;
    let analyser;

    function handleAudioContext(audio) {
        const playButton = document.getElementById(`voice_player_btn_${id}`);

        if (!audioContext) {
            audioContext = new (window.AudioContext)();
        }
        if (!mediaSource) {
            try {
                mediaSource =  audioContext.createMediaElementSource(audio)
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
        }
    }
}

function uploadFileWithProgress(file, url, progressBarId) {
    return new Promise((resolve, reject) => {
        try {
            const progressCircle = document.getElementById(progressBarId);
            const xhr = new XMLHttpRequest();
            let isUploaded = false
            
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentComplete = Math.round((event.loaded / event.total) * 100);
                    progressCircle.style.setProperty('--progress', percentComplete);
                }
            });
            progressCircle.addEventListener("click", () => {
                if (isUploaded) return;
                xhr.abort();
                progressCircle.parentElement.remove();
            })
            xhr.addEventListener('load', (data) => {
                isUploaded = true
                progressCircle.classList.add("active");
                resolve(JSON.parse(data.target.response));
            });
            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });
            xhr.addEventListener('abort', () => {
                reject(new Error('Upload canceled'));
            });
            xhr.open('POST', url);
            const formData = new FormData();
            formData.append('file', file);
            xhr.send(formData);
        } catch(err) {
            reject(err)
        }
    })
}

function scrollEnd(elementId) {
    const element = document.getElementById(elementId);
    element.scrollTo({ top: element.scrollHeight, behavior: 'smooth' });
}

const chatEmojies = {
    smile: ["😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃", "🫠", "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "☺", "😚", "😙", "🥲", "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🫢", "🫣", "🤫", "🤔", "🫡", "🤐", "🤨", "😐", "😑", "😶", "🫥", "😶‍🌫", "😏", "😒", "🙄", "😬", "😮‍💨", "🤥", "😌", "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕", "🤢", "🤮", "🤧", "🥵", "🥶", "🥴", "😵", "😵‍💫", "🤯", "🤠", "🥳", "🥸", "😎", "🤓", "🧐", "😕", "🫤", "😟", "🙁", "☹", "😮", "😯", "😲", "😳", "🥺", "🥹", "😦", "😧", "😨", "😰", "😥", "😢", "😭", "😱", "😖", "😣", "😞", "😓", "😩", "😫", "🥱", "😤", "😡", "😠", "🤬", "😈", "👿", "💀", "☠", "💩", "🤡", "👹", "👺", "👻", "👽", "👾", "🤖", "😺", "😸", "😹", "😻", "😼", "😽", "🙀", "😿", "😾", "🙈", "🙉", "🙊", "💋", "💌", "💘", "💝", "💖", "💗", "💓", "💞", "💕", "💟", "❣", "💔", "❤️‍🔥", "❤️‍🩹", "❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍", "💯", "💢", "💥", "💫", "💦", "💨", "🕳", "💣", "💬", "👁‍🗨", "🗨", "🗯", "💭", "💤", "👋", "🤚", "🖐", "✋", "🖖", "🫱", "🫲", "🫳", "🫴", "👌", "🤌", "🤏", "✌", "🤞", "🫰", "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝", "🫵", "👍", "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌", "🫶", "👐", "🤲", "🤝", "🙏", "✍", "💅", "🤳", "💪", "🦾", "🦿", "🦵", "🦶", "👂", "🦻", "👃", "🧠", "🫀", "🫁", "🦷", "🦴", "👀", "👁", "👅", "👄", "🫦", "👶", "🧒", "👦", "👧", "🧑", "👱", "👨", "🧔", "🧔‍♂️", "🧔‍♀️", "👨‍🦰", "👨‍🦱", "👨‍🦳", "👨‍🦲", "👩", "👩‍🦰", "🧑‍🦰", "👩‍🦱", "🧑‍🦱", "👩‍🦳", "🧑‍🦳", "👩‍🦲", "🧑‍🦲", "👱‍♀️", "👱‍♂️", "🧓", "👴", "👵", "🙍", "🙍‍♂️", "🙍‍♀️", "🙎", "🙎‍♂️", "🙎‍♀️", "🙅", "🙅‍♂️", "🙅‍♀️", "🙆", "🙆‍♂️", "🙆‍♀️", "💁", "💁‍♂️", "💁‍♀️", "🙋", "🙋‍♂️", "🙋‍♀️", "🧏", "🧏‍♂️", "🧏‍♀️", "🙇", "🙇‍♂️", "🙇‍♀️", "🤦", "🤦‍♂️", "🤦‍♀️", "🤷", "🤷‍♂️", "🤷‍♀️", "🧑‍⚕", "👨‍⚕", "👩‍⚕", "🧑‍🎓", "👨‍🎓", "👩‍🎓", "🧑‍🏫", "👨‍🏫", "👩‍🏫", "🧑‍⚖", "👨‍⚖", "👩‍⚖", "🧑‍🌾", "👨‍🌾", "👩‍🌾", "🧑‍🍳", "👨‍🍳", "👩‍🍳", "🧑‍🔧", "👨‍🔧", "👩‍🔧", "🧑‍🏭", "👨‍🏭", "👩‍🏭", "🧑‍💼", "👨‍💼", "👩‍💼", "🧑‍🔬", "👨‍🔬", "👩‍🔬", "🧑‍💻", "👨‍💻", "👩‍💻", "🧑‍🎤", "👨‍🎤", "👩‍🎤", "🧑‍🎨", "👨‍🎨", "👩‍🎨", "🧑‍✈", "👨‍✈", "👩‍✈", "🧑‍🚀", "👨‍🚀", "👩‍🚀", "🧑‍🚒", "👨‍🚒", "👩‍🚒", "👮", "👮‍♂️", "👮‍♀️", "🕵", "🕵‍♂️", "🕵‍♀️", "💂", "💂‍♂️", "💂‍♀️", "🥷", "👷", "👷‍♂️", "👷‍♀️", "🫅", "🤴", "👸", "👳", "👳‍♂️", "👳‍♀️", "👲", "🧕", "🤵", "🤵‍♂️", "🤵‍♀️", "👰", "👰‍♂️", "👰‍♀️", "🤰", "🫃", "🫄", "🤱", "👩‍🍼", "👨‍🍼", "🧑‍🍼", "👼", "🎅", "🤶", "🧑‍🎄", "🦸", "🦸‍♂️", "🦸‍♀️", "🦹", "🦹‍♂️", "🦹‍♀️", "🧙", "🧙‍♂️", "🧙‍♀️", "🧚", "🧚‍♂️", "🧚‍♀️", "🧛", "🧛‍♂️", "🧛‍♀️", "🧜", "🧜‍♂️", "🧜‍♀️", "🧝", "🧝‍♂️", "🧝‍♀️", "🧞", "🧞‍♂️", "🧞‍♀️", "🧟", "🧟‍♂️", "🧟‍♀️", "🧌", "💆", "💆‍♂️", "💆‍♀️", "💇", "💇‍♂️", "💇‍♀️", "🚶", "🚶‍♂️", "🚶‍♀️", "🧍", "🧍‍♂️", "🧍‍♀️", "🧎", "🧎‍♂️", "🧎‍♀️", "🧑‍🦯", "👨‍🦯", "👩‍🦯", "🧑‍🦼", "👨‍🦼", "👩‍🦼", "🧑‍🦽", "👨‍🦽", "👩‍🦽", "🏃", "🏃‍♂️", "🏃‍♀️", "💃", "🕺", "🕴", "👯", "👯‍♂️", "👯‍♀️", "🧖", "🧖‍♂️", "🧖‍♀️", "🧗", "🧗‍♂️", "🧗‍♀️", "🤺", "🏇", "⛷", "🏂", "🏌", "🏌‍♂️", "🏌‍♀️", "🏄", "🏄‍♂️", "🏄‍♀️", "🚣", "🚣‍♂️", "🚣‍♀️", "🏊", "🏊‍♂️", "🏊‍♀️", "⛹", "⛹‍♂️", "⛹‍♀️", "🏋", "🏋‍♂️", "🏋‍♀️", "🚴", "🚴‍♂️", "🚴‍♀️", "🚵", "🚵‍♂️", "🚵‍♀️", "🤸", "🤸‍♂️", "🤸‍♀️", "🤼", "🤼‍♂️", "🤼‍♀️", "🤽", "🤽‍♂️", "🤽‍♀️", "🤾", "🤾‍♂️", "🤾‍♀️", "🤹", "🤹‍♂️", "🤹‍♀️", "🧘", "🧘‍♂️", "🧘‍♀️", "🛀", "🛌", "🧑‍🤝‍🧑", "👭", "👫", "👬", "💏", "👩‍❤️‍💋‍👨", "👨‍❤️‍💋‍👨", "👩‍❤️‍💋‍👩", "💑", "👩‍❤️‍👨", "👨‍❤️‍👨", "👩‍❤️‍👩", "👪", "👨‍👩‍👦", "👨‍👩‍👧", "👨‍👩‍👧‍👦", "👨‍👩‍👦‍👦", "👨‍👩‍👧‍👧", "👨‍👨‍👦", "👨‍👨‍👧", "👨‍👨‍👧‍👦", "👨‍👨‍👦‍👦", "👨‍👨‍👧‍👧", "👩‍👩‍👦", "👩‍👩‍👧", "👩‍👩‍👧‍👦", "👩‍👩‍👦‍👦", "👩‍👩‍👧‍👧", "👨‍👦", "👨‍👦‍👦", "👨‍👧", "👨‍👧‍👦", "👨‍👧‍👧", "👩‍👦", "👩‍👦‍👦", "👩‍👧", "👩‍👧‍👦", "👩‍👧‍👧", "🗣", "👤", "👥", "🫂", "👣"],
    cat: ["🐵", "🐒", "🦍", "🦧", "🐶", "🐕", "🦮", "🐕‍🦺", "🐩", "🐺", "🦊", "🦝", "🐱", "🐈", "🐈‍⬛", "🦁", "🐯", "🐅", "🐆", "🐴", "🐎", "🦄", "🦓", "🦌", "🦬", "🐮", "🐂", "🐃", "🐄", "🐷", "🐖", "🐗", "🐽", "🐏", "🐑", "🐐", "🐪", "🐫", "🦙", "🦒", "🐘", "🦣", "🦏", "🦛", "🐭", "🐁", "🐀", "🐹", "🐰", "🐇", "🐿", "🦫", "🦔", "🦇", "🐻", "🐻‍❄", "🐨", "🐼", "🦥", "🦦", "🦨", "🦘", "🦡", "🐾", "🦃", "🐔", "🐓", "🐣", "🐤", "🐥", "🐦", "🐧", "🕊", "🦅", "🦆", "🦢", "🦉", "🦤", "🪶", "🦩", "🦚", "🦜", "🐸", "🐊", "🐢", "🦎", "🐍", "🐲", "🐉", "🦕", "🦖", "🐳", "🐋", "🐬", "🦭", "🐟", "🐠", "🐡", "🦈", "🐙", "🐚", "🪸", "🐌", "🦋", "🐛", "🐜", "🐝", "🪲", "🐞", "🦗", "🪳", "🕷", "🕸", "🦂", "🦟", "🪰", "🪱", "🦠", "💐", "🌸", "💮", "🪷", "🏵", "🌹", "🥀", "🌺", "🌻", "🌼", "🌷", "🌱", "🪴", "🌲", "🌳", "🌴", "🌵", "🌾", "🌿", "☘", "🍀", "🍁", "🍂", "🍃", "🪹", "🪺"],
    'apple-alt': ["🍇", "🍈", "🍉", "🍊", "🍋", "🍌", "🍍", "🥭", "🍎", "🍏", "🍐", "🍑", "🍒", "🍓", "🫐", "🥝", "🍅", "🫒", "🥥", "🥑", "🍆", "🥔", "🥕", "🌽", "🌶", "🫑", "🥒", "🥬", "🥦", "🧄", "🧅", "🍄", "🥜", "🫘", "🌰", "🍞", "🥐", "🥖", "🫓", "🥨", "🥯", "🥞", "🧇", "🧀", "🍖", "🍗", "🥩", "🥓", "🍔", "🍟", "🍕", "🌭", "🥪", "🌮", "🌯", "🫔", "🥙", "🧆", "🥚", "🍳", "🥘", "🍲", "🫕", "🥣", "🥗", "🍿", "🧈", "🧂", "🥫", "🍱", "🍘", "🍙", "🍚", "🍛", "🍜", "🍝", "🍠", "🍢", "🍣", "🍤", "🍥", "🥮", "🍡", "🥟", "🥠", "🥡", "🦀", "🦞", "🦐", "🦑", "🦪", "🍦", "🍧", "🍨", "🍩", "🍪", "🎂", "🍰", "🧁", "🥧", "🍫", "🍬", "🍭", "🍮", "🍯", "🍼", "🥛", "☕", "🫖", "🍵", "🍶", "🍾", "🍷", "🍸", "🍹", "🍺", "🍻", "🥂", "🥃", "🫗", "🥤", "🧋", "🧃", "🧉", "🧊", "🥢", "🍽", "🍴", "🥄", "🔪", "🫙", "🏺"],
    lightbulb: ["🌍", "🌎", "🌏", "🌐", "🗺", "🗾", "🧭", "🏔", "⛰", "🌋", "🗻", "🏕", "🏖", "🏜", "🏝", "🏞", "🏟", "🏛", "🏗", "🧱", "🪨", "🪵", "🛖", "🏘", "🏚", "🏠", "🏡", "🏢", "🏣", "🏤", "🏥", "🏦", "🏨", "🏩", "🏪", "🏫", "🏬", "🏭", "🏯", "🏰", "💒", "🗼", "🗽", "⛪", "🕌", "🛕", "🕍", "⛩", "🕋", "⛲", "⛺", "🌁", "🌃", "🏙", "🌄", "🌅", "🌆", "🌇", "🌉", "♨", "🎠", "🛝", "🎡", "🎢", "💈", "🎪", "🚂", "🚃", "🚄", "🚅", "🚆", "🚇", "🚈", "🚉", "🚊", "🚝", "🚞", "🚋", "🚌", "🚍", "🚎", "🚐", "🚑", "🚒", "🚓", "🚔", "🚕", "🚖", "🚗", "🚘", "🚙", "🛻", "🚚", "🚛", "🚜", "🏎", "🏍", "🛵", "🦽", "🦼", "🛺", "🚲", "🛴", "🛹", "🛼", "🚏", "🛣", "🛤", "🛢", "⛽", "🛞", "🚨", "🚥", "🚦", "🛑", "🚧", "⚓", "🛟", "⛵", "🛶", "🚤", "🛳", "⛴", "🛥", "🚢", "✈", "🛩", "🛫", "🛬", "🪂", "💺", "🚁", "🚟", "🚠", "🚡", "🛰", "🚀", "🛸", "🛎", "🧳", "⌛", "⏳", "⌚", "⏰", "⏱", "⏲", "🕰", "🕛", "🕧", "🕐", "🕜", "🕑", "🕝", "🕒", "🕞", "🕓", "🕟", "🕔", "🕠", "🕕", "🕡", "🕖", "🕢", "🕗", "🕣", "🕘", "🕤", "🕙", "🕥", "🕚", "🕦", "🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌙", "🌚", "🌛", "🌜", "🌡", "☀", "🌝", "🌞", "🪐", "⭐", "🌟", "🌠", "🌌", "☁", "⛅", "⛈", "🌤", "🌥", "🌦", "🌧", "🌨", "🌩", "🌪", "🌫", "🌬", "🌀", "🌈", "🌂", "☂", "☔", "⛱", "⚡", "❄", "☃", "⛄", "☄", "🔥", "💧", "🌊"],
    'futbol-ball': ["🎃", "🎄", "🎆", "🎇", "🧨", "✨", "🎈", "🎉", "🎊", "🎋", "🎍", "🎎", "🎏", "🎐", "🎑", "🧧", "🎀", "🎁", "🎗", "🎟", "🎫", "🎖", "🏆", "🏅", "🥇", "🥈", "🥉", "⚽", "⚾", "🥎", "🏀", "🏐", "🏈", "🏉", "🎾", "🥏", "🎳", "🏏", "🏑", "🏒", "🥍", "🏓", "🏸", "🥊", "🥋", "🥅", "⛳", "⛸", "🎣", "🤿", "🎽", "🎿", "🛷", "🥌", "🎯", "🪀", "🪁", "🎱", "🔮", "🪄", "🧿", "🪬", "🎮", "🕹", "🎰", "🎲", "🧩", "🧸", "🪅", "🪩", "🪆", "♠", "♥", "♦", "♣", "♟", "🃏", "🀄", "🎴", "🎭", "🖼", "🎨", "🧵", "🪡", "🧶", "🪢"],
    car: ["👓", "🕶", "🥽", "🥼", "🦺", "👔", "👕", "👖", "🧣", "🧤", "🧥", "🧦", "👗", "👘", "🥻", "🩱", "🩲", "🩳", "👙", "👚", "👛", "👜", "👝", "🛍", "🎒", "🩴", "👞", "👟", "🥾", "🥿", "👠", "👡", "🩰", "👢", "👑", "👒", "🎩", "🎓", "🧢", "🪖", "⛑", "📿", "💄", "💍", "💎", "🔇", "🔈", "🔉", "🔊", "📢", "📣", "📯", "🔔", "🔕", "🎼", "🎵", "🎶", "🎙", "🎚", "🎛", "🎤", "🎧", "📻", "🎷", "🪗", "🎸", "🎹", "🎺", "🎻", "🪕", "🥁", "🪘", "📱", "📲", "☎", "📞", "📟", "📠", "🔋", "🪫", "🔌", "💻", "🖥", "🖨", "⌨", "🖱", "🖲", "💽", "💾", "💿", "📀", "🧮", "🎥", "🎞", "📽", "🎬", "📺", "📷", "📸", "📹", "📼", "🔍", "🔎", "🕯", "💡", "🔦", "🏮", "🪔", "📔", "📕", "📖", "📗", "📘", "📙", "📚", "📓", "📒", "📃", "📜", "📄", "📰", "🗞", "📑", "🔖", "🏷", "💰", "🪙", "💴", "💵", "💶", "💷", "💸", "💳", "🧾", "💹", "✉", "📧", "📨", "📩", "📤", "📥", "📦", "📫", "📪", "📬", "📭", "📮", "🗳", "✏", "✒", "🖋", "🖊", "🖌", "🖍", "📝", "💼", "📁", "📂", "🗂", "📅", "📆", "🗒", "🗓", "📇", "📈", "📉", "📊", "📋", "📌", "📍", "📎", "🖇", "📏", "📐", "✂", "🗃", "🗄", "🗑", "🔒", "🔓", "🔏", "🔐", "🔑", "🗝", "🔨", "🪓", "⛏", "⚒", "🛠", "🗡", "⚔", "🔫", "🪃", "🏹", "🛡", "🪚", "🔧", "🪛", "🔩", "⚙", "🗜", "⚖", "🦯", "🔗", "⛓", "🪝", "🧰", "🧲", "🪜", "⚗", "🧪", "🧫", "🧬", "🔬", "🔭", "📡", "💉", "🩸", "💊", "🩹", "🩼", "🩺", "🩻", "🚪", "🛗", "🪞", "🪟", "🛏", "🛋", "🪑", "🚽", "🪠", "🚿", "🛁", "🪤", "🪒", "🧴", "🧷", "🧹", "🧺", "🧻", "🪣", "🧼", "🫧", "🪥", "🧽", "🧯", "🛒", "🚬", "⚰", "🪦", "⚱", "🗿", "🪧", "🪪", "🏧", "🚮", "🚰", "♿", "🚹", "🚺", "🚻", "🚼", "🚾", "🛂", "🛃", "🛄", "🛅", "⚠", "🚸", "⛔", "🚫", "🚳", "🚭", "🚯", "🚱", "🚷", "📵", "🔞", "☢", "☣", "⬆", "↗", "➡", "↘", "⬇", "↙", "⬅", "↖", "↕", "↔", "↩", "↪", "⤴", "⤵", "🔃", "🔄", "🔙", "🔚", "🔛", "🔜", "🔝", "🛐", "⚛", "🕉", "✡", "☸", "☯", "✝", "☦", "☪", "☮", "🕎", "🔯", "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓", "⛎", "🔀", "🔁", "🔂", "▶", "⏩", "⏭", "⏯", "◀", "⏪", "⏮", "🔼", "⏫", "🔽", "⏬", "⏸", "⏹", "⏺", "⏏", "🎦", "🔅", "🔆", "📶", "📳", "📴", "⚧", "✖", "➕", "➖", "➗", "🟰", "♾", "‼", "⁉", "❓", "❔", "❕", "❗", "〰", "💱", "💲", "♻", "⚜", "🔱", "📛", "🔰", "⭕", "✅", "☑", "✔", "❌", "❎", "➰", "➿", "〽", "✳", "✴", "❇", "©", "®", "™", "#⃣", "*⃣", "0⃣", "1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟", "🔠", "🔡", "🔢", "🔣", "🔤", "🅰", "🆎", "🅱", "🆑", "🆒", "🆓", "ℹ", "🆔", "Ⓜ", "🆕", "🆖", "🅾", "🆗", "🅿", "🆘", "🆙", "🆚", "🈁", "🈂", "🈷", "🈶", "🈯", "🉐", "🈹", "🈚", "🈲", "🉑", "🈸", "🈴", "🈳", "㊗", "㊙", "🈺", "🈵", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫", "⚪", "🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "🟫", "⬛", "⬜", "◼", "◻", "◾", "◽", "▪", "▫", "🔶", "🔷", "🔸", "🔹", "🔺", "🔻", "💠", "🔘", "🔳", "🔲"],
    flag: ["🏁", "🚩", "🎌", "🏴", "🏳", "🏴‍☠", "🇦🇨", "🇦🇩", "🇦🇪", "🇦🇫", "🇦🇬", "🇦🇮", "🇦🇱", "🇦🇲", "🇦🇴", "🇦🇶", "🇦🇷", "🇦🇸", "🇦🇹", "🇦🇺", "🇦🇼", "🇦🇽", "🇦🇿", "🇧🇦", "🇧🇧", "🇧🇩", "🇧🇪", "🇧🇫", "🇧🇬", "🇧🇭", "🇧🇮", "🇧🇯", "🇧🇱", "🇧🇲", "🇧🇳", "🇧🇴", "🇧🇶", "🇧🇷", "🇧🇸", "🇧🇹", "🇧🇻", "🇧🇼", "🇧🇾", "🇧🇿", "🇨🇦", "🇨🇨", "🇨🇩", "🇨🇫", "🇨🇬", "🇨🇭", "🇨🇮", "🇨🇰", "🇨🇱", "🇨🇲", "🇨🇳", "🇨🇴", "🇨🇵", "🇨🇷", "🇨🇺", "🇨🇻", "🇨🇼", "🇨🇽", "🇨🇾", "🇨🇿", "🇩🇪", "🇩🇬", "🇩🇯", "🇩🇰", "🇩🇲", "🇩🇴", "🇩🇿", "🇪🇦", "🇪🇨", "🇪🇪", "🇪🇬", "🇪🇭", "🇪🇷", "🇪🇸", "🇪🇹", "🇪🇺", "🇫🇮", "🇫🇯", "🇫🇰", "🇫🇲", "🇫🇴", "🇫🇷", "🇬🇦", "🇬🇧", "🇬🇩", "🇬🇪", "🇬🇫", "🇬🇬", "🇬🇭", "🇬🇮", "🇬🇱", "🇬🇲", "🇬🇳", "🇬🇵", "🇬🇶", "🇬🇷", "🇬🇸", "🇬🇹", "🇬🇺", "🇬🇼", "🇬🇾", "🇭🇰", "🇭🇲", "🇭🇳", "🇭🇷", "🇭🇹", "🇭🇺", "🇮🇨", "🇮🇩", "🇮🇪", "🇮🇲", "🇮🇳", "🇮🇴", "🇮🇶", "🇮🇷", "🇮🇸", "🇮🇹", "🇯🇪", "🇯🇲", "🇯🇴", "🇯🇵", "🇰🇪", "🇰🇬", "🇰🇭", "🇰🇮", "🇰🇲", "🇰🇳", "🇰🇵", "🇰🇷", "🇰🇼", "🇰🇾", "🇰🇿", "🇱🇦", "🇱🇧", "🇱🇨", "🇱🇮", "🇱🇰", "🇱🇷", "🇱🇸", "🇱🇹", "🇱🇺", "🇱🇻", "🇱🇾", "🇲🇦", "🇲🇨", "🇲🇩", "🇲🇪", "🇲🇫", "🇲🇬", "🇲🇭", "🇲🇰", "🇲🇱", "🇲🇲", "🇲🇳", "🇲🇴", "🇲🇵", "🇲🇶", "🇲🇷", "🇲🇸", "🇲🇹", "🇲🇺", "🇲🇻", "🇲🇼", "🇲🇽", "🇲🇾", "🇲🇿", "🇳🇦", "🇳🇨", "🇳🇪", "🇳🇫", "🇳🇬", "🇳🇮", "🇳🇱", "🇳🇴", "🇳🇵", "🇳🇷", "🇳🇺", "🇳🇿", "🇴🇲", "🇵🇦", "🇵🇪", "🇵🇫", "🇵🇬", "🇵🇭", "🇵🇰", "🇵🇱", "🇵🇲", "🇵🇳", "🇵🇷", "🇵🇸", "🇵🇹", "🇵🇼", "🇵🇾", "🇶🇦", "🇷🇪", "🇷🇴", "🇷🇸", "🇷🇺", "🇷🇼", "🇸🇦", "🇸🇧", "🇸🇨", "🇸🇩", "🇸🇪", "🇸🇬", "🇸🇭", "🇸🇮", "🇸🇯", "🇸🇰", "🇸🇱", "🇸🇲", "🇸🇳", "🇸🇴", "🇸🇷", "🇸🇸", "🇸🇹", "🇸🇻", "🇸🇽", "🇸🇾", "🇸🇿", "🇹🇦", "🇹🇨", "🇹🇩", "🇹🇫", "🇹🇬", "🇹🇭", "🇹🇯", "🇹🇰", "🇹🇱", "🇹🇲", "🇹🇳", "🇹🇴", "🇹🇷", "🇹🇹", "🇹🇻", "🇹🇼", "🇹🇿", "🇺🇦", "🇺🇬", "🇺🇲", "🇺🇳", "🇺🇸", "🇺🇾", "🇺🇿", "🇻🇦", "🇻🇨", "🇻🇪", "🇻🇬", "🇻🇮", "🇻🇳", "🇻🇺", "🇼🇫", "🇼🇸", "🇽🇰", "🇾🇪", "🇾🇹", "🇿🇦", "🇿🇲", "🇿🇼", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "🏴󠁧󠁢󠁷󠁬󠁳󠁿"]
}

function addEmoji(emoji, inputId) {
    var messageInput = document.getElementById(inputId)
    messageInput.value += emoji
    messageInput.focus()
    messageInput.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
}