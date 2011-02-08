$(document).ready(function(){
    // Attaches the hide and show actions for the main page
    $("#logo").click(function(event){
        history.pushState("", "main", "/");
        showMain();
        //event.preventDefault();
        return false;
    });
    $("#infoLink").click(function(event){
        history.pushState("", "info", "/info");
        showInfo();
        //event.preventDefault();
        return false;
    });
    $("#settingsLink").click(function(event){
        history.pushState("", "settings", "/settings");
        showSettings();
        //event.preventDefault();
        return false;
    });
    $("#teamformLink").click(function(event){
        history.pushState("", "teamform", "/teamform");
        showTeamform();
        //event.preventDefault();
        return false;
    });

    // Makes the back button work
    window.onpopstate = function(event) {
        if (document.location.pathname == "/") {
            showMain();
        }
        if (document.location.pathname == "/info") {
            showInfo();
        }
        if (document.location.pathname == "/settings") {
            showSettings();
        }
        if (document.location.pathname == "/teamform") {
            showTeamform();
        }
    };
    
    // Some helper functions
    function showMain() {
        $("#main").show();
        $("#info").hide();
        $("#settings").hide();
        $("#teamform").hide();
    }
    function showInfo() {
        $("#main").hide();
        $("#info").show();
        $("#settings").hide();
        $("#teamform").hide();
    }
    function showSettings() {
        $("#main").hide();
        $("#info").hide();
        $("#settings").show();
        $("#teamform").hide();
    }
    function showTeamform() {
        $("#main").hide();
        $("#info").hide();
        $("#settings").hide();
        $("#teamform").show();
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
        
    // Add the event listeners for the main edit stuff
    hookupAjaxEdit();
    
    // Putting this in a function so we can add the listeners to new dom elements
    function hookupAjaxEdit() {
        $(".plans").click(function(event){
            $(this).hide();
            $(this).siblings(".edit").show();
            $(this).siblings(".edit").find('textarea').focus();
        });

        $(".cancel").click(function(event){
            $(this).parent().parent().hide();
            $(this).parent().parent().siblings(".plans").show();
            event.preventDefault();
        });

        $(".submit_optimistic").click(function(event){
            var $planWrap = $(this).parent().parent().parent();
            $.post("/taskweek/update/optimistic",
                {twkey:$(this).parent().attr('id'),
                 twedit:$(this).parent().children("textarea").val()},
                   function(data){
                       $planWrap.replaceWith(data);
                       hookupAjaxEdit();
                   });
        event.preventDefault();
        });
        
        $(".submit_realistic").click(function(event){
            var $planWrap = $(this).parent().parent().parent();
            $.post("/taskweek/update/realistic",
                {twkey:$(this).parent().attr('id'),
                 twedit:$(this).parent().children("textarea").val()},
                   function(data){
                       $planWrap.replaceWith(data);
                       hookupAjaxEdit();
                   });
        event.preventDefault();
        });
    }
    
    // This will allow you to close the edit area by clicking the background
    $("#bg").click(function(event){
        $(".edit").hide();
        $(".plans").show();
    });
    
    // TODO refactor this
    $("#newteamSubmit").click(function(event){
        $.post("/team/new/wtf",
               {newteamname:$('#newteamname').val(),
               colleagues:$('#colleagues').val()},
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
    $(".acceptInviteLink").click(function(event){
        $.post("/team/join/wtf",
               {invitekey:$(this).parent().attr('id')},
               function(data){
                   $("#notifications").html(data);
                   $('#notifications').addClass('notificationShow');
                   setTimeout(function(){
                       $('#notifications').removeClass('notificationShow');
                    }, 1500);
               });
        event.preventDefault();
    });
    $(".declineInviteLink").click(function(event){
        $.post("/team/decline/wtf",
               {invitekey:$(this).parent().attr('id')},
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
