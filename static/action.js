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
            var params = {}
            params.twkey = $(this).parent().attr('id');

            var textInputs = $(this).parent().children("input:text");
            $.each(textInputs, function(index, item) {
                params[item.id] = item.value;
            });
            $.post("/taskweek/update/optimistic",
                   params,
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
});

