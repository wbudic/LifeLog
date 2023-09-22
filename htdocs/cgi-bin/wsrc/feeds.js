var ID = "#feeds";
function fetchFeeds(id){
    ID =   id?id:"#feeds";
    var pnl =$(ID);
    pnl.html(
    '<div><span style="border:1px solid Crimson;padding:5px;"><font color="Crimson">&nbsp;&nbsp;<b>P l e a s e &nbsp;&nbsp;    W a i t  &nbsp;&nbsp;!&nbsp;&nbsp;</b></font></span><br><img src="images/Wedges-9.1s-64px.png"></div>'
    );
    pnl.show();
    pnl.css('visibility','visible');
    $(document).scrollTop( $("#rss_anchor").offset().top );
    $.post('CNFServices.cgi', {service:'feeds',action:'list'}, displayFeeds).fail(
        function(response) {pnl.html("Service Error: "+response.status,response.responseText);pnl.fadeOut(10000);}
    );
}
function fetchFeed(feed) {
    ID = '#feeds';
    var pnl = $(ID);
    pnl.html(
    '<div><span style="border:1px solid Crimson;padding:5px;"><font color="Crimson">&nbsp;&nbsp;<b>&nbsp;&nbsp;Please &nbsp Wait ->  '+feed+' loading...&nbsp;&nbsp;</b></font></span><br><img src="images/Wedges-9.1s-64px.png"></div>'
    );
    pnl.show();
    pnl.css('visibility','visible');
    $.post('CNFServices.cgi', {service:'feeds', action:'read', feed:feed}, displayFeeds).fail(
        function(response) {pnl.html("Service Error: "+response.status,response.responseText);pnl.fadeOut(10000);}
    );
}
function displayFeeds(content){
    var pnl = $(ID);
    pnl.html(content);
    pnl.show();
    $(document).scrollTop( $("#rss_anchor").offset().top );
}
