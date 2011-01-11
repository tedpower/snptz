$(document).ready(function(){    
    $("#infoLink").click(function(event){
        $("#main").hide();
        $("#info").show();
        $("#settings").hide();
        history.pushState("test", "test", "/info");
        event.preventDefault();
    });

    $("#logo").click(function(event){
        $("#main").show();
        $("#info").hide();
        $("#settings").hide();
        history.pushState("test", "test", "/main");
        event.preventDefault();
    });
    
    $("#settingsLink").click(function(event){
        $("#main").hide();
        $("#info").hide();
        $("#settings").show();
        history.pushState("test", "test", "/settings");
        event.preventDefault();
    });
});

