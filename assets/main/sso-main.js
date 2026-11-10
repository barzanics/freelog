function setTablistRadio(name) {
    $("[name="+name+"]").on("change", function() {
        $("#" + event.target.value).addClass("active").siblings(".tablist-radio-pane").removeClass("active")
    })
}

function getOTPSMS(inputs) {
    if ("OTPCredential" in window && typeof AbortController !== "undefined") {
        const abortController = new AbortController();
        navigator.credentials.get({
            otp: { transport: ["sms"] },
            signal: abortController.signal
        }).then(function (otp) {
            if (inputs?.length > 1) {
                inputs.forEach((input, i) => {
                    input.value = otp.code?.[(otp.code.length - 1) - i]
                    input.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
                })
            } else {
                inputs.value = otp.code
                inputs.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
            }
        }).catch(function (error) {
            console.error("Error:", error);
        });
    }
}