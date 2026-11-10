var map;
var full_address;
var origin_marker;
var goal_marker;
var waypoint1;
var waypoint2;
var distance;
var duration;

var homeLocation, workLocation;
var timeoutDelay = 200;
var allowMapClick = false;
var isActivePlacesMarkers = true;

function origin_getAddress(lat, lng) {
    fetch("https://map.ir/reverse/fast-reverse?lat=" + lat + "&lon=" + lng, {
        method: "GET",
        headers: { "x-api-key": API_TOKEN },
    })
        .then((res) => {
            if (res.status == 200) {
                return res.json();
            }
            return new Error("Error :/");
        })
        .then((data) => {
            $("#origin_routing_input").val(data?.postal_address ?? $("#origin_routing_input").val());
        });
}

function goal_getAddress(lat, lng) {
    fetch("https://map.ir/reverse/fast-reverse?lat=" + lat + "&lon=" + lng, {
        method: "GET",
        headers: { "x-api-key": API_TOKEN },
    })
        .then((res) => {
            if (res.status == 200) {
                return res.json();
            }
            return new Error("Error :/");
        })
        .then((data) => {
            $("#goal_routing_input").val(data?.postal_address ?? $("#goal_routing_input").val());
        });
}


function setGoalMarker(e) {
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
        var existingOTooltip = origin_marker?.getTooltip();
        origin_marker = L.marker(
            [route_origin.lat, route_origin.lng],
            origin_marker.options ?? {
                icon: origin_icon,
                draggable: true,
            },
        ).addTo(map);
        if (existingOTooltip) origin_marker.bindTooltip(existingOTooltip).openTooltip();
        origin_marker.on("dragend", setOriginMarker);
        var origin_latlng = {
            lat: route_origin.lat,
            lng: route_origin.lng,
        };
        clickMapHandler(origin_latlng, false);
        origin_getAddress(route_origin.lat, route_origin.lng);
    }

    // process of goal route
    var goal_icon = L.icon({
        iconUrl: PATHFILE + "assets/images/maps/markers/goal-marker.png",
        iconSize: [27, 41],
    });
    if (goal_marker) {
        map.removeLayer(goal_marker);
        var existingGTooltip = goal_marker?.getTooltip();
        goal_marker = L.marker(
            [route_goal.lat, route_goal.lng],
            goal_marker.options ?? {
                icon: goal_icon,
                draggable: true,
            },
        ).addTo(map);
        if (existingGTooltip) goal_marker.bindTooltip(existingGTooltip).openTooltip();
        goal_marker.on("dragend", setGoalMarker);
        var goal_latlng = { lat: route_goal.lat, lng: route_goal.lng };
        clickMapHandler(goal_latlng, true);
        goal_getAddress(route_goal.lat, route_goal.lng);
    }
}

function setOriginMarker(e) {
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
        var existingOTooltip = origin_marker?.getTooltip();
        origin_marker = L.marker(
            [route_origin.lat, route_origin.lng],
            origin_marker.options ?? {
                icon: origin_icon,
                draggable: true,
            },
        ).addTo(map);
        if (existingOTooltip) origin_marker.bindTooltip(existingOTooltip).openTooltip();
        origin_marker.on("dragend", setOriginMarker);
        var origin_latlng = {
            lat: route_origin.lat,
            lng: route_origin.lng,
        };
        clickMapHandler(origin_latlng, false);
        origin_getAddress(route_origin.lat, route_origin.lng);
    }

    // process of goal route
    var goal_icon = L.icon({
        iconUrl: PATHFILE + "assets/images/maps/markers/goal-marker.png",
        iconSize: [27, 41],
    });
    if (goal_marker) {
        map.removeLayer(goal_marker);
        var existingGTooltip = goal_marker?.getTooltip();
        goal_marker = L.marker(
            [route_goal.lat, route_goal.lng],
            goal_marker.options ?? {
                icon: goal_icon,
                draggable: true,
            },
        ).addTo(map);
        if (existingGTooltip) goal_marker.bindTooltip(existingGTooltip).openTooltip();
        goal_marker.on("dragend", setGoalMarker);
        var goal_latlng = { lat: route_goal.lat, lng: route_goal.lng };
        clickMapHandler(goal_latlng, true);
        goal_getAddress(route_goal.lat, route_goal.lng);
    }
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

function currentLocationRouting(elem) {
    $(elem).addClass("is-circular-loading")
    var routingStatus = $(".routing-button").attr("data-status")
    map.locate({ setView: true, maxZoom: 16 });
    map.on("locationfound", onLocationFound);
    function onLocationFound(e) {
        $(elem).removeClass("is-circular-loading")
        if (routingStatus == "onlyOrigin") {
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
            origin_getAddress(route_origin.lat, route_origin.lng);
            if (coordsArray.length > 1) {
                $(this).attr("data-status", "origin");
                $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
                    <div class="d-flex align-items-center">
                        <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
                    </div>
                    <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                        <div class="d-flex flex-column">
                            <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                        </div>
                    </div>
                    <span class="circular-loading"></span>
                </div>`);
                $(".marker_center").hide();
                $(this).removeClass("active");
                $(".leaflet-control-container").show();
                $(".down-section").show();
            } else {
                $(".marker_center").show();
                $(this).text("انتخاب مقصد");
                $(this).attr("data-status", "goal");
                $(this).addClass("active");
            }
        } else if (routingStatus == "origin") {
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
            origin_getAddress(route_origin.lat, route_origin.lng);
            if (coordsArray.length > 1) {
                $(".marker_center").hide();
                $(".routing-button").removeClass("active");
                $(".leaflet-control-container").show();
                $(".down-section").show();
            } else {
                $(".marker_center").show();
                $(".routing-button").text("انتخاب مقصد");
                $(".routing-button").attr("data-status", "goal");
                $(".routing-button").addClass("active");
            }
        } else {
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
            goal_getAddress(route_goal.lat, route_goal.lng);
            if (coordsArray.length > 1) {
                $(".routing-button").attr("data-status", "origin");
                $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
                    <div class="d-flex align-items-center">
                        <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
                    </div>
                    <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                        <div class="d-flex flex-column">
                            <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                        </div>
                    </div>
                </div>`);
                $(".marker_center").hide();
                $(".routing-button").removeClass("active");
                $(".leaflet-control-container").show();
                $(".down-section").show();
            } else {
                $(".marker_center").show();
                $(".routing-button").text("انتخاب مبدا");
                $(".routing-button").attr("data-status", "origin");
                $(".routing-button").addClass("active");
            }
        }
        map.off("locationfound", onLocationFound)
    }
    map.on("locationerror", onLocationError);
    function onLocationError(e) {
        $(elem).removeClass("is-circular-loading")
        snackbar("map_snackbar_18394829", "موقعیت مکانی شما یافت نشد.", "danger", {
            hasIcon: true,
        });
        map.off("locationerror", onLocationError);
    }
}

function targetLocationRouting(elem) {
    var route_page_lat = $(elem).attr("data-lat");
    var route_page_lng = $(elem).attr("data-lng");
    map.setView([route_page_lat, route_page_lng], 17);
    $("#" + routingInputId).val($(elem).find("div:nth-child(2) > div > span:nth-child(2)").text());
    if (routingInputId === "origin_routing_input") {
        // مبدا
        // process of origin route
        if (!$("#routing-page").hasClass("active")) {
            $("#routing-page").fadeIn().show().addClass("active").siblings().fadeOut().hide().removeClass("active");
        }
        route_origin = { lat: route_page_lat, lng: route_page_lng };
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
            lat: route_origin.lat,
            lng: route_origin.lng,
        };
        clearRouteDraw(false)
        if (coordsArray.length > 1) coordsArray = coordsArray.slice(1, 2)
        coordsArray.unshift(origin_latlng);
        route(coordsArray);
        origin_getAddress(route_origin.lat, route_origin.lng);
        if (coordsArray.length > 1) {
            $(".marker_center").hide();
            $(".routing-button").removeClass("active");
            $(".leaflet-control-container").show();
            $(".down-section").show();
        } else {
            $(".marker_center").show();
            $(".routing-button").text("انتخاب مقصد");
            $(".routing-button").attr("data-status", "goal");
            $(".routing-button").addClass("active");
            $(".leaflet-control-container").hide();
            $(".down-section").hide();
        }
    } else if (routingInputId === "goal_routing_input") {
        // مقصد
        // process of goal route
        route_goal = { lat: route_page_lat, lng: route_page_lng };
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
        clearRouteDraw(false)
        if (coordsArray.length > 1) coordsArray = coordsArray.slice(0, 1)
        coordsArray.push(route_goal);
        route(coordsArray);
        goal_getAddress(route_goal.lat, route_goal.lng);
        if (coordsArray.length > 1) {
            $(".routing-button").attr("data-status", "origin");
            $(".route-page-places-items").html(`
    <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
<div class="d-flex align-items-center">
    <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
</div>
<div class="d-flex align-items-center  justify-content-between ms-4 w-100">
    <div class="d-flex flex-column">
        <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
    </div>
</div>
</div>`);
            $(".marker_center").hide();
            $(".routing-button").removeClass("active");
            $(".leaflet-control-container").show();
            $(".down-section").show();
        } else {
            $(".marker_center").show();
            $(".routing-button").text("انتخاب مبدا");
            $(".routing-button").attr("data-status", "origin");
            $(".routing-button").addClass("active");
            $(".leaflet-control-container").hide();
            $(".down-section").hide();
        }
    }
}
function setRoutingNativeLink(id ,origin_lat, origin_lng, dest_lat, dest_lng, driving_method = 'car') {
    if (driving_method == 'route') driving_method = 'car';
    else if (driving_method == 'foot') driving_method = 'pedestrian';
    else if (driving_method == 'bicycle') driving_method = 'bike';
    var isAndroid = navigator.userAgent.toLowerCase().indexOf("android") > -1;
    var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    var link = document.getElementById(id);
    var href = '';
    if (isIOS) {
        href = `https://neshan.org/maps/routing/${driving_method}/origin/${origin_lat},${origin_lng}/destination/${dest_lat},${dest_lng}`;
    } else if (isAndroid) {
        href = `geo:${dest_lat},${dest_lng}?q=${dest_lat},${dest_lng}`;
    } else {
        href = `https://neshan.org/maps/routing/${driving_method}/origin/${origin_lat},${origin_lng}/destination/${dest_lat},${dest_lng}`;
    }
    link.href = href;
    link.setAttribute("data-desktop-href", href);
}
function route(coordsArray) {
    if (coordsArray.length < 2) {
        $("#sidebarRoutingMapBtn").removeClass("d-none");
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
    var routeLayerLines = [];
    var routeLayerOutLines = [];

    var driver_data = $(".routing-box-item-button").filter(".active").attr("data-driver");
    if (driver_data == undefined)
        driver_data = "route";
    $.ajax({
        url: `https://map.ir/routes/${driver_data}/v1/driving/${cords}`,
        data: {
            steps: true,
            alternatives: true,
        },
        beforeSend: function (request) {
            $("#switch_routing").addClass("is-circular-loading")
            request.setRequestHeader("x-api-key", API_TOKEN);
        },
        error: function() {
            $(".route-page-places-items").html(`
                <p class="mb-0 text-danger py-2 text-center">متاسفانه مسیری یافت نشد.</p>
            `);
        },
        success: function (data, status) {
            const routes = data.routes;
            if (data.routes) {
                $("#sidebarRoutingMapBtn").addClass("d-none");
                waypoint1 = data.waypoints[0].name !== "" ? data.waypoints[0].name : "";
                waypoint2 = data.waypoints[1].name !== "" ? data.waypoints[1].name : "";
                var htmlRoutePlaces = [];
                $.each(routes, function (idxR, val) {
                    routeLayerOutLines[idxR] = [];
                    routeLayerLines[idxR] = [];
                    // for each route (may more than one path be available)
                    $.each(val.legs, function (idx, leg) {
                        distance = formatDistance(leg.distance);
                        duration = formatTime(leg.duration);
                        const legHtml =
                            '<div data-route-id="' +
                            idxR +
                            '" class="route_page_item route-page-places-item d-flex align-items-center p-2 bg-white rounded"><div class="d-flex align-items-center justify-content-between mx-2 w-100"><div class="d-flex flex-column"><span class="fs-14 fw-500 text-darkest">' +
                            waypoint1 +
                            '</span><span class="fs-13 fw-400 text-light-dark mt-2">' +
                            waypoint2 +
                            '</span><span class="fs-13 fw-400 text-light-dark mt-2">' +
                            "از " +
                            leg.summary.replace(",", " به ") +
                            '</span></div><div class="d-flex flex-column"><span class="fs-13 fw-500 text-light-dark text-nowrap">' +
                            duration +
                            '</span><span class="fs-13 fw-400 text-light-dark text-nowrap">' +
                            distance +
                            "</span></div></div></div>";
                        htmlRoutePlaces.push(legHtml);
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
                var cordinations = cords.split(";");
                var originLatLng = cordinations[0].split(',').reverse().join(',');
                var goalLatLng = cordinations[1].split(',').reverse().join(',');
                var origin_lat = originLatLng.split(',')[0]
                var origin_lng = originLatLng.split(',')[1]
                var goal_lat = goalLatLng.split(',')[0]
                var goal_lng = goalLatLng.split(',')[1]
                htmlRoutePlaces.push(`
                    <a href="https://neshan.org/maps/routing/${driver_data}/origin/${originLatLng}/destination/${goalLatLng}"
                       target="_blank"
                       data-desktop-href="https://neshan.org/maps/routing/${driver_data}/origin/${originLatLng}/destination/${goalLatLng}"
                       data-mobile-href="geo:${goalLatLng}?q=${goalLatLng}"
                       class="btn btn-primary mt-3 w-fit mx-auto"
                       id="routing_map_link"
                   >
                       مسیر یابی
                    </a>
                    <script>
                        $(document).ready(() => setRoutingNativeLink('routing_map_link',${origin_lat},${origin_lng},${goal_lat},${goal_lng},'${driver_data}'));
                        $(window).resize(() => setRoutingNativeLink('routing_map_link',${origin_lat},${origin_lng},${goal_lat},${goal_lng},'${driver_data}'));
                    </script>
                `)
                $(".route-page-places-items").html(htmlRoutePlaces);
                processRoutesEvent();
                var startLatLng = L.latLng(coordsArray[0]);
                var endLatLng = L.latLng(coordsArray[1]);
                var bounds = L.latLngBounds(startLatLng, endLatLng);
                map.fitBounds(bounds);
                $(".route-page-places-items").find("[data-route-id]").first().addClass("active");
            }
        },
        complete: function () {
            setTimeout(() => {
                $("#switch_routing").removeClass("is-circular-loading")
            },100)
        }
    });

    function processRoutesEvent() {
        $("[data-route-id]").unbind("click")
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
        $("[data-route-id]").unbind("mouseenter")
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
        $("[data-route-id]").unbind("mouseleave");
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

    route_origin = coordsArray[0]
    route_goal = coordsArray[1]
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

function clearRouteDraw(removeCoords = true) {
    pLineGroup.removeFrom(map);
    pLineGroup = L.layerGroup();
    if (removeCoords) coordsArray = [];
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
function clickMapHandler(latlng, pushing = true) {
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
    route(coordsArray);
    return true;
}

// var saveAsImage = function () {
//     return domtoimage.toPng(document.body)
//         .then(function (dataUrl) {
//             var link = document.createElement('a');
//             link.download = map.printControl.options.documentTitle || "exportedMap" + '.png';
//             link.href = dataUrl;
//             link.click();
//         });
// };
function processLatLng(latLng, callback = () => {}) {
    if (Array.isArray(latLng)) {
        latLng.forEach(latLngs => processLatLng(latLngs, callback));
    } else {
        callback(latLng)
    }
}

var pLineGroup = L.layerGroup();
var coordsArray = [];
var route_origin;
var route_goal;
var routingInputId = "origin_routing_input";
let removeAllPlacesMarkers = () => {};
var panoMarker;
document.addEventListener("DOMContentLoaded", (event) => {
    // start map
    map = L.map("map", {
        attributionControl: false,
        // center: [33.9081949, 50.4677707],
        center: [DEFAULTLAT, DEFAULTLNG],
        zoom: DEFAULTZOOM,
        zoomControl: false,
        contextmenu: true,
        contextmenuWidth: 200,
        closePopupOnClick: false,
        contextmenuItems: [
            {
                text: "تمرکز بر این نقطه",
                icon: PATHFILE + "assets/images/maps/target.png",
                callback: centerMap,
            },
            {
                text: "مسیریابی از این نقطه",
                callback: routingFromHere,
            },
            {
                text: "مسیریابی به این نقطه",
                callback: routingToHere,
            },
            {
                text: "Show coordinates",
                callback: showCoordinates,
            },
            "-",
            {
                text: "بزرگ کردن",
                icon: "data:image/svg+xml,%3Csvg version='1.1' id='Layer_1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' x='0px' y='0px' width='100px' height='100px' fill='%2364748b' viewBox='0 0 122.879 119.801' enable-background='new 0 0 122.879 119.801' xml:space='preserve'%3E%3Cg%3E%3Cpath fill='%2364748b' d='M49.991,0h0.015v0.006c13.794,0.004,26.294,5.601,35.336,14.645c9.026,9.031,14.618,21.515,14.628,35.303h0.006v0.034v0.04 h-0.006c-0.005,5.557-0.918,10.905-2.594,15.892c-0.281,0.837-0.576,1.641-0.877,2.409v0.007c-1.446,3.661-3.315,7.12-5.548,10.307 l29.08,26.14l0.018,0.015l0.157,0.146l0.012,0.012c1.641,1.563,2.535,3.656,2.648,5.779c0.11,2.1-0.538,4.248-1.976,5.971 l-0.011,0.016l-0.176,0.204l-0.039,0.046l-0.145,0.155l-0.011,0.011c-1.563,1.642-3.656,2.539-5.782,2.651 c-2.104,0.111-4.254-0.54-5.975-1.978l-0.012-0.012l-0.203-0.175l-0.029-0.024L78.764,90.865c-0.88,0.62-1.779,1.207-2.687,1.763 c-1.234,0.756-2.51,1.467-3.816,2.117c-6.699,3.342-14.266,5.223-22.27,5.223v0.006h-0.016v-0.006 c-13.797-0.005-26.297-5.601-35.334-14.644l-0.004,0.005C5.608,76.3,0.016,63.81,0.007,50.021H0v-0.033v-0.016h0.007 c0.005-13.799,5.601-26.297,14.646-35.339C23.684,5.607,36.169,0.015,49.958,0.006V0H49.991L49.991,0z M67.787,43.397 c1.21-0.007,2.353,0.312,3.322,0.872l-0.002,0.002c0.365,0.21,0.708,0.454,1.01,0.715c0.306,0.264,0.594,0.569,0.851,0.895h0.004 c0.873,1.11,1.397,2.522,1.394,4.053c-0.003,1.216-0.335,2.358-0.906,3.335c-0.454,0.78-1.069,1.461-1.791,1.996 c-0.354,0.261-0.751,0.496-1.168,0.688v0.002c-0.823,0.378-1.749,0.595-2.722,0.6l-11.051,0.08l-0.08,11.062 c-0.004,1.034-0.254,2.02-0.688,2.886c-0.188,0.374-0.417,0.737-0.678,1.074l-0.006,0.007c-0.257,0.329-0.551,0.644-0.866,0.919 c-1.169,1.025-2.713,1.649-4.381,1.649v-0.007c-0.609,0-1.195-0.082-1.743-0.232c-1.116-0.306-2.115-0.903-2.899-1.689 c-0.788-0.791-1.377-1.787-1.672-2.893v-0.006c-0.144-0.543-0.22-1.128-0.215-1.728v-0.005l0.075-10.945l-10.962,0.076 c-1.209,0.011-2.354-0.31-3.327-0.873l0.002-0.002c-0.37-0.212-0.715-0.458-1.016-0.722c-0.306-0.264-0.589-0.567-0.844-0.891 h-0.004c-0.873-1.112-1.397-2.522-1.393-4.053c0.002-1.213,0.337-2.354,0.906-3.328l-0.004-0.002 c0.376-0.642,0.869-1.225,1.442-1.714h0.004c0.574-0.489,1.236-0.883,1.942-1.151c0.704-0.266,1.484-0.418,2.296-0.423 l11.051-0.082l0.08-11.062c0.004-1.207,0.345-2.345,0.921-3.309l0.004,0.002c0.224-0.374,0.467-0.715,0.727-1.003 c0.264-0.296,0.576-0.584,0.908-0.839l0.005-0.004v0.002c1.121-0.861,2.533-1.379,4.055-1.375c1.211,0.002,2.352,0.332,3.317,0.897 c0.479,0.279,0.928,0.631,1.32,1.025l0.004-0.004c0.383,0.383,0.73,0.834,1.019,1.333c0.56,0.968,0.879,2.104,0.868,3.304 l-0.075,10.942L67.787,43.397L67.787,43.397z M50.006,11.212v0.006h-0.015h-0.034v-0.006C39.274,11.219,29.59,15.56,22.581,22.566 l0.002,0.002c-7.019,7.018-11.365,16.711-11.368,27.404h0.006v0.016v0.033h-0.006c0.006,10.683,4.347,20.365,11.354,27.377 l0.002-0.002c7.018,7.018,16.711,11.365,27.404,11.367v-0.007h0.016h0.033v0.007c10.685-0.007,20.367-4.348,27.381-11.359 c7.012-7.009,11.359-16.702,11.361-27.401H88.76v-0.015v-0.034h0.007C88.76,39.273,84.419,29.591,77.407,22.58v-0.007 C70.398,15.562,60.705,11.214,50.006,11.212L50.006,11.212z'/%3E%3C/g%3E%3C/svg%3E",
                callback: zoomIn,
            },
            {
                text: "کوچک کردن",
                icon: `data:image/svg+xml,%3Csvg version='1.1' id='Layer_1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' x='0px' y='0px' width='100px' height='100px' viewBox='0 0 122.879 119.801' fill='%2364748b' enable-background='new 0 0 122.879 119.801' xml:space='preserve'%3E%3Cg%3E%3Cpath fill='%2364748b' fill-rule='evenodd' clip-rule='evenodd' d='M49.991,0h0.015v0.006c13.794,0.004,26.294,5.601,35.336,14.645 c9.026,9.031,14.618,21.515,14.628,35.303h0.006v0.034v0.04h-0.006c-0.005,5.557-0.918,10.905-2.594,15.892 c-0.281,0.837-0.576,1.641-0.877,2.409v0.007c-1.446,3.661-3.315,7.12-5.548,10.307l29.08,26.14l0.018,0.015l0.157,0.146 l0.012,0.012c1.641,1.563,2.535,3.656,2.648,5.779c0.11,2.1-0.538,4.248-1.976,5.971l-0.011,0.016l-0.176,0.204l-0.039,0.046 l-0.145,0.155l-0.011,0.011c-1.563,1.642-3.656,2.539-5.782,2.651c-2.104,0.111-4.254-0.54-5.975-1.978l-0.012-0.012l-0.203-0.175 l-0.029-0.024L78.764,90.865c-0.88,0.62-1.779,1.207-2.687,1.763c-1.234,0.756-2.51,1.467-3.816,2.117 c-6.699,3.342-14.266,5.223-22.27,5.223v0.006h-0.016v-0.006c-13.797-0.005-26.297-5.601-35.334-14.644l-0.004,0.005 C5.608,76.3,0.016,63.81,0.007,50.021H0v-0.033v-0.016h0.007c0.005-13.799,5.601-26.297,14.646-35.339 C23.684,5.607,36.169,0.015,49.958,0.006V0H49.991L49.991,0z M67.787,43.397c1.21-0.007,2.353,0.312,3.322,0.872l-0.002,0.002 c0.365,0.21,0.708,0.454,1.01,0.715c0.306,0.264,0.594,0.569,0.851,0.895h0.004c0.873,1.11,1.397,2.522,1.394,4.053 c-0.003,1.216-0.335,2.358-0.906,3.335c-0.454,0.78-1.069,1.461-1.791,1.996c-0.354,0.261-0.751,0.496-1.168,0.688v0.002 c-0.823,0.378-1.749,0.595-2.722,0.6l-35.166,0.248c-1.209,0.011-2.354-0.31-3.327-0.873l0.002-0.002 c-0.37-0.212-0.715-0.458-1.016-0.722c-0.306-0.264-0.589-0.567-0.844-0.891h-0.004c-0.873-1.112-1.397-2.522-1.393-4.053 c0.002-1.213,0.337-2.354,0.906-3.328l-0.004-0.002c0.376-0.642,0.869-1.225,1.442-1.714h0.004 c0.574-0.489,1.236-0.883,1.942-1.151c0.704-0.266,1.484-0.418,2.296-0.423L67.787,43.397L67.787,43.397z M50.006,11.212v0.006 h-0.015h-0.034v-0.006C39.274,11.219,29.59,15.56,22.581,22.566l0.002,0.002c-7.019,7.018-11.365,16.711-11.368,27.404h0.006v0.016 v0.033h-0.006c0.006,10.683,4.347,20.365,11.354,27.377l0.002-0.002c7.018,7.018,16.711,11.365,27.404,11.367v-0.007h0.016h0.033 v0.007c10.685-0.007,20.367-4.348,27.381-11.359c7.012-7.009,11.359-16.702,11.361-27.401H88.76v-0.015v-0.034h0.007 C88.76,39.273,84.419,29.591,77.407,22.58v-0.007C70.398,15.562,60.705,11.214,50.006,11.212L50.006,11.212z'/%3E%3C/g%3E%3C/svg%3E`,
                callback: zoomOut,
            },
        ],
    });

    var zoom_level = DEFAULTZOOM;
    map.on("zoomstart zoom zoomend", (ev) => {
        zoom_level = map.getZoom();
        set_push_state(DEFAULTLAT, DEFAULTLNG, map.getZoom());
    });

    map.on("dragend", function (e) {
        set_push_state(map.getCenter().lat, map.getCenter().lng, zoom_level);
    });

    // scale
    if (window.app_config._map_display.scale == 't') 
        L.control
            .scale({
                position: window["app_config"]["_direction"] == "ltr" ? "topright" : "topleft",
                imperial: false,
            })
            .addTo(map);
    
    // mousehover
    if (window.app_config._map_display.latlng == 't') 
        L.control
            .coordinates({
                position: window["app_config"]["_direction"] == "ltr" ? "topright" : "topleft",
            })
        .addTo(map);
    // if (window.app_config._map_display.draw == 't') 
    //     {
            var drawnItems = new L.FeatureGroup();
            map.addLayer(drawnItems);
            var drawnItems = new L.FeatureGroup();
            map.addLayer(drawnItems);
        // }

    // var drawControl = new L.Control.Draw({
    //     draw: {
    //         polygon: false,
    //         polyline: false,
    //         rectangle: false,
    //         marker: false,
    //         circlemarker: false,
    //         circle: true  // Allow user to draw circles only
    //     },
    //     edit: {
    //         featureGroup: drawnItems
    //     }
    // });
    // map.addControl(drawControl);
    //
    // // Event Listener for Created Shapes
    // map.on(L.Draw.Event.CREATED, function (event) {
    //     var layer = event.layer;
    //
    //     if (layer instanceof L.Circle) {
    //         var center = layer.getLatLng();
    //         var radius = layer.getRadius();
    //         console.log(layer.getRadius())
    //         // var bounds = layer.getBounds();
    //         // alert(`Circle Center: ${center.lat}, ${center.lng}\nRadius: ${radius} meters\nBounds: ${bounds.toBBoxString()}`);
    //
    //         // Add Layer to Map
    //         drawnItems.addLayer(layer);
    //     }
    // });

    var placeNodeMarkers = [];
    removeAllPlacesMarkers = removeAllMarkers;

    function removeOutOfViewMarkers() {
        var bounds = map.getBounds();
        placeNodeMarkers = placeNodeMarkers.filter(markerData => {
            if (!bounds.contains(markerData.marker.getLatLng())) {
                map.removeLayer(markerData.marker);
                return false;
            }
            return true;
        });
    }

    function removeAllMarkers() {
        placeNodeMarkers.forEach(markerData => {
            map.removeLayer(markerData.marker);
        });
        placeNodeMarkers = []
    }

    function fetchAndAddMarkers() {
        if (!isActivePlacesMarkers) return;
        var center = map.getCenter();
        var zoom = map.getZoom();

        var alreadyLoaded = placeNodeMarkers.some(marker => {
            return marker.lat === center.lat.toString().slice(0, 6) &&
                marker.lng === center.lng.toString().slice(0, 6) &&
                marker.zoom === zoom;
        });

        if (alreadyLoaded) {
            return;
        }

        var formData = new FormData();
        formData.append("token", TOKEN);
        formData.append("lat", center.lat);
        formData.append("lng", center.lng);
        formData.append("zoom", map.getZoom());

        $.ajax({
            url: PATHFILE + "execute/maps/node_places",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function (markers) {
                markers = JSON.parse(markers);
                if (markers.length) {
                    markers.forEach(item => {
                        var markerExists = placeNodeMarkers.some(marker => marker.id === item.id);

                        if (!markerExists) {
                            var markerIcon = L.icon({
                                iconUrl: item.marker || item.icons || PATHFILE + "assets/images/maps/markers/blue-marker.png",
                                iconSize: [34, 50]
                            });

                            var marker = L.marker([item.lat, item.lng], { icon: markerIcon }, { id: item.id })
                                .addTo(map)
                                .bindPopup('<a href="' + PATHFILE + 'maps/nodes/' + item.id + '/' + item.title + '" target="_blank">' + item.title + '</a>');

                            marker._id = item.id;
                            marker._actualId = item.id;

                            marker.on("click", (event) => {
                                show_sidebar_node(event.target._actualId);
                            });

                            map.addLayer(marker);

                            placeNodeMarkers.push({ id: item.id, marker, lat: center.lat.toString().slice(0, 6), lng: center.lng.toString().slice(0, 6), zoom: zoom });
                        }
                    });
                }
            }
        });
    }

    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    map.on('moveend', debounce(function () {
        removeOutOfViewMarkers();
        if (map.getZoom() >= 17 && !$("aside").hasClass("show")) {
            fetchAndAddMarkers();
        } else if (placeNodeMarkers.length) {
            removeAllMarkers();
        }
    },300));

    map.on('zoomend', debounce(function () {
        removeOutOfViewMarkers();
        if (map.getZoom() >= 17 && !$("aside").hasClass("show")) {
            fetchAndAddMarkers();
        }
    },300));

    L.control.mouseCoordinate({ gpsLong: false, utm: true, utmref: false, gps: false }).addTo(map);

    function showCoordinates(e) {
        alert(e.latlng);
    }

    function centerMap(e) {
        map.panTo(e.latlng);
    }

    function zoomIn(e) {
        map.zoomIn();
    }

    function zoomOut(e) {
        map.zoomOut();
    }

    var miniMap;
    if (window.app_config._map_display.minimap == 't') 
    for(var key in app_config["_map_types"]) {
        if (app_config["_map_types"][key]["default"]) {
            window[app_config["_map_types"][key]["var_name"]].addTo(map).bringToBack();
            if (window[app_config["_map_types"][key]["var_name"]+"Mini"])
                miniMap = new L.Control.MiniMap(window[app_config["_map_types"][key]["var_name"]+"Mini"], {
                    toggleDisplay: false,
                    width: 120,
                    height: 120,
                    zoomAnimation: true,
                    autoToggleDisplay: true,
                    position: window["app_config"]["_direction"] == "ltr" ? "bottomright" : "bottomleft",
                }).addTo(map);
            $(`.${app_config["_map_types"][key]["id"]}`).addClass("active").siblings().removeClass("active");
            // Check layer needs dark mode filter?
            if (app_config["_map_types"][key]["filter"]) 
                $(".leaflet-layer").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
            else
                $(".leaflet-layer").css("filter", "none");
        }
    }


    // // min-map
    // var primaryTileMini = new L.TileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    //     attribution: false,
    //     zoomControl: false,
    //     minZoom: 0,
    //     maxZoom: 22,
    //     maxNativeZoom: 19,
    // });

    // var sateliteTileMini = new L.tileLayer("http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}", {
    //     maxZoom: 20,
    //     subdomains: ["mt0", "mt1", "mt2", "mt3"],
    // });
    // fullscreen
    if (window.app_config._map_display.fullscreen == 't') 
        var mapFullScreen = L.control.fullscreen({ position: window["app_config"]["_direction"] == "ltr" ? "bottomright" : "bottomleft" }).addTo(map);

    // zoomslider
    if (window.app_config._map_display.zoomslider == 't') 
    var mapZoomSlider = L.control.zoomslider({ position: window["app_config"]["_direction"] == "ltr" ? "bottomright" : "bottomleft" }).addTo(map);

    // print
    // L.easyPrint({sizeModes: ["Current"],defaultSizeTitles: { Current: "Current Size" },filename: "myMap",exportOnly: true,hideControlContainer: true}).addTo(map);

    if (window.app_config._map_display.latlng == 't') 
        {
            // mouse
            L.control.coordinates({ position: window["app_config"]["_direction"] == "ltr" ? "topleft" : "topright" }).addTo(map);
            // Coordinate
            L.control.mouseCoordinate({ gpsLong: false, utm: true, utmref: false, gps: false }).addTo(map);
        }

    //   search latlng
    var search_latlng_submit = document.getElementById("search_latlng_submit");
    search_latlng_submit.addEventListener("click", function (e) {
        var search_lat = document.getElementById("search_lat").value;
        var search_lng = document.getElementById("search_lng").value;
        if (search_lat !== "" && search_lng !== "") {
            map.setView([search_lat, search_lng], 16);
        }
    });

    if ($(".switch_layer.active").length > 0) {
        allowMapClick = false
        isActivePlacesMarkers = false;
        removeAllMarkers();
    }
    else {
        allowMapClick = true
        isActivePlacesMarkers = true;
    }

    // Prevent confilicting the map events with the elements inside of it.
    if (document.querySelector(".mapp-layers-button")) L.DomEvent.disableClickPropagation(document.querySelector(".mapp-layers-button"));
    if (document.querySelector(".mapp-layers-button-second")) L.DomEvent.disableClickPropagation(document.querySelector(".mapp-layers-button-second"));
    let clickMapTimeout;
    map.on('click', function (event) {
        clearTimeout(clickMapTimeout);
        clickMapTimeout = setTimeout(() => {
            handleMapClicked(event);
        }, 250); 
    });

    map.on('dblclick', function () {
        clearTimeout(clickMapTimeout);
    });
    // searchLive
    if (window.app_config._map_display.draw == 't') 
        {
            // ruler
            L.control
                .ruler({
                    position: window["app_config"]["_direction"] == "ltr" ? "topright" : "topleft",
                })
                .addTo(map);
        }
    
    
    $(".leaflet-ruler").on("click", function() {
        setTimeout(()=>{
            if ($(".leaflet-ruler").hasClass("leaflet-ruler-clicked")) {
                allowMapClick = false
                isActivePlacesMarkers = false;
                removeAllMarkers();
            } else {
                if ($(".switch_layer.active").length > 0) {
                    allowMapClick = false
                    isActivePlacesMarkers = false;
                    removeAllMarkers();
                }
                else {
                    allowMapClick = true
                    isActivePlacesMarkers = true;
                }
            }
        },50)
    })
    
    // location
    if (window.app_config._map_display.my_location == 't') 
        L.control
            .locate({
                position: window["app_config"]["_direction"] == "ltr" ? "bottomleft" : "bottomright",
            })
            .addTo(map);
    // var drawnItems = new L.FeatureGroup().addTo(map);
    // map.addControl(
    //     new L.Control.Draw({
    //         edit: {
    //             featureGroup: drawnItems,
    //             poly: {
    //                 allowIntersection: false,
    //             },
    //         },
    //         draw: {
    //             polygon: {
    //                 allowIntersection: false,
    //                 showArea: true,
    //             },
    //             circle: false,
    //             marker: false,
    //             circlemarker: false,
    //         },
    //     }),
    // );
    //
    // map.on(L.Draw.Event.CREATED, function (event) {
    //     var layer = event.layer;
    //
    //     drawnItems.addLayer(layer);
    // });

    $(".switch_tile").click(function () {
        $(this).addClass("is-loading")
        map.removeLayer(mapFullScreen)
        map.removeLayer(mapZoomSlider)
        for(var key in app_config["_map_types"]) {
            if ($(this).hasClass(app_config["_map_types"][key]["id"])) {
                // Check if tile layer variable exits
                if (window[app_config["_map_types"][key]["var_name"]]) {
                    window[app_config["_map_types"][key]["var_name"]].addTo(map).bringToBack();
                    if (window[app_config["_map_types"][key]["var_name"] + "Mini"])
                        miniMap?.changeLayer(window[app_config["_map_types"][key]["var_name"] + "Mini"])
                }
                
                $(this).addClass("active").siblings().removeClass("active");
                $(`.${app_config["_map_types"][key]["id"]}`).addClass("active").siblings().removeClass("active");
                // Check layer needs dark mode filter?
                if (app_config["_map_types"][key]["filter"]) 
                    $(".leaflet-layer").css("filter", "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)");
                else
                    $(".leaflet-layer").css("filter", "none");
                
            } else {
                if (window[app_config["_map_types"][key]["var_name"]]) 
                    map.removeLayer(window[app_config["_map_types"][key]["var_name"]])
            }
        }
        mapFullScreen.addTo(map)
        mapZoomSlider.addTo(map)
        setTimeout(() => {
            $(this).removeClass("is-loading")
        }, 100)
    });

    var pano;
    var panoramaInterval;
    var lastClickedToggleBtn = Date.now();

    $(".switch_layer").click(async function () {
        if(!$(this).hasClass("active") && $(this).data('url')?.length)
            window.history.pushState("", "", "/"+$(this).data('url')+"/")
        else
            window.history.pushState("", "", "")
        $(this).toggleClass("active");
        if ($(this).hasClass("360_layer")) {
            if ($(this).hasClass("active")) {
                // create the panorama player with the container
                $("#layers_box").modal("hide");
                if (document.documentElement.clientWidth < 768 && $("aside").hasClass("show")) toggleWithOverlay($("aside"), "show");
                $("#map_360_wrapper").addClass("active");
                $(".mapp-container").addClass("active");
                $("#map_back_btn").addClass("active");
                $("#map_play_btn").addClass("active");
                $(".leaflet-control-container").hide();
                $(".mapp-header").children().hide();
                $(".mapp-header").find(".mapp-search").addClass("mx-2").show();
                $(".bottom-navbar").hide();
                $(".down-section").hide();
                $("#map_close_btn").addClass("active");
                $(".map_360_loader").addClass("active");
                pausePanorama();
                map.invalidateSize();
                var pano_icon = L.divIcon({
                    className: 'leaflet-marker-icon leaflet-control-locate-location leaflet-zoom-animated leaflet-interactive leaflet-control-map-360',
                    iconSize: [32, 32],
                    iconAnchor: [16, 16],
                    html: `<div class="schema-edge"></div><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" version="1.1" viewBox="-12 -12 24 24"><circle r="9" style="stroke:rgb(var(--rgb-first));stroke-width:6;fill:rgb(var(--rgb-first));fill-opacity:1;opacity:1;"><animateTransform attributeName="transform" type="scale" begin="0s" dur="2s" from="1" to="1.5" repeatCount="indefinite" additive="sum" origin="center" /></circle></svg>`
                });

                pano = new pano2vrPlayer("map_360_wrapper");
                var targetLatLng = L.latLng(map.getCenter().lat, map.getCenter().lng); // replace with your lat, lng
                var limitedDistance = 100;
                var minDistance = Infinity;
                var nearesetLayer = {
                    feature: {
                        properties: window["app_config"]["_map_default_360"]
                    }
                };
                const validTypes = ["خیابان اصلی", "خیابان فرعی", "میدان"];
                // Process to find nearest layer to pano marker
                if (app_config["_map_layers"]["street_layer"]?.["scripts"]) {
                    await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["street_layer"]?.["scripts"]);
                }
                (app_config["_map_layers"]["street_layer"]?.["var_name"] ?? []).forEach((var_name,index) => {
                    L.geoJSON(window[var_name]).eachLayer(function (layer) {
                        if (validTypes.includes(layer.feature.properties.Type)) {
                            var layerLatLng = layer.getLatLng ? layer.getLatLng() : null;
                            if (layerLatLng == null) {
                                layer.getLatLngs().forEach(latLngs => processLatLng(latLngs, (latLng) => {
                                    var distance = targetLatLng.distanceTo(latLng);
                                    if (distance < limitedDistance && distance < minDistance) {
                                        minDistance = distance;
                                        nearesetLayer = layer;
                                    }
                                }));
                            } else {
                                var distance = targetLatLng.distanceTo(layerLatLng);
                                if (distance < limitedDistance && distance < minDistance) {
                                    minDistance = distance;
                                    nearesetLayer = layer;
                                }
                            }
                        }
                    });
                })

                setTimeout(() => {
                    if (panoMarker) map.removeLayer(panoMarker);
                    // Define the pano marker
                    panoMarker = L.marker(map.getCenter(), {
                        icon: pano_icon,
                        draggable: true,
                    }).addTo(map);
                    panoMarker.off("dragend");
                    panoMarker.on("dragend", async function (e) {
                        $(".map_360_loader").addClass("active");
                        var target = L.latLng(e.target.getLatLng());
                        // Process to find nearest layer to pano marker on dragend
                        if (app_config["_map_layers"]["street_layer"]?.["scripts"]) {
                            await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["street_layer"]?.["scripts"]);
                        }
                        (app_config["_map_layers"]["street_layer"]?.["var_name"] ?? []).forEach((var_name,index) => {
                            L.geoJSON(window[var_name]).eachLayer(function (layer) {
                                if (validTypes.includes(layer.feature.properties.Type)) {
                                    var layerLatLng = layer.getLatLng ? layer.getLatLng() : null;
                                    if (layerLatLng == null) {
                                        layer.getLatLngs().forEach(latLngs => processLatLng(latLngs, (latLng) => {
                                            var distance = target.distanceTo(latLng);
                                            if (distance < limitedDistance && distance < minDistance) {
                                                minDistance = distance;
                                                nearesetLayer = layer;
                                            }
                                        }))
                                    } else {
                                        var distance = target.distanceTo(layerLatLng);
                                        if (distance < limitedDistance && distance < minDistance) {
                                            minDistance = distance;
                                            nearesetLayer = layer;
                                        }
                                    }
                                }
                            });
                        })
                        minDistance = Infinity;

                        if (nearesetLayer) {
                            try {
                                if (nearesetLayer.feature.properties.Type === "میدان") pano.readConfigUrlAsync(`${app_config["_map_layers"]["360_layer"]["var_name"][0]}Square%20${nearesetLayer.feature.properties.Rel_ID}/pano.xml`);
                                else pano.readConfigUrlAsync(`${app_config["_map_layers"]["360_layer"]["var_name"][0]}Street%20${nearesetLayer.feature.properties.Rel_ID}/pano.xml`);
                            } catch (error) {
                                console.log("error", error);
                            } finally {
                                nearesetLayer = null
                                minDistance = Infinity
                            }
                        } else {
                            snackbar("element_8543258459", "برای این منطقه پانورامایی یافت نشد", "error", {hasIcon: true});
                        }
                        // Process to get the nearest node to pano marker in layer
                        var nearestNodeId;
                        var minNodeDistance = Infinity;
                        pano.removeEventListener("configloaded", configLoadedHandle);
                        pano.on("configloaded", configLoadedHandle);
                        var nodesProcessed = false
                        function configLoadedHandle() {
                            if (!nodesProcessed) {
                                $.each(pano.getNodeIds(), function (i, nodeId) {
                                    if (pano.getNodeLatLng(nodeId).length) {
                                        var nodeLatLng = L.latLng(pano.getNodeLatLng(nodeId));
                                        var distance = target.distanceTo(nodeLatLng);
                                        if (distance < limitedDistance && distance < minNodeDistance) {
                                            minNodeDistance = distance;
                                            nearestNodeId = nodeId;
                                        }
                                    }
                                });
                                nodesProcessed = true
                            }
                            minNodeDistance = Infinity;
                            if (nearestNodeId) {
                                $(".map_360_loader").addClass("active");
                                var nextPanoramaUrl = "{" + nearestNodeId + "}";
                                // Open the next panorama in the tour, changing the node
                                pano.openNext(nextPanoramaUrl, "");
                                // pano.loadScene(nearestNodeId)
                                var panoLatLng = pano.getNodeLatLng();
                                if (panoLatLng.length) {
                                    panoMarker.setLatLng(panoLatLng).update();
                                    map.setView(panoLatLng, 17);
                                } else {
                                    console.error("pano lat lng not found!")
                                }
                                nearestNodeId = null;
                            }
                        }
                    });
                    const schemaEdge = document.getElementsByClassName("schema-edge")[0]
                    schemaEdge.addEventListener("mousedown", () => {
                        panoMarker.dragging?.disable();
                        map.dragging?.disable();
                    });
                    schemaEdge.addEventListener("touchstart", () => {
                        panoMarker.dragging?.disable();
                        map.dragging?.disable();
                    });
                    document.addEventListener("touchend", () => {
                        panoMarker.dragging?.enable();
                        map.dragging?.enable();
                    });
                    // Re-enable dragging when needed (e.g., after releasing the schema-edge)
                    document.addEventListener("mouseup", () => {
                        panoMarker.dragging?.enable();
                        map.dragging?.enable();
                    });

                    let startAngle = 0;
                    schemaEdge.addEventListener("touchstart", (event) => {
                        const touch = event.touches[0];
                        isDraggingSchema = true;
                        const rect = schemaEdge.getBoundingClientRect();
                        const centerX = rect.left + rect.width / 2;
                        const centerY = rect.top + rect.height / 2;
                        initialAngle = Math.atan2(touch.clientY - centerY, touch.clientX - centerX);
                        $("#map_pause_btn").click();
                    });

                    schemaEdge.addEventListener("touchmove", (event) => {
                        const touch = event.touches[0];
                        const rect = schemaEdge.getBoundingClientRect();
                        const centerX = rect.left + rect.width / 2;
                        const centerY = rect.top + rect.height / 2;
                        const currentAngle = Math.atan2(touch.clientY - centerY, touch.clientX - centerX);
                        const angleDiff = currentAngle - initialAngle;
                        const rotation = angleDiff * (180 / Math.PI);
                        // Apply rotation to the element
                        pano.setPanNorth(-rotation)
                        schemaEdge.style.transformOrigin = "center center";
                        schemaEdge.style.transform = `translate(-50%,-50%) rotate(${-rotation}deg)`;
                    });

                    schemaEdge.addEventListener("touchend", () => {
                        isDraggingSchema = false;
                    });

                    let isDraggingSchema = false;
                    let initialAngle = 0;
                    
                    schemaEdge.addEventListener('mousedown', function(e) {
                        isDraggingSchema = true;
                        const rect = schemaEdge.getBoundingClientRect();
                        const centerX = rect.left + rect.width / 2;
                        const centerY = rect.top + rect.height / 2;
                        initialAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                        $("#map_pause_btn").click();
                    });

                    document.addEventListener('mousemove', function(e) {
                        if (isDraggingSchema) {
                            const rect = schemaEdge.getBoundingClientRect();
                            const centerX = rect.left + rect.width / 2;
                            const centerY = rect.top + rect.height / 2;
                            const currentAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                            const angleDiff = currentAngle - initialAngle;
                            const rotation = angleDiff * (180 / Math.PI);
                            // Apply rotation to the element
                            pano.setPanNorth(-rotation)
                            schemaEdge.style.transformOrigin = "center center";
                            schemaEdge.style.transform = `translate(-50%,-50%) rotate(${-rotation}deg)`;
                        }
                    });

                    // Add mouseup event listener
                    document.addEventListener('mouseup', function(e) {
                        isDraggingSchema = false;
                        const rect = schemaEdge.getBoundingClientRect();
                        const centerX = rect.left + rect.width / 2;
                        const centerY = rect.top + rect.height / 2;
                        initialAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                    });

                    var nearestNodeId = 256;
                    var minNodeDistance = Infinity;
                    pano.removeEventListener("configloaded", configLoadedHandle);
                    pano.on("configloaded", configLoadedHandle);
                    function configLoadedHandle() {
                        nearestNodeId = pano.getNodeIds()[0]
                        if (nearestNodeId) {
                            var nextPanoramaUrl = "{" + nearestNodeId + "}";
                            // Open the next panorama in the tour, changing the node
                            pano.openNext(nextPanoramaUrl, "");
                            // pano.loadScene(nearestNodeId)
                            var panoLatLng = pano.getNodeLatLng();
                            if (panoLatLng.length) {
                                panoMarker.setLatLng(panoLatLng).update();
                                map.setView(panoLatLng, 17);
                            } else {
                                console.error("pano lat lng not found!")
                            }
                            nearestNodeId = null;
                            minNodeDistance = Infinity;
                            const schemaEdge = document.getElementsByClassName("schema-edge")[0]
                            if (schemaEdge) schemaEdge.style.transform = `translate(-50%,-50%) rotate(${-pano.getPanNorth()}deg)`;
                        }
                    }
                    // load the configuration
                    if (nearesetLayer) {
                        try {
                            if (nearesetLayer.feature.properties.Type === "میدان") pano.readConfigUrlAsync(`${app_config["_map_layers"]["360_layer"]["var_name"][0]}Square%20${nearesetLayer.feature.properties.Rel_ID}/pano.xml`);
                            else pano.readConfigUrlAsync(`${app_config["_map_layers"]["360_layer"]["var_name"][0]}Street%20${nearesetLayer.feature.properties.Rel_ID}/pano.xml`);
                        } catch (error) {
                            console.log("error", error);
                        } finally {
                            nearesetLayer = null
                            minDistance = Infinity
                        }
                    } else {
                        snackbar("element_8543258459", "برای این منطقه پانورامایی یافت نشد", "error", {hasIcon: true});
                    }
    
                    pano.on("beforechangenode", function () {
                        $(".map_360_loader").addClass("active");
                    });
                    pano.on("positionchanged", function() {
                        const schemaEdge = document.getElementsByClassName("schema-edge")[0]
                        if (schemaEdge) schemaEdge.style.transform = `translate(-50%,-50%) rotate(${-pano.getPanNorth()}deg)`;
                    }) 
                    pano.on("changenode", function () {
                        var panoLatLng = pano.getNodeLatLng();
                        if (panoLatLng.length) {
                            panoMarker.setLatLng(panoLatLng).update();
                            map.setView(panoLatLng, 17);
                        } else {
                            console.error("pano lat lng not found!")
                        }
                        panoMarker.off("dragend");
                        panoMarker.on("dragend", async function (e) {
                            $(".map_360_loader").addClass("active");
                            var target = L.latLng(e.target.getLatLng());
                            if (app_config["_map_layers"]["street_layer"]?.["scripts"]) {
                                await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["street_layer"]?.["scripts"]);
                            }
                            (app_config["_map_layers"]["street_layer"]?.["var_name"] ?? []).forEach((var_name,index) => {
                                L.geoJSON(window[var_name]).eachLayer(function (layer) {
                                    if (validTypes.includes(layer.feature.properties.Type)) {
                                        var layerLatLng = layer.getLatLng ? layer.getLatLng() : null;
                                        if (layerLatLng == null) {
                                            layer.getLatLngs().forEach(latLngs => processLatLng(latLngs, (latLng) => {
                                                var distance = target.distanceTo(latLng);
                                                if (distance < limitedDistance && distance < minDistance) {
                                                    minDistance = distance;
                                                    nearesetLayer = layer;
                                                }
                                            }))
                                        } else {
                                            var distance = target.distanceTo(layerLatLng);
                                            if (distance < limitedDistance && distance < minDistance) {
                                                minDistance = distance;
                                                nearesetLayer = layer;
                                            }
                                        }
                                    }
                                });
                            })
                            minDistance = Infinity;
                            if (nearesetLayer) {
                                try {
                                    if (nearesetLayer.feature.properties.Type === "میدان") pano.readConfigUrlAsync(`${app_config["_map_layers"]["360_layer"]["var_name"][0]}Square%20${nearesetLayer.feature.properties.Rel_ID}/pano.xml`);
                                    else pano.readConfigUrlAsync(`${app_config["_map_layers"]["360_layer"]["var_name"][0]}Street%20${nearesetLayer.feature.properties.Rel_ID}/pano.xml`);
                                } catch (error) {
                                    console.log("error", error);
                                } finally {
                                    nearesetLayer = null
                                    minDistance = Infinity
                                }
                            } else {
                                snackbar("element_8543258459", "برای این منطقه پانورامایی یافت نشد", "error", { hasIcon: true });
                            }
    
                            var nearestNodeId;
                            var minNodeDistance = Infinity;
                            minNodeDistance = Infinity;
                            pano.removeEventListener("configloaded", configLoadedHandle);
                            pano.on("configloaded", configLoadedHandle);
                            var nodesProcessed = false
                            function configLoadedHandle() {
                                if (!nodesProcessed) {
                                    $.each(pano.getNodeIds(), function (i, nodeId) {
                                        if (pano.getNodeLatLng(nodeId).length) {
                                            var nodeLatLng = L.latLng(pano.getNodeLatLng(nodeId));
                                            var distance = target.distanceTo(nodeLatLng);
                                            if (distance < limitedDistance && distance < minNodeDistance) {
                                                minNodeDistance = distance;
                                                nearestNodeId = nodeId;
                                            }
                                        }
                                    });
                                    nodesProcessed = true
                                }
                                if (nearestNodeId) {
                                    var nextPanoramaUrl = "{" + nearestNodeId + "}";
                                    // Open the next panorama in the tour, changing the node
                                    pano.openNext(nextPanoramaUrl, "");
                                    // pano.loadScene(nearestNodeId)
                                    var panoLatLng = pano.getNodeLatLng();
                                    if (panoLatLng.length) {
                                        panoMarker.setLatLng(panoLatLng).update();
                                        map.setView(panoLatLng, 17);
                                    } else {
                                        console.error("pano lat lng not found!")
                                    }
                                    nearestNodeId = null;
                                    minNodeDistance = Infinity;
                                    const schemaEdge = document.getElementsByClassName("schema-edge")[0]
                                    if (schemaEdge) schemaEdge.style.transform = `translate(-50%,-50%) rotate(${-pano.getPanNorth()}deg)`;
                                }
                            }
                        });
    
                        map.setView(panoLatLng, 17);
                    });
    
                    pano.on("imagesready", function () {
                        setTimeout(() => {
                            $(".map_360_loader").removeClass("active");
                        }, 100);
                    });
                }, 400);

                $("#map_play_btn").unbind("click");
                $("#map_play_btn").on("click", function () {
                    if (pano.getIsTour()) {
                        playPanorama();
                        $("#map_pause_btn").addClass("active");
                        $(this).removeClass("active");
                    }
                });
                $("#map_pause_btn").unbind("click");
                $("#map_pause_btn").on("click", function () {
                    pausePanorama();
                    $("#map_play_btn").addClass("active");
                    $(this).removeClass("active");
                });

                $("#map_360_wrapper").unbind("click drag");
                $("#map_360_wrapper").on("click drag", function () {
                    $("#map_pause_btn").click();
                });
                function playPanorama() {
                    if (pano.getIsTour()) {
                        panoramaInterval = setInterval(() => {
                            var currnetPan = pano.getPan();
                            var currentTilt = pano.getTilt();
                            var currentFov = pano.getFov();
                            var nextPanoramaUrl;
                            if (pano.getPanN() < 45 && pano.getPanN() > -135) {
                                nextPanoramaUrl = "{" + pano.getPrevNode() + "}";
                            } else {
                                nextPanoramaUrl = "{" + pano.getNextNode() + "}";
                            }
                            // Open the next panorama in the tour, changing the node
                            pano.openNext(nextPanoramaUrl, "");
                            pano.moveToDefaultView();
                            pano.setPan(currnetPan);
                            pano.setTilt(currentTilt);
                            pano.setFov(currentFov);
                        }, 1500);
                    }
                }
                function pausePanorama() {
                    if (panoramaInterval) clearInterval(panoramaInterval);
                    panoramaInterval = null;
                }

                if (window.navigator.userAgent.match(/Safari/i)) {
                    // fix for white borders, rotation on iPhone
                    function iosHfix(e) {
                        window.scrollTo(0, 1);
                        var container = document.getElementById("map_360_wrapper");
                        var oh = container.offsetHeight;
                        document.documentElement.style.setProperty("height", "100vh");
                        if (oh != container.offsetHeight) {
                            container.style.setProperty("height", "100%");
                        } else {
                            container.style.setProperty("height", window.innerHeight + "px");
                        }
                        window.scrollTo(0, 0);
                        pano.setViewerSize(container.offsetWidth, container.offsetHeight);
                    }
                    setTimeout(iosHfix, 0);
                    setTimeout(iosHfix, 100);
                    window.addEventListener("resize", function () {
                        setTimeout(iosHfix, 0);
                        // hide toolbar on iPad happens with a delay
                        setTimeout(iosHfix, 500);
                        setTimeout(iosHfix, 1000);
                        setTimeout(iosHfix, 2000);
                    });
                }

            } else {
                $("#map_pause_btn").click();
                clearInterval(panoramaInterval);
                $("#map_360_wrapper").removeClass("active");
                $(".mapp-container").removeClass("active");
                $("#map_back_btn").removeClass("active");
                $("#map_play_btn").removeClass("active");
                $(".leaflet-control-container").show();
                $(".mapp-header").children().show();
                $(".mapp-header").find(".mapp-search").removeClass("mx-2").show();
                $(".bottom-navbar").show();
                $(".down-section").show();
                $("#map_close_btn").removeClass("active");
                $(".map_360_loader").removeClass("active");
                $(".mapp-container").removeClass("hidden-map");
                $("#map_360_wrapper").removeClass("full");
                if (panoMarker) map.removeLayer(panoMarker);
                map.invalidateSize();
                var nextPanoramaUrl = "{" + pano.getCurrentNode() + "}";
                // Open the next panorama in the tour, changing the node
                pano.openNext(nextPanoramaUrl, "");
                pano.updatePanorama();
            }
        }
        if ($(".switch_layer.active").length > 0) {
            allowMapClick = false
            isActivePlacesMarkers = false;
            removeAllMarkers();
        }
        else {
            allowMapClick = true
            isActivePlacesMarkers = true;
        }
    });

    $("#map_back_btn").on("click", function () {
        $("#map_pause_btn").click();
        clearInterval(panoramaInterval);
        $("#map_360_wrapper").removeClass("active");
        $(".mapp-container").removeClass("active");
        $("#map_back_btn").removeClass("active");
        $("#map_play_btn").removeClass("active");
        $(".360_layer").removeClass("active");
        $(".leaflet-control-container").show();
        $(".mapp-header").children().show();
        $(".mapp-header").find(".mapp-search").addClass("mx-2").show();
        $(".bottom-navbar").show();
        $(".down-section").show();
        $("#map_close_btn").removeClass("active");
        $(".map_360_loader").removeClass("active");
        $(".mapp-container").removeClass("hidden-map");
        $("#map_360_wrapper").removeClass("full");
        if (panoMarker) map.removeLayer(panoMarker);
        map.invalidateSize();
        if ($(".switch_layer.active").length > 0) {
            allowMapClick = false
            isActivePlacesMarkers = false;
            removeAllMarkers();
        }
        else {
            allowMapClick = true
            isActivePlacesMarkers = true;
        }
    });

    $("#map_close_btn").on("click", function () {
        if (Date.now() - lastClickedToggleBtn < 1100) {
            return;
        } else {
            lastClickedToggleBtn = Date.now();
        }
        $("#map_360_wrapper").toggleClass("full");
        $(".mapp-container").toggleClass("hidden-map");
        if ($(".mapp-container").hasClass("hidden-map")) {
            $(".map_360_loader").addClass("full");
            $(this).find("span").text("بازکردن نقشه");
        } else {
            $(".map_360_loader").removeClass("full");
            $(this).find("span").text("بستن نقشه");
        }
        map.invalidateSize();
        var nextPanoramaUrl = "{" + pano.getCurrentNode() + "}";
        // Open the next panorama in the tour, changing the node
        pano.openNext(nextPanoramaUrl, "");
        pano.updatePanorama();
    });
    // Theme changed handle start
    const themeTileManager = {
        currentTile: null,
        currentTileId: null,
        miniMap: null,
        
        init: function(miniMapInstance) {
            this.miniMap = miniMapInstance;
            this.setupInitialTile();
        },
        
        setupInitialTile: function() {
            const isDarkMode = getCookie("theme_mode") === themeCustomDarkClass;
            const defaultTileKey = this.findDefaultTile();
            
            if (isDarkMode) {
                const darkTileKey = this.findDarkVariant(defaultTileKey);
                const tileKeyToUse = darkTileKey || defaultTileKey;
                this.switchToTile(tileKeyToUse, true);
            } else {
                this.switchToTile(defaultTileKey, false);
            }
        },
        
        findDefaultTile: function() {
            for (const key in app_config["_map_types"]) {
                if (app_config["_map_types"][key]["default"] === true) {
                    return key;
                }
            }
            return Object.keys(app_config["_map_types"])[0];
        },
        
        findDarkVariant: function(tileKey) {
            if (app_config["_map_types"][tileKey]?.filter === true) {
                return tileKey;
            }
            
            for (const key in app_config["_map_types"]) {
                if (key === tileKey + "_dark" || 
                    (app_config["_map_types"][key].id === app_config["_map_types"][tileKey].id + "_dark")) {
                    return key;
                }
            }
            return null;
        },
        
        findLightVariant: function(tileKey) {
            if (app_config["_map_types"][tileKey]?.filter === false) {
                return tileKey;
            }
            
            const baseId = app_config["_map_types"][tileKey].id;
            const lightId = baseId.replace("_dark", "");
            
            for (const key in app_config["_map_types"]) {
                if (app_config["_map_types"][key].id === lightId) {
                    return key;
                }
            }
            return null;
        },
        
        switchToTile: function(tileKey, isDarkMode) {
            const tileConfig = app_config["_map_types"][tileKey];
            if (!tileConfig || !window[tileConfig.var_name]) return;
            
            if (this.currentTile) {
                map.removeLayer(this.currentTile);
            }
            
            this.currentTile = window[tileConfig.var_name];
            this.currentTileId = tileConfig.id;
            this.currentTile.addTo(map).bringToBack();
            
            if (this.miniMap && window[tileConfig.var_name + "Mini"]) {
                this.miniMap.changeLayer(window[tileConfig.var_name + "Mini"]);
            }
            
            this.updateActiveClasses(tileConfig.id);
            
            this.applyTileFilter(tileConfig.filter);
        },
        
        updateActiveClasses: function(tileId) {
            document.querySelectorAll(".switch_tile.active").forEach(el => {
                el.classList.remove("active");
            });
            
            const tileElement = document.querySelector(`.${tileId}`);
            if (tileElement) {
                tileElement.classList.add("active");
            }
        },
        
        applyTileFilter: function(shouldFilter) {
            const filterValue = shouldFilter ? 
                "invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%)" : 
                "none";
            
            document.querySelectorAll(".leaflet-layer").forEach(layer => {
                layer.style.filter = filterValue;
            });
        },
        
        onThemeChange: function(isDarkMode) {
            if (this.currentTileId) {
                let targetTileKey = null;
                
                if (isDarkMode) {
                    for (const key in app_config["_map_types"]) {
                        if (app_config["_map_types"][key].id === this.currentTileId + "_dark") {
                            targetTileKey = key;
                            break;
                        }
                    }
                    
                    if (!targetTileKey) {
                        targetTileKey = this.findDarkVariant(this.findDefaultTile());
                    }
                } else {
                    if (this.currentTileId.endsWith("_dark")) {
                        const lightTileId = this.currentTileId.replace("_dark", "");
                        for (const key in app_config["_map_types"]) {
                            if (app_config["_map_types"][key].id === lightTileId) {
                                targetTileKey = key;
                                break;
                            }
                        }
                    } else {
                        targetTileKey = this.findDefaultTile();
                    }
                }
                
                if (targetTileKey) {
                    this.switchToTile(targetTileKey, isDarkMode);
                }
            }
        },
        
        getActiveTileKey: function() {
            return this.currentTileId;
        }
    };

    function handleTileSwitch(e) {
        const tileElement = e.target.closest(".switch_tile");
        if (!tileElement) return;
        
        const tileId = Array.from(tileElement.classList)
            .find(cls => cls !== "switch_tile" && cls !== "active");
        
        if (!tileId) return;
        
        let targetTileKey = null;
        for (const key in app_config["_map_types"]) {
            if (app_config["_map_types"][key].id === tileId) {
                targetTileKey = key;
                break;
            }
        }
        
        if (targetTileKey) {
            const isDarkMode = getCookie("theme_mode") === themeCustomDarkClass;
            themeTileManager.switchToTile(targetTileKey, isDarkMode);
        }
    }

    function handleThemeChange(e, data) {
        const isDarkMode = data.themeName === themeCustomDarkClass;
        themeTileManager.onThemeChange(isDarkMode);
    }

    $(document).ready(function() {
        themeTileManager.init(miniMap);
        document.querySelectorAll(".switch_tile").forEach(el => {
            el.addEventListener("click", handleTileSwitch);
        });
    });
    $(document).on("themeChanged", handleThemeChange);
    $("#layers_box").click(function () {
        $(".mapp-layers-button").removeClass("active");
    });
    $(".routing-button").click(function () {
        allowMapClick = false
        isActivePlacesMarkers = false;
        removeAllMarkers();
        if (!$("#routing-page").hasClass("active")) {
            $("#routing-page").fadeIn().show().addClass("active").siblings().fadeOut().hide().removeClass("active");
        }
        //اگر مقصد انتخاب شده بود(مورد استفاده در  لیست اماکن)
        if ($(this).attr("data-status") == "onlyOrigin") {
            route_origin = map.getCenter();
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
                lat: map.getCenter().lat,
                lng: map.getCenter().lng,
            };
            clickMapHandler(origin_latlng, false);
            origin_getAddress(route_origin.lat, route_origin.lng);
            if (coordsArray.length > 1) {
                $(this).attr("data-status", "origin");
                $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
            <div class="d-flex align-items-center">
                <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
            </div>
            <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                <div class="d-flex flex-column">
                    <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                </div>
            </div>
            <span class="circular-loading"></span>
        </div>`);
                $(".marker_center").hide();
                $(this).removeClass("active");
                $(".leaflet-control-container").show();
                $(".down-section").show();
            } else {
                $(".marker_center").show();
                $(this).text("انتخاب مقصد");
                $(this).attr("data-status", "goal");
                $(this).addClass("active");
            }
            // routingToSelectedPointA(origin_latlng)
            return;
        } else if ($(this).attr("data-status") == "origin") {
            route_origin = map.getCenter();
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
                lat: map.getCenter().lat,
                lng: map.getCenter().lng,
            };
            clickMapHandler(origin_latlng, false);
            origin_getAddress(route_origin.lat, route_origin.lng);
            if (coordsArray.length > 1) {
                $(".marker_center").hide();
                $(this).removeClass("active");
                $(".leaflet-control-container").show();
                $(".down-section").show();
            } else {
                $(".marker_center").show();
                $(this).text("انتخاب مقصد");
                $(this).attr("data-status", "goal");
                $(".routing-button").addClass("active");
            }
        } else {
            route_goal = map.getCenter();
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
            var goal_latlng = { lat: map.getCenter().lat, lng: map.getCenter().lng };
            clickMapHandler(goal_latlng, true);
            goal_getAddress(route_goal.lat, route_goal.lng);
            if (route_origin?.lat && route_origin?.lng) origin_getAddress(route_origin.lat, route_origin.lng);
            if (coordsArray.length > 1) {
                $(this).attr("data-status", "origin");
                $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
            <div class="d-flex align-items-center">
                <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
            </div>
            <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                <div class="d-flex flex-column">
                    <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                </div>
            </div>
            <span class="circular-loading"></span>
        </div>`);
                $(".marker_center").hide();
                $(this).removeClass("active");
                $(".leaflet-control-container").show();
                $(".down-section").show();
            } else {
                $(".marker_center").show();
                $(this).text("انتخاب مبدا");
                $(this).attr("data-status", "origin");
                $(this).addClass("active");
            }
        }
    });

    function routingFromHere(e) {
        // مبدا
        // process of origin route
        if (coordsArray.length > 1) {
            $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
            <div class="d-flex align-items-center">
                <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
            </div>
            <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                <div class="d-flex flex-column">
                    <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                </div>
            </div>
            <span class="circular-loading"></span>
        </div>`);
            clearRoute();
        }
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
        origin_getAddress(route_origin.lat, route_origin.lng);
        if (coordsArray.length > 1) {
            $(".marker_center").hide();
            $(".routing-button").removeClass("active");
            $(".leaflet-control-container").show();
            $(".down-section").show();
        } else {
            $(".marker_center").show();
            $(".routing-button").text("انتخاب مقصد");
            $(".routing-button").attr("data-status", "goal");
            $(".routing-button").addClass("active");
            $(".leaflet-control-container").hide();
            $(".down-section").hide();
        }
    }

    function routingToHere(e) {
        // مقصد
        // process of goal route
        if (coordsArray.length > 1) {
            $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
            <div class="d-flex align-items-center">
                <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
            </div>
            <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                <div class="d-flex flex-column">
                    <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                </div>
            </div>
            <span class="circular-loading"></span>
        </div>`);
            clearRoute();
        }
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
        goal_getAddress(route_goal.lat, route_goal.lng);
        if (coordsArray.length > 1) {
            $(".routing-button").attr("data-status", "origin");
            $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
            <div class="d-flex align-items-center">
                <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
            </div>
            <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                <div class="d-flex flex-column">
                    <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                </div>
            </div>
            <span class="circular-loading"></span>
        </div>`);
            $(".marker_center").hide();
            $(".routing-button").removeClass("active");
            $(".leaflet-control-container").show();
            $(".down-section").show();
        } else {
            $(".marker_center").show();
            $(".routing-button").text("انتخاب مبدا");
            $(".routing-button").attr("data-status", "origin");
            $(".routing-button").addClass("active");
        }
    }

    $("#switch_routing").on("click", function () {
        if (route_goal && route_origin) {
            var goal_icon = null, 
                origin_icon = null;
            const route_goal_const = route_goal;
            route_goal = route_origin;
            route_origin = route_goal_const;
            if (goal_marker && origin_marker) {
                const goal_marker_const = goal_marker;
                goal_marker = origin_marker;
                origin_marker = goal_marker_const;
            } else {
                if (goal_marker) {
                    origin_icon = L.icon({
                        iconSize: [27, 41],
                        iconUrl: "../assets/images/maps/markers/origin-marker.png"
                    });
                }
                if (origin_marker) {
                    goal_icon = L.icon({
                        iconSize: [27, 41],
                        iconUrl: "../assets/images/maps/markers/goal-marker.png"
                    });
                }
            }
            clearRoute();

            if (goal_marker && !origin_icon) {
                origin_icon = L.icon({
                    ...goal_marker.options.icon.options,
                });
            }

            if (origin_marker && !goal_icon) {
                goal_icon = L.icon({
                    ...origin_marker.options.icon.options,
                });
            }

            // process of origin route
            if (origin_marker)
                map.removeLayer(origin_marker);
            if (origin_icon) {
                origin_marker = L.marker([route_origin.lat, route_origin.lng], {
                    icon: origin_icon,
                    draggable: true,
                }).addTo(map);
                origin_marker.on("dragend", setOriginMarker);
            } else {
                origin_marker = null
            }
            
            var origin_latlng = {
                lat: route_origin.lat,
                lng: route_origin.lng,
            };
            clickMapHandler(origin_latlng, false);
            origin_getAddress(route_origin.lat, route_origin.lng);

            // process of goal route
            if (goal_marker)
                map.removeLayer(goal_marker);
            if (goal_icon) {
                goal_marker = L.marker([route_goal.lat, route_goal.lng], {
                    icon: goal_icon,
                    draggable: true,
                }).addTo(map);
                goal_marker.on("dragend", setGoalMarker);
            } else {
                goal_marker = null
            }
            
            var goal_latlng = { lat: route_goal.lat, lng: route_goal.lng };
            clickMapHandler(goal_latlng, true);
            goal_getAddress(route_goal.lat, route_goal.lng);
        } else {
            snackbar("map_snackbar_18394829", "ابتدا مبدا و مقصد مسیریابی را مشخص نمایید.", "danger", {
                hasIcon: true,
            });
        }
    });

    $(".routing-page-back-button").click(function () {
        clearRoute();
        $(".marker_center").hide();
        $("#sidebarRoutingMapBtn").removeClass("d-none");
        $("#routing_setting_button").removeClass("active");
        origin_marker = null;
        goal_marker = null;
        routingInputId = "origin_routing_input";
        route_goal = null
        route_origin = null
    });
    // Start Routing Feature
    var routingTimeout;
    $(".routing_input").on("input", function (e) {
        routingInputId = e.target.id;
        var searchInput = $("#" + routingInputId).val();
        if (searchInput != "") {
            var raw = JSON.stringify({
                text: searchInput,
                $filter: DEFAULTSRCH,
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
            var addresses = document.querySelector(".route-page-places-items");
            addresses.innerHTML = `
            <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
            <div class="d-flex align-items-center">
                <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
            </div>
            <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                <div class="d-flex flex-column">
                    <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                </div>
            </div>
            <span class="circular-loading"></span>
        </div>`;
            if (routingTimeout) clearTimeout(routingTimeout);
            routingTimeout = setTimeout(async function () {
                fetch("https://map.ir/search/v2/autocomplete", requestOptions)
                    .then((res) => {
                        if (res.status == 200) {
                            return res.json();
                        }
                        return new Error("Error :/");
                    })
                    .then((data) => {
                        if (data.value) {
                            data.value.forEach((address) => {
                                addresses.insertAdjacentHTML(
                                    "beforeend",
                                    `<div class="route-page-places-item cursor-pointer p-2 rounded d-flex align-items-center bg-white" data-lat="${address.geom.coordinates[1]}" data-lng="${address.geom.coordinates[0]}" onclick="targetLocationRouting(this)">
                      <div class="d-flex align-items-center">
                          <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
                      </div>
                      <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                          <div class="d-flex flex-column">
                              <span class="fs-13 fw-500 text-darkest">${address.title}</span>
                              <span class="fs-13 fw-400 text-light-dark">${address.address}</span>
                          </div>
                      </div>
                  </div>`,
                                );
                            });
                        }
                    });
            }, timeoutDelay);
        }
    });

    var timeoutLocation;
    $("[data-current-location-select]").on("click", function () {
        map.locate({ setView: true, maxZoom: 16 });
        if (timeoutLocation) clearTimeout(timeoutLocation);
        timeoutLocation = setTimeout(() => {
            map.on("locationfound", function (e) {
                if (document.documentElement.clientWidth < 768 && $("aside").hasClass("show")) toggleWithOverlay($("aside"), "show");
                var latLng = e.latlng;
                // if (current_marker) map.removeLayer(current_marker)
                // var current_icon=L.icon({
                //     iconUrl: PATHFILE+"assets/images/maps/markers/blue-marker.png",
                //     iconSize: [34, 50],
                // })
                // current_marker=new L.marker(current_route, { icon: current_icon }).addTo(map).bindTooltip("موقعیت مکانی من", {
                //     direction: "top",
                //     className: "search-leaflet-tooltip"
                // }).openTooltip()
                map.off("locationfound")
            });
            map.on("locationerror", async function (e) {
                snackbar("map_snackbar_18394829", "موقعیت مکانی شما یافت نشد. در حال تلاش از طریق آی‌پی...", "warning", {
                    hasIcon: true,
                });

                await fetchAndCenterLocation(true);
            });
        }, 200);
    });

    async function fetchAndCenterLocation(panToLocation = true) {
        try {
            const position = await getLocation();
            const { latitude, longitude, accuracy, heading } = position.coords;
            if (panToLocation) {
                const latLng = [latitude, longitude];

                // *****
                if (current_marker) map.removeLayer(current_marker)
                var current_icon=L.icon({
                    iconUrl: PATHFILE+"assets/images/maps/markers/blue-marker.png",
                    iconSize: [34, 50],
                })
                current_marker=new L.marker(latLng, { icon: current_icon }).addTo(map).bindTooltip("موقعیت مکانی من", {
                    direction: "top",
                    className: "search-leaflet-tooltip"
                }).openTooltip()
            }
        } catch (err) {
            let message = "خطای ناشناخته‌ای رخ داد";
            switch (err.code) {
                case err.PERMISSION_DENIED:
                    message = "دسترسی لازم به موقعیت یاب داده نشد";
                    break;
                case err.POSITION_UNAVAILABLE:
                    message = "در حال حاضر اطلاعات مکانی قابل دسترسی نیست";
                    break;
                case err.TIMEOUT:
                    message = "در حال حاضر سرویس geoLocation قابل دسترسی نیست";
                    break;
                case -1:
                    message = "سرویس geoLocation در مرورگر فعلی پشتیبانی نمی‌شود";
                    break;
            }
            console.warn("Location Error:", message);

            fallbackToIP((ipPos) => {
                const latLng = [ipPos.lat, ipPos.lon];

                // *****
                if (current_marker) map.removeLayer(current_marker)
                var current_icon=L.icon({
                    iconUrl: PATHFILE+"assets/images/maps/markers/blue-marker.png",
                    iconSize: [34, 50],
                })
                current_marker=new L.marker(latLng, { icon: current_icon }).addTo(map).bindTooltip("موقعیت مکانی من", {
                    direction: "top",
                    className: "search-leaflet-tooltip"
                }).openTooltip()
            });
        }
    }

    const getLocation = () =>
        new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject({ code: -1, message: "Geolocation not supported" });
            } else {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    timeout: 10000,
                    enableHighAccuracy: true,
                    maximumAge: 0
                });
            }
        });

    function fallbackToIP(callback) {
        fetch("https://ipwho.is/")
            .then(res => res.json())
            .then(data => {
                if (data.latitude && data.longitude) {
                    callback({ lat: data.latitude, lon: data.longitude });
                } else {
                    console.warn("IP API failed to return coordinates");
                }
            })
            .catch(err => console.error("IP API Error:", err));
    }


    // افزودن موقعیت مکانی من به عنوان مبدا یا مقصد
    $("[data-current-location]").on("click", function () {

        map.locate({ setView: true, maxZoom: 16 });
        map.on("locationfound", function (e) {
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
            goal_getAddress(route_goal.lat, route_goal.lng);
            if (coordsArray.length > 1) {
                $(".routing-button").attr("data-status", "origin");
                $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
            <div class="d-flex align-items-center">
                <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
            </div>
            <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                <div class="d-flex flex-column">
                    <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                </div>
            </div>
            <span class="circular-loading"></span>
        </div>`);
                $(".marker_center").hide();
                $(".routing-button").removeClass("active");
                $(".leaflet-control-container").show();
                $(".down-section").show();
            } else {
                $(".marker_center").show();
                $(".routing-button").text("انتخاب مبدا");
                $(".routing-button").attr("data-status", "origin");
                $(".routing-button").addClass("active");
            }
            map.off("locationfound")
        });
        map.on("locationerror", function (e) {
            snackbar("map_snackbar_18394829", "موقعیت مکانی شما یافت نشد.", "danger", {
                hasIcon: true,
            });
        });
    });
});

function showInSidebar() {
    if (!$("aside").hasClass("show")) toggleWithOverlay($("aside"), "show");
    $("#search-place").fadeIn().show().addClass("active").siblings().fadeOut().hide().removeClass("active");
}

$(".routing-box-item-button").click(function () {
    $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
            <div class="d-flex align-items-center">
                <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
            </div>
            <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                <div class="d-flex flex-column">
                    <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                </div>
            </div>
            <span class="circular-loading"></span>
        </div>`);
    $(".routing-box-item-button").removeClass("active");
    $(this).addClass("active");
    removeRoute();
    route(coordsArray);
});

function exportMapAsPng() {
    document.getElementById("print-loading").style.display = "block";
    printMap(map);
}

function showPlaceDetail() {
    $("#place-detail").addClass("active");
    $(this).addClass("active");
}

function routingToGoal(route, title) {
    $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
            <div class="d-flex align-items-center">
                <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
            </div>
            <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                <div class="d-flex flex-column">
                    <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                </div>
            </div>
            <span class="circular-loading"></span>
        </div>`);
    clearRoute();
    // var goal_icon = L.icon({
    //     iconUrl: PATHFILE + "assets/images/maps/markers/goal-marker.png",
    //     iconSize: [27, 41],
    // });
    // route_goal = route;
    // if (goal_marker) map.removeLayer(goal_marker);
    // goal_marker = L.marker([route.lat, route.lng], {
    //     icon: goal_icon,
    // }).addTo(map);
    // if (title.length) goal_marker.bindTooltip(title, { direction: "top", className: "search-leaflet-tooltip" }).openTooltip();
    
    var goal_latlng = { lat: route.lat, lng: route.lng };
    clickMapHandler(goal_latlng, true);
    goal_getAddress(route.lat, route.lng);
    map.setView([route.lat, route.lng], 17);
    $(".marker_center").show();
    $("#routing-page").fadeIn().show().addClass("active").siblings().fadeOut().hide().removeClass("active");
    $(".routing-button").addClass("active");
    $(".routing-button").text("انتخاب مبدا ");
    $(".routing-button").attr("data-status", "onlyOrigin");
    $(".mouse-move-box").addClass("hide");
    $(".leaflet-control-container").hide();
    $(".down-section").hide();
}

function routingToSelectedPointA(pointA) {
    //   var array = [
    //     { lat: 33.911285280583876, lng: 50.45594573020936 },
    //     {
    //       lat: 33.916431571844356,
    //       lng: 50.45017361640931,
    //     },
    //   ];
    pointB = {
        lat: 33.916431571844356,
        lng: 50.45017361640931,
    };

    //   route_goal = map.getCenter();

    var goal_icon = L.icon({
        iconUrl: PATHFILE + "assets/images/maps/markers/goal-marker.png",
        iconSize: [27, 41],
    });

    if (goal_marker) map.removeLayer(goal_marker);
    goal_marker = L.marker([pointB.lat, pointB.lng], {
        icon: goal_icon,
    }).addTo(map);
    var goal_latlng = { lat: pointB.lat, lng: pointB.lng };
    clickMapHandler(goal_latlng);
    goal_getAddress(pointB.lat, pointB.lng);
    $(".routing-button").attr("data-status", "origin");
    $(".route-page-places-items").html(`
                <div class="route-page-places-item cursor-pointer p-2 py-3 rounded d-flex align-items-center bg-white text-darkest" onclick="currentLocationRouting(this)">
            <div class="d-flex align-items-center">
                <i class="fa-regular fa-location-dot fs-13 text-light-dark"></i>
            </div>
            <div class="d-flex align-items-center  justify-content-between ms-4 w-100">
                <div class="d-flex flex-column">
                    <span class="fs-13 fw-500 text-darkest">موقعیت مکانی خودم</span>
                </div>
            </div>
            <span class="circular-loading"></span>
        </div>`);
    $(".marker_center").hide();
    $(".routing-button").removeClass("active");
    $(".leaflet-control-container").show();
    $(".down-section").show();
    console.log(map.getCenter(), pointB);

    // goal_getAddress(pointB.lat, pointB.lng);
    // route(array);
}

function routingFromSelectedPoint() { }
function routingToSelectedPoint() { }

function setPersonalLocation() {
    var place = $(".select-location").attr("place");

    switch (place) {
        case "home":
            homePoint = map.getCenter();
            var point_icon = L.icon({
                iconUrl: PATHFILE + "assets/images/maps/home.png",
                iconSize: [46, 46],
                className: "user-home-location",
            });
            pointMarker = L.marker([homePoint.lat, homePoint.lng], {
                icon: point_icon,
            }).addTo(map);

            // console.log(homePoint);
            // return homePoint;
            homeLocation = homePoint;
            $(".select-location").removeClass("active");
            $(".mouse-move-box").removeClass("hide");
            break;
        case "work":
            workPoint = map.getCenter();
            var point_icon = L.icon({
                iconUrl: PATHFILE + "assets/images/maps/work.png",
                iconSize: [46, 46],
                className: "user-work-location",
            });
            pointMarker = L.marker([workPoint.lat, workPoint.lng], {
                icon: point_icon,
            }).addTo(map);

            // console.log(homePoint);
            // return homePoint;
            workLocation = workPoint;
            $(".select-location").removeClass("active");
            $(".mouse-move-box").removeClass("hide");
            break;

        default:
            break;
    }
}

function showPersonalLocation(place) {
    var markers = $(".leaflet-marker-pane").children("img");
    // console.log(markers);

    if (markers.length > 0) {
        switch (place) {
            case "home":
                if ($(".user-home-location")[0]) {
                    $(".user-home-location").show();
                } else {
                    alert("لطفا ابتدا یک مکان را به عنوان خانه به نقشه اضافه کنید");
                }

                break;
            case "work":
                if ($(".user-work-location")[0]) {
                    $(".user-work-location").show();
                } else {
                    alert("لطفا ابتدا یک مکان را به عنوان محل کار به نقشه اضافه کنید");
                }
                break;

            default:
                break;
        }
    } else {
        alert("لطفا ابتدا یک مکان را به عنوان خانه به نقشه اضافه کنید");
    }
}

function closeOtherTooltips(excludeTooltip) {
    map.eachLayer(function (layer) {
        if (layer instanceof L.Marker && layer !== excludeTooltip) layer.closeTooltip();
    });
}

function panToAvgPositions(...positions) {
    var center = positions.reduce(
        function (acc, latLng) {
            return [acc[0] + latLng.lat, acc[1] + latLng.lng];
        },
        [0, 0],
    );
    center = [center[0] / positions.length, center[1] / positions.length];

    map.panTo(center);
}

function setViewToAvgPositions(zoom, ...positions) {
    var center = positions.reduce(
        function (acc, latLng) {
            return [acc[0] + latLng.lat, acc[1] + latLng.lng];
        },
        [0, 0],
    );
    center = [center[0] / positions.length, center[1] / positions.length];

    map.setView(center, zoom);
}

/* Time format helper start */
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

/* Time format helper end */
/* Date format helper start */
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
/* Date format helper end */
/* Transforms Start */
function nosaziToLocation(nosaziCode) {
    return new Promise(async (resolve, reject) => {
        var response = {lat: null, lng: null}
        if (!validateNosaziCode(nosaziCode)) {
            snackbar("map_snackbar_18394829", "کد نوسازی وارد شده نامعتبر میباشد.", "danger");
        } else {
            // @TODO
            if (app_config["_map_layers"]["nosazi_layer"]?.["scripts"]) {
                await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["nosazi_layer"]?.["scripts"]);
            }
            (app_config["_map_layers"]["nosazi_layer"]?.["var_name"] ?? []).forEach((var_name,index) => {
                var apartmentRenCodes = [];
                if (window[app_config["_map_layers"]["nosazi_layer"]["relate_var_name"][index]])
                    apartmentRenCodes = window[app_config["_map_layers"]["nosazi_layer"]["relate_var_name"][index]].filter(arse => (arse.RenCode + "-" + arse.Aparteman == nosaziCode) || (arse.RenCode == nosaziCode))
                if (apartmentRenCodes.length) 
                    L.geoJSON(window[var_name]).eachLayer(function (layer) {
                        if (layer.feature.properties.RenCode == apartmentRenCodes[0].RenCode) {
                            response = { 
                                lat: layer.feature.geometry.coordinates[0][0][0][1] != null ? (Array.isArray(layer.feature.geometry.coordinates[0][0][0][1]) ? layer.feature.geometry.coordinates[0][0][0][0][1] : layer.feature.geometry.coordinates[0][0][0][1]) : layer.feature.geometry.coordinates[0][0][1], 
                                lng: layer.feature.geometry.coordinates[0][0][0][0] != null ? (Array.isArray(layer.feature.geometry.coordinates[0][0][0][0]) ? layer.feature.geometry.coordinates[0][0][0][0][0] : layer.feature.geometry.coordinates[0][0][0][0]) : layer.feature.geometry.coordinates[0][0][0]
                            }
                        }
                    })
            })
        }
        setTimeout(() => {
            resolve(response)
        }, 100)
    })
}
function nosaziToLocation(nosaziCode) {
    return new Promise(async (resolve, reject) => {
        var response = {lat: null, lng: null}
        if (!validateNosaziCode(nosaziCode)) {
            snackbar("map_snackbar_18394829", "کد نوسازی وارد شده نامعتبر میباشد.", "danger");
        } else {
            if (app_config["_map_layers"]["nosazi_layer"]?.["scripts"]) {
                await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["nosazi_layer"]?.["scripts"]);
            }
            (app_config["_map_layers"]["nosazi_layer"]?.["var_name"] ?? []).forEach((var_name,index) => {
                var apartmentRenCodes = [];
                if (window[app_config["_map_layers"]["nosazi_layer"]["relate_var_name"][index]])
                    apartmentRenCodes = window[app_config["_map_layers"]["nosazi_layer"]["relate_var_name"][index]].filter(arse => (arse.RenCode + "-" + arse.Aparteman == nosaziCode) || (arse.RenCode == nosaziCode))
                if (apartmentRenCodes.length) 
                    L.geoJSON(window[var_name]).eachLayer(function (layer) {
                        if (layer.feature.properties.RenCode == apartmentRenCodes[0].RenCode) {
                            response = { 
                                lat: layer.feature.geometry.coordinates[0][0][0][1] != null ? (Array.isArray(layer.feature.geometry.coordinates[0][0][0][1]) ? layer.feature.geometry.coordinates[0][0][0][0][1] : layer.feature.geometry.coordinates[0][0][0][1]) : layer.feature.geometry.coordinates[0][0][1], 
                                lng: layer.feature.geometry.coordinates[0][0][0][0] != null ? (Array.isArray(layer.feature.geometry.coordinates[0][0][0][0]) ? layer.feature.geometry.coordinates[0][0][0][0][0] : layer.feature.geometry.coordinates[0][0][0][0]) : layer.feature.geometry.coordinates[0][0][0]
                            }
                        }
                    })
            })
        }
        setTimeout(() => {
            resolve(response)
        }, 100)
    })
}
function nosaziToLocationWs(nosaziCode) {
    return new Promise(async (resolve, reject) => {
        var response = {lat: null, lng: null}
        if (!nosaziCode?.length) {
            resolve(response)
            return;
        }
        if (!validateNosaziCode(nosaziCode)) {
            snackbar("map_snackbar_18394829", "کد نوسازی وارد شده نامعتبر میباشد.", "danger");
        } else {
            var nosaziCodeArray = nosaziCode.split("-")
            var aparteman = ""
            if (nosaziCodeArray.length > 4) {
                aparteman = nosaziCodeArray[4].toString()
                nosaziCodeArray.pop()
                nosaziCode = nosaziCodeArray.join("-")
            }
            if (app_config["_map_layers"]["nosazi_layer"]?.["scripts"]) {
                await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["nosazi_layer"]?.["scripts"]);
            }
            (app_config["_map_layers"]["nosazi_layer"]?.["var_name"] ?? []).forEach((var_name,index) => {
                if (nosaziCode.length) 
                    L.geoJSON(window[var_name]).eachLayer(function (layer) {
                        if (layer.feature.properties.RenCode == nosaziCode) {
                            response = { 
                                lat: layer.feature.geometry.coordinates[0][0][0][1] != null ? (Array.isArray(layer.feature.geometry.coordinates[0][0][0][1]) ? layer.feature.geometry.coordinates[0][0][0][0][1] : layer.feature.geometry.coordinates[0][0][0][1]) : layer.feature.geometry.coordinates[0][0][1], 
                                lng: layer.feature.geometry.coordinates[0][0][0][0] != null ? (Array.isArray(layer.feature.geometry.coordinates[0][0][0][0]) ? layer.feature.geometry.coordinates[0][0][0][0][0] : layer.feature.geometry.coordinates[0][0][0][0]) : layer.feature.geometry.coordinates[0][0][0]
                            }
                        }
                    })
            })
        }
        setTimeout(() => {
            resolve(response)
        }, 100)
    })
}
async function locationToNosazi(lat, lng, showSnackbar = true) {
    return new Promise(async (resolve, reject) => {
        var response = null
        var wait = false
        if (!lat) {
            snackbar("map_snackbar_18394829", "عرض جغرافیایی وارد نشده است.", "danger");
        } else if (!lng) {
            snackbar("map_snackbar_18394829", "طول جغرافیایی وارد نشده است.", "danger");
        } else {
            if (app_config["_map_layers"]["nosazi_layer"]?.["scripts"]) {
                await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["nosazi_layer"]?.["scripts"]);
            }
            (app_config["_map_layers"]["nosazi_layer"]?.["var_name"] ?? []).forEach((var_name,index) => {
                L.geoJSON(window[var_name]).eachLayer(async function (layer) {                    
                    // Define a sample polygon coordinates in lat lng format
                    const polygon = extractLatLngs(layer.feature.geometry.coordinates)
                    
                    // Define a sample point in lat lng format
                    const point = [parseFloat(lat), parseFloat(lng)];
                    
                    // Check if the point is inside the polygon
                    const result = pointInPolygon(point, polygon);
                    
                    if (result) {
                        wait = true
                        try {
                            $.ajax({type:"Post",url:PATHFILE+"execute/maps/conversions",data:"token="+TOKEN+"&value="+layer.feature.properties.RenCode+"&aparteman=&data_input=rencode&data_output=aparteman&cas_id="+getCookie("CAS_ID"),cache:"false",success:function(data){
                                data = JSON.parse(data)
                                if (data.status != "8") return;
                                if (data.result.length > 1) {
                                    $("#nosaziLayerModalLabel").text("کد های نوسازی آپارتمان")
                                    if (document.documentElement.clientWidth < 768 && $("aside").hasClass("show")) toggleWithOverlay($("aside"), "show")
                                    $("#nosaziLayerModal").modal("show")
                                    var apartmentHTML = [];
                                    data.result.forEach((aparteman) => {
                                        var itemNosazi = layer.feature.properties.RenCode + "-" + aparteman
                                        apartmentHTML.push(`
                                        <div class="grid-layer-item flex-wrap" data-value="${itemNosazi}" data-bs-dismiss="modal">
                                            <span class="fw-500 text-darker">کد نوسازی :</span>
                                            <span>${itemNosazi}</span>
                                        </div>`)
                                    })
                                    $("#apartmentNosaziSet").html(apartmentHTML)
                                    document.querySelectorAll("#nosaziLayerModal .grid-layer-item").forEach(item=> {
                                        item.onclick = () => {
                                            response = $(item).data("value").toString()
                                            setTimeout(() => {
                                                $(".map-loader").removeClass("active")
                                            },200)
                                            resolve(response)
                                        }
                                    })
                                    $("#nosaziLayerModal").on("hide.bs.modal", () => {
                                        setTimeout(() => {
                                            $(".map-loader").removeClass("active")
                                        },200)
                                        setTimeout(() => {
                                            resolve(null)
                                        }, 100)
                                    })
                                } else if (data.result.length == 1) {
                                    response = layer.feature.properties.RenCode + "-" + data.result[0]
                                    setTimeout(() => {
                                        $(".map-loader").removeClass("active")
                                    },200)
                                    resolve(response)
                                } else {
                                    $("#apartmentNosaziSet").html("")
                                    setTimeout(() => {
                                        $(".map-loader").removeClass("active")
                                    },200)
                                    if (layer.feature.properties.RenCode)
                                        resolve(layer.feature.properties.RenCode + "-0")
                                    else 
                                        resolve(null)
                                }
                            }})
                        } catch(err) {
                            setTimeout(() => {
                                $(".map-loader").removeClass("active")
                            },200)
                            resolve(null)
                            return null
                        } finally {
                            setTimeout(() => {
                                $(".map-loader").removeClass("active")
                            },200)
                        }
                    }
                })
            })
        }
        setTimeout(() => {
            $(".map-loader").removeClass("active")
        },200)
        if (!response && !wait) {
            if (showSnackbar) snackbar("map_snackbar_18394829", "کد نوسازی برای این موقعیت یافت نشد.", "danger");
            resolve(null)
        }
        if (response)
            setTimeout(() => {
                resolve(response)
            }, 100)
    })
}
async function postalCodeToNosazi(postalCode) {
    return new Promise(async (resolve, reject) => {
        var response = ""
        if (!postalCode.length) {
            snackbar("map_snackbar_18394829", "کد پستی وارد شده نامعتبر میباشد.", "danger");
        } else {
            var filterItems = []
            if (app_config["_map_layers"]["nosazi_layer"]?.["scripts"]) {
                await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["nosazi_layer"]?.["scripts"]);
            }
            app_config["_map_layers"]["nosazi_layer"]["relate_var_name"].forEach((var_name,index) => {
                filterItems = [...filterItems, ...window[var_name].filter(item => item.PostalCode === postalCode)]
            })
            if (filterItems.length > 0) {
                response = filterItems[0].RenCode + "-" + filterItems[0].Aparteman
            }
        }
        if (response)
            setTimeout(() => {
                resolve(response)
            }, 100)
    })
}
async function nosaziToPostalCode(nosaziCode) {
    return new Promise(async (resolve, reject) => {
        var response = ""
        if (!validateNosaziCode(nosaziCode)) {
            snackbar("map_snackbar_18394829", "کد نوسازی وارد شده نامعتبر میباشد.", "danger");
        } else {
            var filterItems = []
            if (app_config["_map_layers"]["nosazi_layer"]?.["scripts"]) {
                await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["nosazi_layer"]?.["scripts"]);
            }
            app_config["_map_layers"]["nosazi_layer"]["relate_var_name"].forEach((var_name,index) => {
                filterItems = [...filterItems, ...window[var_name].filter(item => (item.RenCode == nosaziCode) || (item.RenCode + "-" + item.Aparteman == nosaziCode))]
            })
            if (filterItems.length > 0)
                response = filterItems[0].PostalCode
        }
        if (response)
            setTimeout(() => {
                resolve(response)
            }, 100)
        else resolve(null)
    })
}
async function locationToPostalCode(lat, lng, showSnackbar = true) {
    return new Promise(async (resolve, reject) => {
        var response = null
        var wait = false
        var renCode = "";
        if (!lat) {
            snackbar("map_snackbar_18394829", "عرض جغرافیایی وارد نشده است.", "danger");
        } else if (!lng) {
            snackbar("map_snackbar_18394829", "طول جغرافیایی وارد نشده است.", "danger");
        } else {
            if (app_config["_map_layers"]["nosazi_layer"]?.["scripts"]) {
                await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["nosazi_layer"]?.["scripts"]);
            }
            (app_config["_map_layers"]["nosazi_layer"]?.["var_name"] ?? []).forEach((var_name,index) => {
                L.geoJSON(window[var_name]).eachLayer(async function (layer) {
                    
                    // Define a sample polygon coordinates in lat lng format
                    const polygon = extractLatLngs(layer.feature.geometry.coordinates)
                    
                    // Define a sample point in lat lng format
                    const point = [parseFloat(lat), parseFloat(lng)];
                    
                    // Check if the point is inside the polygon
                    const result = pointInPolygon(point, polygon);
                    
                    
                    if (result) {
                        wait = true
                        try {
                            $.ajax({type:"Post",url:PATHFILE+"execute/maps/conversions",data:"token="+TOKEN+"&value="+layer.feature.properties.RenCode+"&aparteman=&data_input=rencode&data_output=zipcode&cas_id="+getCookie("CAS_ID"),cache:"false",success:function(data){
                                data = JSON.parse(data)
                                if (data.status != "8") return;
                                if (!data.result.filter(r => r?.length).length) {
                                    if(showSnackbar) snackbar("map_snackbar_18394829", "کد پستی برای این موقعیت یافت نشد.", "danger");
                                    resolve(null)
                                }
                                if (data.result.length > 1) {
                                    $("#nosaziLayerModalLabel").text("کد های پستی آپارتمان")
                                    if (document.documentElement.clientWidth < 768 && $("aside").hasClass("show")) toggleWithOverlay($("aside"), "show")
                                    $("#nosaziLayerModal").modal("show")
                                    var apartmentHTML = [];
                                    data.result.forEach((postalcode) => {
                                        apartmentHTML.push(`
                                        <div class="grid-layer-item flex-wrap" data-value="${postalcode}" data-bs-dismiss="modal">
                                            <span class="fw-500 text-darker">کد پستی :</span>
                                            <span>${postalcode}</span>
                                        </div>`)
                                    })
                                    $("#apartmentNosaziSet").html(apartmentHTML)
                                    document.querySelectorAll("#nosaziLayerModal .grid-layer-item").forEach(item=> {
                                        item.onclick = () => {
                                            response = $(item).data("value").toString()
                                            setTimeout(() => {
                                                $(".map-loader").removeClass("active")
                                            },200)
                                            resolve(response)
                                        }
                                    })
                                    $("#nosaziLayerModal").on("hide.bs.modal", () => {
                                        setTimeout(() => {
                                            $(".map-loader").removeClass("active")
                                        },200)
                                        setTimeout(() => {
                                            resolve(null)
                                        }, 100)
                                    })
                                } else if (data.result.length == 1) {
                                    response = data.result[0]
                                    setTimeout(() => {
                                        $(".map-loader").removeClass("active")
                                    },200)
                                    resolve(response)
                                } else {
                                    $("#apartmentNosaziSet").html("")
                                    setTimeout(() => {
                                        $(".map-loader").removeClass("active")
                                    },200)
                                    resolve(null)
                                }
                        }})
                        } catch(err) {
                            setTimeout(() => {
                                $(".map-loader").removeClass("active")
                            },200)
                            resolve(null)
                            return null
                        } finally {
                            setTimeout(() => {
                                $(".map-loader").removeClass("active")
                            },200)
                        }
                    }
                })
            })
        }
        if (!response && !wait) {
            if(showSnackbar) snackbar("map_snackbar_18394829", "کد پستی برای این موقعیت یافت نشد.", "danger");
            resolve(null)
        }
        if (response) {
            setTimeout(() => {
                resolve(response)
            }, 100)
        }
    })
}

async function locationToAddress(lat, lng) {
    if (!lat) {
        snackbar("map_snackbar_18394829", "عرض جغرافیایی وارد نشده است.", "danger");
        return null;
    } else if (!lng) {
        snackbar("map_snackbar_18394829", "طول جغرافیایی وارد نشده است.", "danger");
        return null;
    } else {
        var data = await fetch("https://map.ir/reverse/fast-reverse?lat=" + lat + "&lon=" + lng, {
            method: "GET",
            headers: { "x-api-key": API_TOKEN },
        })
            .then((res) => {
                if (res.status == 200) {
                    return res.json();
                }
                return new Error("Error :/");
            })
        return data.postal_address
    }
}

function postalCodeToLocation(postalCode, showSnackbar = false) {
    return new Promise((resolve, reject) => {
        var response = {lat: null, lng: null}
        var wait = false
        if (!postalCode.length) {
            resolve(response);
            return;
        } else {
            wait = true
            try {
                $.ajax({type:"Post",url:PATHFILE+"execute/maps/conversions",data:"token="+TOKEN+"&value="+postalCode+"&aparteman=&data_input=zipcode&data_output=rencode&cas_id="+getCookie("CAS_ID"),cache:"false",success:async function(data){
                    data = JSON.parse(data)
                    if (data.result.length) {
                        var nosaziCode = data.result
                        var nosaziCodeArray = nosaziCode.split("-")
                        var aparteman = ""
                        if (nosaziCodeArray.length > 4) {
                            aparteman = nosaziCodeArray[4].toString()
                            nosaziCodeArray.pop()
                            nosaziCode = nosaziCodeArray.join("-")
                        }
                        if (app_config["_map_layers"]["nosazi_layer"]?.["scripts"]) {
                            await scriptLoader.loadScriptsSequentially(app_config["_map_layers"]["nosazi_layer"]?.["scripts"]);
                        }
                        (app_config["_map_layers"]["nosazi_layer"]?.["var_name"] ?? []).forEach((var_name,index) => {
                            L.geoJSON(window[var_name]).eachLayer(function (layer) {
                                if (layer.feature.properties.RenCode == nosaziCode) {
                                    response = { 
                                        lat: layer.feature.geometry.coordinates[0][0][0][1] != null ? (Array.isArray(layer.feature.geometry.coordinates[0][0][0][1]) ? layer.feature.geometry.coordinates[0][0][0][0][1] : layer.feature.geometry.coordinates[0][0][0][1]) : layer.feature.geometry.coordinates[0][0][1], 
                                        lng: layer.feature.geometry.coordinates[0][0][0][0] != null ? (Array.isArray(layer.feature.geometry.coordinates[0][0][0][0]) ? layer.feature.geometry.coordinates[0][0][0][0][0] : layer.feature.geometry.coordinates[0][0][0][0]) : layer.feature.geometry.coordinates[0][0][0]
                                    }
                                    resolve(response)
                                    return;
                                }
                            })
                        })
                        if (!response.lat || !response.lng) {
                            snackbar("map_snackbar_18394829", "موقعیتی برای این کد پستی یافت نشد.", "danger");
                            resolve(response)
                        }
                    }
                }})
            } catch(err) {

            }
        }
        if ((!response.lat || !response.lng) && !wait ) {
            if (showSnackbar) snackbar("map_snackbar_18394829", "موقعیتی برای این کد پستی یافت نشد.", "danger");
            setTimeout(() => {
                resolve(response)
            }, 100)
        }
    })
}
async function searchLocationRequest(body) {
    var requestOptions = {
        method: "POST",
        headers: {
            "x-api-key": API_TOKEN,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        redirect: "follow",
    };
    try {
        return await fetch("https://map.ir/search/v2/autocomplete", requestOptions)
            .then((res) => {
                if (res.status == 200) {
                    return res.json();
                }
                return new Error("Error :/");
            })
    } catch(err) {
        return null
    }
}
async function addressToLocation(address) {
    if (!address) {
        snackbar("map_snackbar_18394829", "آدرسی وارد نشده است!", "danger");
        return {lat:null,lng:null,address: null};
    } else {
        var data = await searchLocationRequest({
            text: address,
            $filter: DEFAULTSRCH,
        })
        if (data.value) {
            return {
                lat: data.value[0].geom.coordinates[1],
                lng: data.value[0].geom.coordinates[0],
                address: data.value[0].title
            }
        }
    }
    snackbar("map_snackbar_18394829", "موقعیتی برای این آدرس یافت نشد.", "danger");
    return {lat:null,lng:null,address: null};
}

/** @TODO */
async function postalCodeToLocationWs(postalCode) {
    var response = {lat: null, lng: null}
    try {
        $.ajax({type:"Post",url:PATHFILE+"execute/maps/conversions",data:"token="+TOKEN+"&value="+postalCode+"&aparteman=&data_input=zipcode&data_output=rencode&cas_id="+getCookie("CAS_ID"),cache:"false",success:function(data){
            data = JSON.parse(data)
            if (data.status != "8") return;
            if (data.result.length > 1) {
                //. . .
            } else {
                return data.result[0]
            }
        }})
    } catch(err) {
        return null
    }
}

async function postalCodeToNosaziWs(postalCode) {
    if (!postalCode.length) {
        return null
    } else {
        try {
            return new Promise((resolve, reject) => {
                $.ajax({type:"Post",url:PATHFILE+"execute/maps/conversions",data:"token="+TOKEN+"&value="+postalCode+"&aparteman=&data_input=zipcode&data_output=rencode&cas_id="+getCookie("CAS_ID"),cache:"false",success:function(data){
                    data = JSON.parse(data)
                    if (data.status != "8") resolve(null);
                    if (data.result.length) {
                        resolve(data.result)
                    } else {
                        snackbar("map_snackbar_18394829", "هیچ کد نوسازی برای این کد پستی یافت نشد.", "danger");
                        resolve(null)
                    }
                }})
            })
        } catch(err) {
            return null
        }
    }
}

async function postalCodeToAddressWs(postalCode) {
    if (!postalCode.length) {
        snackbar("map_snackbar_18394829", "کد پستی وارد شده نامعتبر میباشد.", "danger");
        return null
    } else {
        try {
            return new Promise((resolve, reject) => {
                $.ajax({type:"Post",url:PATHFILE+"execute/maps/conversions",data:"token="+TOKEN+"&value="+postalCode+"&aparteman=&data_input=zipcode&data_output=address&cas_id="+getCookie("CAS_ID"),cache:"false",success:function(data){
                    data = JSON.parse(data)
                    if (data.status != "8") resolve(null);
                    if (data.result.length) {
                        resolve(data.result)
                    } else {
                        snackbar("map_snackbar_18394829", "هیچ آدرسی برای این کد پستی یافت نشد.", "danger");
                        resolve(null);
                    }
                }})
            })
        } catch(err) {
            return null
        }
    }
}

async function nosaziToPostalCodeWs(nosaziCode, showSnackbar = true) {
    var nosaziCodeArray = nosaziCode.split("-")
    var aparteman = ""
    if (nosaziCodeArray.length > 4) {
        aparteman = nosaziCodeArray[4].toString()
        nosaziCodeArray.pop()
        nosaziCode = nosaziCodeArray.join("-")
    }
    try {
        return await new Promise((resolve, reject) => {
            $.ajax({type:"Post",url:PATHFILE+"execute/maps/conversions",data:"token="+TOKEN+"&value="+nosaziCode+"&aparteman="+aparteman+"&data_input=rencode&data_output=zipcode&cas_id="+getCookie("CAS_ID"),cache:"false",success:function(data){
                data = JSON.parse(data)
                if (data.status != "8") resolve(null);
                if (!data.result.filter(r => r?.length).length) {
                    if(showSnackbar) snackbar("map_snackbar_18394829", "کد پستی برای این کد نوسازی یافت نشد.", "danger");
                    resolve(null)
                }
                if (data.result.length > 1) {
                    $("#nosaziLayerModalLabel").text("کد های پستی آپارتمان")
                    if (document.documentElement.clientWidth < 768 && $("aside").hasClass("show")) toggleWithOverlay($("aside"), "show")
                    $("#nosaziLayerModal").modal("show")
                    var apartmentHTML = [];
                    data.result.forEach((item) => {
                        apartmentHTML.push(`
                        <div class="grid-layer-item flex-wrap" data-value="${item}" data-bs-dismiss="modal">
                            <span class="fw-500 text-darker">کد پستی :</span>
                            <span>${item}</span>
                        </div>`)
                    })
                    $("#apartmentNosaziSet").html(apartmentHTML)
                    document.querySelectorAll("#nosaziLayerModal .grid-layer-item").forEach(item=> {
                        item.onclick = () => {
                            response = $(item).data("value").toString()
                            setTimeout(() => {
                                $(".map-loader").removeClass("active")
                            },200)
                            resolve(response)
                        }
                    })
                    $("#nosaziLayerModal").on("hide.bs.modal", () => {
                        setTimeout(() => {
                            $(".map-loader").removeClass("active")
                        },200)
                        setTimeout(() => {
                            resolve(null)
                        }, 100)
                    })
                } else if (data.result.length) {
                    setTimeout(() => {
                        $(".map-loader").removeClass("active")
                    },200)
                    resolve(data.result[0])
                } else {
                    setTimeout(() => {
                        $(".map-loader").removeClass("active")
                    },200)
                    snackbar("map_snackbar_18394829", "هیچ کد پستی برای این کد نوسازی یافت نشد.", "danger");
                    resolve(null)
                }
            }})
        })
    } catch(err) {
        return null
    } finally {
        setTimeout(() => {
            $(".map-loader").removeClass("active")
        },200)
    }
}
/* Transforms end */

$(document).ready(function() {
    $("form").on("submit", (event) => {
        event.preventDefault()
    })
})

async function show_unified_parser(e, layerId) {
    if (!allowedLayers.includes(layerId)) return;
    
    const layerConfig = app_config._map_layers[layerId] ?? app_config._map_form_layers[layerId];
    const layerName = layerConfig.id;
    const isActive = $(e.target).hasClass("switch_layer") && $(e.target).hasClass("active") || $(e.target).parents(".switch_layer").hasClass("active");
    if (!isActive) {
        $(`.${layerName}`).addClass("is-loading pointer-events-none");
        await scriptLoader.loadScriptsSequentially(layerConfig.scripts);
        layerConfig.var_name.forEach((var_name, index) => createLayer(layerId, var_name, index));
    } else {
        layerManager.removeParserLayers(layerId);
        if (layerPopups[layerId]) {
            layerPopups[layerId].remove();
            layerPopups[layerId] = null;
        }
        if (lastClickedFeatures[layerId]) {
            delete lastClickedFeatures[layerId];
        }
    }
}

function createLayer(layerId, var_name, index) {
    const layerConfig = app_config._map_layers[layerId] ?? app_config._map_form_layers[layerId];
    const layerKey = layerConfig.id + "_" + index;
    
    window[layerKey + "_overlay"] = map.createPane(layerKey + "_overlay");
    
    let vectorLayer = L.vectorGrid.slicer(window[var_name], {
        maxZoom: 22,
        minNativeZoom: 0,
        rendererFactory: L.canvas.tile,
        pane: layerKey + "_overlay",
        vectorTileLayerStyles: {
            sliced: function(properties, zoom) {
                const uniqueField = layerConfig.unique_field;
                if (uniqueField && properties[uniqueField] != null || !uniqueField) {
                    return getParserStyles(layerConfig.parser_type, layerConfig.color, properties, zoom).default;
                }
                return {color:false,fillColor:false,opacity:0,fillOpacity:0,weight:0,stroke:false,fill:false,interactive:false};
            }
        },
        interactive: layerConfig.interactive !== false,
        preferCanvas: false,
        getFeatureId: function(feature) {
            const uniqueField = layerConfig.unique_field;
            if (uniqueField && feature.properties[uniqueField] != undefined) {
                return feature.properties[uniqueField].toString() + index.toString();
            }
            return Math.random().toString(36).substr(2, 9);
        }
    })
    .on("click", async function(e) { await handleLayerClick(e, layerId, index); })
    .on("loading", function() { $(`.${layerConfig.id}`).addClass("is-loading pointer-events-none"); })
    .on("load", function() { $(`.${layerConfig.id}`).removeClass("is-loading pointer-events-none"); })
    .addTo(map).bringToFront();
    handlePaneClick(window[layerKey + "_overlay"]);
    layerManager.addLayer(layerId, index, vectorLayer, {createdAt: Date.now(),varName: var_name});
}

async function handleLayerClick(e, layerId, index, link = '', mapLayer = '', mapField = '') {
    const layerConfig = app_config._map_layers[layerId] ?? app_config._map_form_layers[layerId];
    if (!layerConfig) return;
    const uniqueField = layerConfig.unique_field;
    const latLng = e.latlng;
    const layer = e.layer;
    const properties = layer.properties;
    const featureId = properties[uniqueField] ? properties[uniqueField].toString() + index.toString() : null;
    const featureKey = properties[mapField]?.toString();
    parserClicked = true;

    if (lastClickedFeatures[layerId]) {
        const prevFeatureId = lastClickedFeatures[layerId];
        const layerKeys = layerManager.getParserLayers(layerId);
        
        layerKeys.forEach(layerKey => {
            const layerData = layerManager.getLayer(layerKey);
            if (layerData && layerData.layer) {
                layerData.layer.setFeatureStyle(
                    prevFeatureId,
                    getParserStyles(
                        layerConfig.parser_type,
                        layerConfig.color,
                        properties,
                        map.getZoom()
                    ).default
                );
            }
        });
    }
    
    if (featureId) {
        lastClickedFeatures[layerId] = featureId;
        const layerKeys = layerManager.getParserLayers(layerId);
        
        layerKeys.forEach(layerKey => {
            const layerData = layerManager.getLayer(layerKey);
            if (layerData && layerData.layer) {
                layerData.layer.setFeatureStyle(
                    featureId,
                    getParserStyles(
                        layerConfig.parser_type,
                        layerConfig.color,
                        properties,
                        map.getZoom()
                    ).hover
                );
            }
        });
    }
    
    if (layerPopups[layerId]) {
        layerPopups[layerId].remove();
        layerPopups[layerId] = null;
    }
    
    const actions = layerConfig.actions ? layerConfig.actions.split(",") : [];
    if ((actions.includes("nosazi_widget") || actions.includes("kasb_widget")) && properties.RenCode) {
        await handleRenCodeAction(e, layerId, properties);
    }
    if (actions.includes("my_amlak_widget")) {
        await handleMyAmlakWidget(e, layerId, properties, featureKey);
    }

    if (link.length) {
        if (featureKey?.length) {
            if (layerConfig.popup && properties[layerConfig.uniqueField]) showUnifiedPopup(layerConfig.id, properties, e.latlng);
            link_transfer(link);
            setTimeout(() => {
                $("#myModa_data").modal("hide");
                $("#myWidgets").modal("show");
            }, 100);
            return;
        }
    }
    
    if (layerConfig.popup && properties[uniqueField]) {
        showUnifiedPopup(layerId, properties, e.latlng);
    }
}

async function handleMyAmlakWidget(e, layerId, properties, featureKey) {
    const layerConfig = app_config._map_layers[layerId] ?? app_config._map_form_layers[layerId];
    try {
        $(".map-loader").addClass("active");
        $.ajax({
            type: "POST",
            url: "'._path_file.'execute/maps/conversions",
            data: `token=${WEB_TOKEN}&value=${featureKey}&aparteman=&data_input=rencode&data_output=aparteman&cas_id=${getCookie("CAS_ID")}`,
            cache: false,
            success: handleNosaziResponse,
            complete: () => setTimeout(() => $(".map-loader").removeClass("active"), 200)
        });
        
        function handleNosaziResponse(dataJson) {
            try {
                dataJson = JSON.parse(dataJson);
                if (dataJson.status !== "8") return;
                
                if (dataJson.result.length > 1) {
                    showMultipleApartments(dataJson.result, properties, featureKey);
                } else if (dataJson.result.length === 1) {
                    const fullKey = featureKey + "-" + dataJson.result[0];
                    showMyAmlak(fullKey, properties.fileNo, properties.owner, properties.address);
                    if (layerConfig.popup && properties[layerConfig.uniqueField]) showUnifiedPopup(layerConfig.id, properties, e.latlng);
                } else {
                    showMyAmlak(featureKey + "-0", properties.fileNo, properties.owner, properties.address);
                }
                $("#myModa_data").modal("hide");
                $("#myWidgets").modal("show");
            } catch (err) {
                console.error(err);
            }
        }                                                                     
    } catch (err) {
        console.error(err);
    } finally {
        setTimeout(() => $(".map-loader").removeClass("active"), 200);
    }

    // if (!properties.RenCode) return;
    // $(".map-loader").addClass("active");
    // try {
    //     const response = await $.ajax({
    //         type: "POST",
    //         url: PATHFILE+"execute/maps/conversions",
    //         data: "token="+WEB_TOKEN+"&value=" + properties.RenCode + "&aparteman=&data_input=rencode&data_output=aparteman&cas_id=" + getCookie("CAS_ID"),
    //         cache: false
    //     });
        
    //     const data = JSON.parse(response);
    //     if (data.status !== "8") return;
        
    //     if (data.result.length > 1) {
    //         $("#nosaziLayerModalLabel").text("کد های نوسازی آپارتمان");
    //         if ($("aside").hasClass("show")) toggleWithOverlay($("aside"), "show");
    //         $("#nosaziLayerModal").modal("show");
            
    //         const apartmentHTML = data.result.map(aparteman => {
    //             const itemNosazi = properties.RenCode + "-" + aparteman;
    //             return `<div class="grid-layer-item flex-wrap" data-value="${itemNosazi}" data-bs-dismiss="modal">
    //                 <span class="fw-500 text-darker">کد نوسازی :</span><span>${itemNosazi}</span></div>`;
    //         });
    //         $("#apartmentNosaziSet").html(apartmentHTML.join(""));
            
    //         $("#nosaziLayerModal .grid-layer-item").off("click").on("click", async function() {
    //             const nosaziCode = $(this).data("value").toString();
    //             const nosaziCodeArray = nosaziCode.split("-");
    //             let aparteman = "";
    //             if (nosaziCodeArray.length > 4) {
    //                 aparteman = nosaziCodeArray[4].toString();
    //                 nosaziCodeArray.pop();
    //             }
    //             $("#apartmentNosaziSet").html("");
    //             const address = await locationToAddress(e.latlng.lat, e.latlng.lng);
                
    //             if (layerConfig.actions.includes("nosazi_widget")) {
    //                 showNosaziWidget(nosaziCodeArray.join("-") + "-" + aparteman, properties.Par_Code, address);
    //             }
    //             if (layerConfig.actions.includes("kasb_widget")) {
    //                 showKasbOPisheWidget(nosaziCodeArray.join("-") + "-" + aparteman, properties.FileNO, address);
    //             }
    //         });
    //     } else if (data.result.length === 1) {
    //         $("#apartmentNosaziSet").html("");
    //         const address = await locationToAddress(e.latlng.lat, e.latlng.lng);
    //         if (layerConfig.actions.includes("nosazi_widget")) {
    //             showNosaziWidget(properties.RenCode + "-" + data.result[0], properties.Par_Code, address);
    //         }
    //         if (layerConfig.actions.includes("kasb_widget")) {
    //             showKasbOPisheWidget(properties.RenCode + "-" + data.result[0], properties.FileNO, address);
    //         }
    //     } else {
    //         $("#apartmentNosaziSet").html("");
    //         const address = await locationToAddress(e.latlng.lat, e.latlng.lng);
    //         if (layerConfig.actions.includes("nosazi_widget")) {
    //             showNosaziWidget(properties.RenCode + "-0", properties.Par_Code, address);
    //         }
    //         if (layerConfig.actions.includes("kasb_widget")) {
    //             showKasbOPisheWidget(properties.RenCode + "-0", properties.FileNO, address);
    //         }
    //     }
    // } catch (err) {
    //     console.error(err);
    // } finally {
    //     setTimeout(() => { $(".map-loader").removeClass("active"); }, 200);
    // }
}

async function handleRenCodeAction(e, layerId, properties) {
    if (!properties.RenCode) return;
    $(".map-loader").addClass("active");
    try {
        const response = await $.ajax({
            type: "POST",
            url: PATHFILE+"execute/maps/conversions",
            data: "token="+WEB_TOKEN+"&value=" + properties.RenCode + "&aparteman=&data_input=rencode&data_output=aparteman&cas_id=" + getCookie("CAS_ID"),
            cache: false
        });
        
        const data = JSON.parse(response);
        if (data.status !== "8") return;
        
        if (data.result.length > 1) {
            $("#nosaziLayerModalLabel").text("کد های نوسازی آپارتمان");
            if ($("aside").hasClass("show")) toggleWithOverlay($("aside"), "show");
            $("#nosaziLayerModal").modal("show");
            
            const apartmentHTML = data.result.map(aparteman => {
                const itemNosazi = properties.RenCode + "-" + aparteman;
                return `<div class="grid-layer-item flex-wrap" data-value="${itemNosazi}" data-bs-dismiss="modal">
                    <span class="fw-500 text-darker">کد نوسازی :</span><span>${itemNosazi}</span></div>`;
            });
            $("#apartmentNosaziSet").html(apartmentHTML.join(""));
            
            $("#nosaziLayerModal .grid-layer-item").off("click").on("click", async function() {
                const nosaziCode = $(this).data("value").toString();
                const nosaziCodeArray = nosaziCode.split("-");
                let aparteman = "";
                if (nosaziCodeArray.length > 4) {
                    aparteman = nosaziCodeArray[4].toString();
                    nosaziCodeArray.pop();
                }
                $("#apartmentNosaziSet").html("");
                const address = await locationToAddress(e.latlng.lat, e.latlng.lng);
                if (layerId === "nosazi_layer") {
                    showNosaziWidget(nosaziCodeArray.join("-") + "-" + aparteman, properties.Par_Code, address);
                } else if (layerId === "kasb_layer") {
                    showKasbOPisheWidget(nosaziCodeArray.join("-") + "-" + aparteman, properties.FileNO, address);
                }
            });
        } else if (data.result.length === 1) {
            $("#apartmentNosaziSet").html("");
            const address = await locationToAddress(e.latlng.lat, e.latlng.lng);
            if (layerId === "nosazi_layer") {
                showNosaziWidget(properties.RenCode + "-" + data.result[0], properties.Par_Code, address);
            } else if (layerId === "kasb_layer") {
                showKasbOPisheWidget(properties.RenCode + "-" + data.result[0], properties.FileNO, address);
            }
        } else {
            $("#apartmentNosaziSet").html("");
            const address = await locationToAddress(e.latlng.lat, e.latlng.lng);
            if (layerId === "nosazi_layer") {
                showNosaziWidget(properties.RenCode + "-0", properties.Par_Code, address);
            } else if (layerId === "kasb_layer") {
                showKasbOPisheWidget(properties.RenCode + "-0", properties.FileNO, address);
            }
        }
    } catch (err) {
        console.error(err);
    } finally {
        setTimeout(() => { $(".map-loader").removeClass("active"); }, 200);
    }
}

function showUnifiedPopup(layerId, properties, latlng) {
    const layerConfig = app_config._map_layers[layerId] ?? app_config._map_form_layers[layerId];
    if (!properties || Object.keys(properties).length === 0) return;
    
    const create_div = document.createElement("div");
    create_div.className = "d-flex flex-column";
    const create_div_info = document.createElement("div");
    create_div_info.className = "d-flex flex-column mt-2 mb-2";
    
    let hasFields = false;
    for (const key in layerConfig.fields) {
        if (!properties[key]?.toString()?.length) continue;
        const fieldDiv = document.createElement("div");
        fieldDiv.className = "d-flex flex-row justify-content-between align-items-center my-1 gap-2";
        const fieldHead = document.createElement("span");
        fieldHead.className = "fs-14 fw-500";
        fieldHead.textContent = layerConfig.fields[key];
        const fieldBody = document.createElement("span");
        fieldBody.className = "fs-13 text-darkest fw-400";
        fieldBody.textContent = properties[key]?.toString()?.length ? properties[key] : "<خالی>";
        fieldDiv.appendChild(fieldHead);
        fieldDiv.appendChild(fieldBody);
        create_div_info.appendChild(fieldDiv);
        hasFields = true;
    }
    
    if (hasFields) {
        create_div.appendChild(create_div_info);
        layerPopups[layerId] = L.popup()
            .setContent(create_div)
            .setLatLng(latlng)
            .openOn(map)
            .on("remove", function() { layerPopups[layerId] = null; });
    }
}

$(document).on("themeChanged", function(e) {
    layerManager.clearAll();
    for (const layerId in app_config._map_layers) {
        const layerConfig = app_config._map_layers[layerId] ?? app_config._map_form_layers[layerId];
        if (layerConfig.status) {
            const switchElement = document.querySelector(`.switch_layer.${CSS.escape(layerId)}`);
            const isActive = switchElement && switchElement.classList.contains("active");
            if (isActive) {
                layerConfig.var_name.forEach((var_name, index) => {
                    if (window[var_name]) {
                        createLayer(layerId, var_name, index);
                    }
                });
            }
        }
    }
    for (let popupLayerId in layerPopups) {
        if (layerPopups[popupLayerId]) {
            layerPopups[popupLayerId].remove();
        }
    }
    layerPopups = {};
    lastClickedFeatures = {};
});