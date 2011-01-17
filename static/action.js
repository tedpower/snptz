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
                    }, 1500);
               });
        event.preventDefault();
    });
    $(".plans").click(function(event){
        $(this).hide();
        $(this).siblings(".edit").show();
    });
    $(".cancel").click(function(event){
        $(this).parent().parent().hide();
        $(this).parent().parent().siblings(".plans").show();
        event.preventDefault();
    });
    $(".submit_optimistic").click(function(event){
        $(this).parent().parent().hide();
        $(this).parent().parent().siblings(".plans").show();
        $.post("/taskweek/update/optimistic",
            {twkey:$(this).parent().attr('id'),
             twedit:$(this).parent().children("textarea").val()},
               function(data){
                   $("#notifications").html(data);
                   $('#notifications').addClass('notificationShow');
                   setTimeout(function(){
                       $('#notifications').removeClass('notificationShow');
                    }, 1500);
               });
    event.preventDefault();
    });
    $(".submit_realistic").click(function(event){
        $(this).parent().parent().hide();
        $(this).parent().parent().siblings(".plans").show();
        $.post("/taskweek/update/realistic",
            {twkey:$(this).parent().attr('id'),
             twedit:$(this).parent().children("textarea").val()},
               function(data){
                   $("#notifications").html(data);
                   $('#notifications').addClass('notificationShow');
                   setTimeout(function(){
                       $('#notifications').removeClass('notificationShow');
                    }, 1500);
               });
    event.preventDefault();
    });
});

