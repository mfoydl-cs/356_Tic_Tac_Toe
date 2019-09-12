


var table = document.getElementById("table");
var board= [" "," "," "," "," "," "," "," "," "];
var play= true;

$(document).ready(function(){
    $("#ng").on("click",function(event){
        board= [" "," "," "," "," "," "," "," "," "];
        for(var i=0;i<board.length;i++){
            $("#"+i.toString()).text(" ");
        }
        play=true;
        $("#winner").text("");
    });
    $(".cell").on("click",function(event){
        if(play){
            if(event.target.innerHTML===" "){
                event.target.innerHTML = "X";
                board[event.target.id]="X";
                $.ajax({
                    type: "POST",
                    contentType: "application/json",
                    data: JSON.stringify({
                        "grid": board
                    }),
                    dataType: "json",
                    url: window.location.href + "play",
                    success: function(response){
                        var nboard= response.grid;
                        for(i=0; i<nboard.length; i++){
                            if(nboard[i]!=board[i]){
                                board[i]= nboard[i];
                                $("#"+i.toString()).text(nboard[i]);
                            }
                        }
                        if(response.winner != " "){
                            play= false;
                            if(response.winner == "t"){
                                $("#winner").text("Tie!"); 
                            }
			                else{
                            	$("#winner").text("Winner: "+response.winner);
			                }
                        }
                    },
                    error: function(e){
                        console.log("Error: "+e);
                    }
                });
            }
        }
    });
});


