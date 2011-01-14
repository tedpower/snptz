$(document).ready(function(){
    // Attaches the hide and show actions for the main page
    
    $("#logo").click(function(event){
        $("#main").show();
        $("#info").hide();
        $("#settings").hide();
        history.pushState("", "main", "/");
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
    
    // Makes the back button work
    window.onpopstate = function(event) {
        if (document.location.pathname == '/') {
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
    
    // On the settings page, do the post with ajax
    $("#settingsSubmit").click(function(event){
        $.post("/settings", 
               {firstname:$('#firstname').val(),
                lastname:$('#lastname').val(), 
                weeklyEmailsToggle:$('#weeklyEmailsToggle:checked').val(),
                timezone:$('timezone').val()},
               function(data){
                   $("#notifications").html(data);
                   $('#notifications').addClass('notificationShow');
                   setTimeout(function(){
                       $('#notifications').removeClass('notificationShow');
                       $("#main").show();
                       $("#info").hide();
                       $("#settings").hide();
                       history.pushState("", "main", "/");
                    }, 1500);
               });
        event.preventDefault();
    });
});

