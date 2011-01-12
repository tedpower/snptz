// Attaches the hide and show actions for the main page
$(document).ready(function(){    
    $("#logo").click(function(event){
        $("#main").show();
        $("#info").hide();
        $("#settings").hide();
        history.pushState("", "main", "/main");
        event.preventDefault();
    });
    $("#infoLink").click(function(event){
        $("#main").hide();
        $("#info").show();
        $("#settings").hide();
        history.pushState("", "info", "/info");
        event.preventDefault();
    });
    $("#settingsLink").click(function(event){
        $("#main").hide();
        $("#info").hide();
        $("#settings").show();
        history.pushState("", "settings", "/settings");
        event.preventDefault();
    });
});

// Makes the back button work
window.onpopstate = function(event) {
    if (document.location.pathname == '/main') {
        $("#main").show();
        $("#info").hide();
        $("#settings").hide();
    }
    if (document.location.pathname == '/info') {
        $("#main").hide();
        $("#info").show();
        $("#settings").hide();
    }
    if (document.location.pathname == '/settings') {
        $("#main").hide();
        $("#info").hide();
        $("#settings").show();
    }
};