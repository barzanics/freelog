$(document).ready(function() {
    // show sidebar
    $('.burger-button').click(function () {
        $('.media-sidebar').toggleClass('active');
        $('.media-sidebar').toggleClass('desktop-active');
        $('.resize-content').toggleClass('full');
        if ($('.media-sidebar').hasClass("active")) {
            $('.overlay').addClass('show')
        } else {
            $('.overlay').removeClass('show')
        }
    })

    // collapse sidebar
    $('.overlay').click(function () {
        $('.media-sidebar').removeClass('active')
        $('.media-sidebar').removeClass('desktop-active');
        $(this).removeClass('show')
    })

    // show search box in mobile
    $('.mobile-search > button').click(function () {
        $('.media-search-widget').addClass('active')
        setTimeout(() => {
            $("#media-search-input").focus()
        },50)
    })

    // remove search box in mobile
    $('.remove-searchbox').click(function () {
        $('.media-search-widget').removeClass('active')
        $('.media-search-widget').removeClass('has-suggestion')
        $('.media-search-suggestion').removeClass('typing')
        $('.media-search-overlay').removeClass("active")
    })


    // channel-search
    $('.channel-search-button').click(function () {
        $(this).removeClass('show')
        $(this).addClass('hide')
        $('.channel-search-form').removeClass('hide')
        $('.channel-search-form').addClass('show')
    })

    $('.channel-search-close').click(function () {
        $('.channel-search-form').addClass('hide')
        $('.channel-search-form').removeClass('show')
        $('.channel-search-button').removeClass('hide')
        $('.channel-search-button').addClass('show')
    })

    $('.chat-open-button').click(function () {
        $('#live').toggleClass('full')
        $('.chat-full-button').toggleClass('chat-full-button-display')
        $('.video-wrapper').toggleClass('video-resize')
        $('.chat-wrapper').toggleClass('chat-resize')
        if ($(window).width() < 992) {
            $('.chat-wrapper').toggleClass('active')
        } else {
            $('.chat-wrapper').removeClass('chat-resize')
        }
    })

    // remove the suggestion with empty input
    $('#media-search-input').keyup(function () {
        if ($(this).val() !== '') {
        $('.media-search-widget').addClass('has-suggestion')
        $('.media-search-overlay').addClass('active')
        $('.media-search-suggestion').addClass('typing')
        } else {
        $('.media-search-widget').removeClass('has-suggestion')
        $('.media-search-overlay').removeClass('active')
        $('.media-search-suggestion').removeClass('typing')
        }
    })

    // remove the suggestion with Search-Overlay

    $('.media-search-overlay').click(function () {
        $('.media-search-widget').removeClass('has-suggestion')
        $('.media-search-suggestion').removeClass('typing')
        $(this).removeClass('active')
    })
    
    $(".media-tooltip-info-cancel").on("click", function() {
        $(this).parents(".media-tooltip-info").removeClass("active")
    })
})

function closeAdsBox(id) {
    $("[data-ads-box-id]").each(function () {
       var adsBoxId = $(this).attr("data-ads-box-id")
       if (+adsBoxId === +id) $(this).stop().slideUp(300)
    })
}

function uploadFile(inputId) {
    document.getElementById(inputId).click();
}

function handleUploadingFile(fileInputId, resultDivId, aspectRatio, modalId, previewDivId, saveBtnId, dismissBtnId) {
    window.addEventListener('DOMContentLoaded', function () {
       var cropper;
       var saved = false;
       const resultDiv = document.getElementById(resultDivId)
       const resultDivImg = resultDiv.querySelector("img")
       const previewImg = document.getElementById(previewDivId)
       $("#"+ fileInputId).on("change", function(data) {
          const file = this.files[0]
          console.log("changed")
          if (!file) return
          $("#"+ modalId).modal("show")
          src = URL.createObjectURL(file)
          previewImg.src = src
       })
       
       $("#"+ modalId).on("shown.bs.modal", function() {
          cropper = new Cropper(previewImg, {
             aspectRatio,
             viewMode: 3,
             autoCropArea: 0.5,
             zoomable: false
          })
       })

       $("#"+ modalId).on("hidden.bs.modal", function() {
          cropper.destroy()
          cropper = null
       })
       
       $("#" + saveBtnId).on("click", function() {
          let imgSrc = cropper
             .getCroppedCanvas({})
             .toDataURL()
          resultDivImg.src = imgSrc
          $(resultDiv).show()
          $("#"+ fileInputId).parents(".select-file").hide()
       })

       $("#" + dismissBtnId).on("click",function() {
          $(resultDiv).hide()
          $("#"+ fileInputId).parents(".select-file").show()
          resultDivImg.src = ""
       })
    })   
 }

function barHeightApplyTo(element) {
    var tag = document.createElement("div");
    tag.id = "control-height";
    tag.style.height = "100vh";
    tag.style.width = "0";
    tag.style.position = "absolute";
    document.body.appendChild(tag);

    const actualHeight = window.innerHeight;
    const elementHeight = document.querySelector("#control-height").clientHeight;

    const barHeight = elementHeight - actualHeight;
    element.css("margin-bottom", barHeight + "px");
    document.body.removeChild(tag);
}