

// Register service worker to control making site work offline



if ("serviceWorker" in navigator) {

    navigator.serviceWorker.register("/sw.js")

        .then(() => { console.log("Service Worker Registered"); });

}

function setCookie(cname,cvalue,exdays,domain) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/" + ";domain=" + domain;
}

function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

// Code to handle install prompt on desktop



$(document).ready(function () {

    var cookieName = getCookie("not-now");
    if(cookieName === "true"){
        console.log("you are already");
    }else{

        let deferredPrompt;
        const addBtn = document.querySelector(".add-button");

        const now_notBtn = document.querySelector(".now_not");

        addBtn.style.display = "none";



        window.addEventListener("beforeinstallprompt", (e) => {

            $("#pwa_modal").modal("show");


            // Prevent Chrome 67 and earlier from automatically showing the prompt

            e.preventDefault();

            // Stash the event so it can be triggered later.

            deferredPrompt = e;

            // Update UI to notify the user they can add to home screen

            addBtn.style.display = "block";



            addBtn.addEventListener("click", () => {

                // hide our user interface that shows our A2HS button
                $("#pwa_modal").modal("hide");


                addBtn.style.display = "none";

                // Show the prompt

                deferredPrompt.prompt();

                // Wait for the user to respond to the prompt

                deferredPrompt.userChoice.then((choiceResult) => {

                    if (choiceResult.outcome === "accepted") {

                        console.log("User accepted the A2HS prompt");

                    } else {

                        console.log("User dismissed the A2HS prompt");

                    }

                    deferredPrompt = null;

                });

            });
            const cureent_domain = getDomain();
            now_notBtn.addEventListener("click", () => {
                setCookie("not-now","true",30,`.${cureent_domain}`);
            });

        });

    }

});
