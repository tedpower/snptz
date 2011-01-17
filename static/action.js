$(document).ready(function(){
    // Attaches the hide and show actions for the main page
    $("#logo").click(function(event){
        showMain();
        history.pushState("", "main", "/");
        event.preventDefault();
    });
    $("#infoLink").click(function(event){
        showInfo();
        history.pushState("", "info", "/info");
        event.preventDefault();
    });
    $("#settingsLink").click(function(event){
        showSettings();
        history.pushState("", "settings", "/settings");
        event.preventDefault();
    });

    // Makes the back button work
    window.onpopstate = function(event) {
        if (document.location.pathname == '/') {
            showMain();
        }
        if (document.location.pathname == '/info') {
            showInfo();
        }
        if (document.location.pathname == '/settings') {
            showSettings()
        }
    };
    
    // Some helper functions
    function showMain() {
        $("#main").show();
        $("#info").hide();
        $("#settings").hide();
    }
    function showInfo() {
        $("#main").hide();
        $("#info").show();
        $("#settings").hide();
    }
    function showSettings() {
        $("#main").hide();
        $("#info").hide();
        $("#settings").show();
    }

    // On the settings page, do the post with ajax
    $("#settingsSubmit").click(function(event){
        $.post("/settings", 
               {firstname:$('#firstname').val(),
                lastname:$('#lastname').val(), 
                weeklyEmailsToggle:$('#weeklyEmailsToggle:checked').val(),
                timezone:$('#timezone').val()},
               function(data){
                   $("#notifications").html(data);
                   $('#notifications').addClass('notificationShow');
                   setTimeout(function(){
                       $('#notifications').removeClass('notificationShow');
                       showMain();
                       history.pushState("", "main", "/");
                    }, 2000);
               });
        event.preventDefault();
    });
    
    
    $("#newteamSubmit").click(function(event){
        $.post("/team/new/wtf",
               {newteamname:$('#newteamname').val()},
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
    $("#teams :checkbox").click(function(event){
        $.post("/team/toggle/wtf",
               {teamslug:$(this).attr('name')},
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
    $(".twedit").click(function(event){
        $.post("/taskweek/update",
            {twkey:$(this).parent().attr('id'),
             twedit:$(this).parent().children("textarea").val()},
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

