(function ($) {
    $.fn.timelinePlayer = function (options) {
        const defaults = {
            startTime: "00:00:00",
            endTime: "00:05:00",
            speedOptions: [0.5, 1, 1.5, 2],
            defaultSpeed: 1,
            isRTL: false,
            onTimeUpdate: null,
        };

        const settings = $.extend({}, defaults, options);

    
        function calculateTotalDuration(startTime, endTime) {
            const start = new Date(`1970-01-01T${startTime}Z`);
            const end = new Date(`1970-01-01T${endTime}Z`);
            return (end - start) / 1000;
        }

        const totalDuration = calculateTotalDuration(settings.startTime, settings.endTime);

        return this.each(function () {
            let currentTime = 0;
            let playbackSpeed = settings.defaultSpeed;
            let isPlaying = false;
            let interval;
            let isDragging = false;

            function formatTime(seconds) {
                const hrs = Math.floor(seconds / 3600);
                const mins = Math.floor((seconds % 3600) / 60);
                const secs = Math.floor(seconds % 60);
                if (hrs > 0) {
                    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
                } else {
                    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
                }
            }            

            function updateTime(newTime) {
                currentTime = Math.min(Math.max(newTime, 0), totalDuration);
                const absoluteTime = currentTime + calculateTotalDuration("00:00:00", settings.startTime);
                const displayTime = formatTime(absoluteTime);
                $currentTimeDisplay.text(displayTime);
                $totalTimeDisplay.text(formatTime(absoluteTime + totalDuration - currentTime));
                const progressPercent = (currentTime / totalDuration) * 100;
                $progressFill.css(settings.isRTL ? "right" : "left", "0");
                $progressFill.css("width", progressPercent + "%");
                if (typeof settings.onTimeUpdate === "function") settings.onTimeUpdate(currentTime);
            }

            function startPlayback() {
                interval = setInterval(() => {
                    if (currentTime >= totalDuration) {
                        stopPlayback();
                        togglePlayPause(false);
                        updateTime(0);
                        return;
                    }
                    updateTime(currentTime + playbackSpeed);
                }, 1000 / playbackSpeed);
            }

            function stopPlayback() {
                clearInterval(interval);
            }

            function togglePlayPause(play) {
                isPlaying = play;
                if (isPlaying) {
                    startPlayback();
                    $playPauseBtn.html('<i class="fas fa-pause"></i>');
                } else {
                    stopPlayback();
                    $playPauseBtn.html('<i class="fas fa-play"></i>');
                }
            }

            const $timeline = $(this).addClass("brztl-timeline-container" + (settings.isRTL ? " rtl" : ""));
            const $progressContainer = $("<div>").addClass("brztl-progress-container").appendTo($timeline);
            const $progressBar = $("<div>").addClass("brztl-progress-bar").appendTo($progressContainer);
            const $progressFill = $("<div>").addClass("brztl-progress-fill").appendTo($progressBar);

            const $controlsContainer = $("<div>").addClass("brztl-controls-container").appendTo($timeline);
            const $currentTimeDisplay = $("<span>").addClass("brztl-current-time").text(formatTime(0)).appendTo($controlsContainer);
            const $totalTimeDisplay = $("<span>").addClass("brztl-total-time").text(formatTime(totalDuration)).appendTo($controlsContainer);

            const $controlButtons = $("<div>").addClass("brztl-control-buttons").appendTo($controlsContainer);

            const $rewindBtn = $("<button>").addClass("brztl-rewindBtn").html('<i class="fas fa-backward"></i>').appendTo($controlButtons).on("click", function () {
                updateTime(currentTime - 5);
            });

            const $playPauseBtn = $("<button>").addClass("brztl-playPauseBtn").html('<i class="fas fa-play"></i>').appendTo($controlButtons).on("click", function () {
                togglePlayPause(!isPlaying);
            });

            const $stopBtn = $("<button>").addClass("brztl-stopBtn").html('<i class="fas fa-stop"></i>').appendTo($controlButtons).on("click", function () {
                togglePlayPause(false);
                updateTime(0);
            });

            const $forwardBtn = $("<button>").addClass("brztl-forwardBtn").html('<i class="fas fa-forward"></i>').appendTo($controlButtons).on("click", function () {
                updateTime(currentTime + 5);
            });

            let speedIndex = settings.speedOptions.indexOf(playbackSpeed);
            const $speedBtn = $("<button>").addClass("brztl-speedBtn").text(`${playbackSpeed}x`).appendTo($controlButtons).on("click", function () {
                speedIndex = (speedIndex + 1) % settings.speedOptions.length;
                playbackSpeed = settings.speedOptions[speedIndex];
                $(this).text(`${playbackSpeed}x`);
                if (isPlaying) {
                    clearInterval(interval);
                    startPlayback();
                }
            });

            $progressContainer.on("mousedown touchstart", function (e) {
                isDragging = true;
                onDrag(e);
            });

            $(document).on("mousemove touchmove", onDrag);
            $(document).on("mouseup touchend", function () {
                isDragging = false;
            });

            function onDrag(e) {
                if (!isDragging) return;
                const offsetX = e.pageX || e.originalEvent.touches[0].pageX;
                const containerOffset = $progressContainer.offset().left;
                const containerWidth = $progressContainer.width();
                let posX = offsetX - containerOffset;
                posX = Math.max(0, Math.min(containerWidth, posX));
                const newTime = ((settings.isRTL ? containerWidth - posX : posX) / containerWidth) * totalDuration;
                updateTime(newTime);
            }  
            
            const instance = {
                updateTimeline(newTime) {
                    updateTime(newTime);
                },
                play() {
                    togglePlayPause(true);
                },
                pause() {
                    togglePlayPause(false);
                },
                setSpeed(speed) {
                    playbackSpeed = speed;
                    if (isPlaying) {
                        clearInterval(interval);
                        startPlayback();
                    }
                },
            };

            $(this).data("timelinePlayer", instance);

            updateTime(0);
        });
    };
}(jQuery));