/*
 Programed by: Will Budic
 Open Source License -> https://choosealicense.com/licenses/isc/
*/
var MNU_SCROLLING = false;

var QUILL, QUILL_PNL;
var Delta;
var RTF_SET = false;
var CHANGE;

var _show_all = true;

var DEF_BACKGROUND = 'white';

var RTF_DOC_RESIZED = false;
var RTF_DOC_ORIG;
var RTF_DOC_CUR_ID;
var TXT_LOG_ROWS = 3;
var TIME_STAMP;
var LOCALE;
var TIMEZONE; 
var DBI_LVAR_SZ;
var EDIT_LOG_TXT = "";

function onBodyLoadGeneric() {
    $("input[type=submit], input[type=reset], .ui-widget-content, button, .a_").button();
    $("#btn_save_doc").button();
    $("#btn_zero_doc").button();  if($("#rtf_buffer").val()==0){$("#btn_zero_doc").hide()};
    $("#btn_load_doc").button();  $("#btn_load_doc").hide();
    if(!LOCALE || LOCALE==="English"){
        LOCALE = "en-US";
    }
}

function onBodyLoad(toggle, locale, tz, today, expires, rs_cur, log_limit) {

    LOCALE      = locale;
    TIMEZONE    = tz;    
    TIME_STAMP  = new Date(today);
    DBI_LVAR_SZ = parseInt(log_limit);    
    
    onBodyLoadGeneric();
    

    if (toggle) {
        this.toggle("#div_srh", false);
    }
    if(rs_cur){
        _show_all = false;//toggle type switch
        showAll();
    }
    $('#ed').datetimepicker({
        dateFormat: 'yy-mm-dd',
        timeFormat: 'HH:mm:ss',
        stepHour: 1,
        stepMinute: 10,
        stepSecond: 10,
        firstDay: 1
    });

    $('#srh_date_from').datepicker({
        dateFormat: 'yy-mm-dd',
        firstDay: 1
    });

    $('#srh_date_to').datepicker({
        dateFormat: 'yy-mm-dd',
        firstDay: 1
    });
    $('#ed').poshytip({
        content: "Select here date and time of your log.",
        className: 'tip-yellowsimple',
        showTimeout: 1,
        alignTo: 'target',
        alignX: 'center',
        alignY: 'bottom',
        offsetY: 5,
        allowTipHover: false
    });
    $('#ec').poshytip({
        content: "Select here the category for your log.",
        className: 'tip-yellowsimple',
        showTimeout: 1,
        alignTo: 'target',
        alignX: 'center',
        alignY: 'bottom',
        offsetY: 5,
        allowTipHover: false
    });
    $('#el').poshytip({
        content: "This is your log entry,<br> can't be left empty.",
        className: 'tip-yellowsimple',
        showOn: 'focus',
        alignTo: 'target',
        alignX: 'left',
        alignY: 'center',
        offsetX: 5,
        showTimeout: 50,
        allowTipHover: true
    });
    $('#am').poshytip({
        content: "Symbolic amount in your local or preferred currency. Can be left empty.",
        className: 'tip-yellowsimple',
        showOn: 'focus',
        alignTo: 'target',
        alignX: 'center',
        alignY: 'bottom',
        offsetX: 5,
        showTimeout: 100
    });
    $('#am').click(function(e){
        e.preventDefault();
        let v = $('#am').val();
        if(v.length==0 || v==0.00){
            const regex = /^[\D]?\d+\.*\d*/gm;
            let str = $('#el').val();
            let m; var tot = 0;

            while ((m = regex.exec(str)) !== null) {                
                if (m.index === regex.lastIndex) {
                    regex.lastIndex++;
                }
                m.forEach( (match, groupIndex) => {
                    let v = `${match}`;
                    let d = v.startsWith('/');
                    let m = v.startsWith('*');
                    if(d||m){v=v.substring(1)}
                    let s = v.startsWith('-');
                    v = v.replace(/^\./g,'0.');
                    v = v.replace(/^\D/g,'');
                    //console.log(`Found match, group ${groupIndex}: ${match}`);
                    if(d){
                        if(s){ tot /= -parseFloat(v);
                        }else{ tot /= parseFloat(v); }
                    }else if(m){
                        if(s){ tot *= -parseFloat(v);
                        }else{ tot *= parseFloat(v); }
                    }else{
                        if(s){ tot -= parseFloat(v);
                        }else{ tot += parseFloat(v); }
                    }
                });
            }
            if(tot==0){tot=""}
            $('#am').val(tot.toFixed(2));            
        }


     });

    $('#sss_xc').poshytip({
        content: "When checked, system will try to remember your view mode while in session.",
        className: 'tip-yellowsimple',
        showOn: 'focus',
        alignTo: 'target',
        alignX: 'center',
        alignY: 'bottom',
        offsetX: 5,
        showTimeout: 100
    });   

    $("#menu_close").poshytip({
        content: "<b>Do not click on this</b> little heart of mine,<br> <b>the menu will be closed</b>!",
        className: 'tip-yellowsimple',
        showOn: 'mouseover',        
        alignTo: 'target',
        alignX: 'center',
        alignY: 'bottom',    
        showTimeout: 100    
    });

    $("#menu_close").click(function() {
        $('#dutchie_close_chime').trigger('play');
        $("#menu_page").effect("shake", {}, 1000, function() {
            $("#menu_page").effect("drop", { direction: "down" }, 1500, function() {
                $("#menu_page").hide();
            })
        })
    });

    $("#dutch_left").poshytip({
        content: "<span class='ui-icon ui-icon-arrowthick-1-w' style='float:none;'></span>Pass the dutchie to the <b>left</b> on side.",
        className: 'tip-yellowsimple',
        showOn: 'mouseover',        
        alignTo: 'target',
        alignX: 'center',
        alignY: 'bottom',    
        showTimeout: 100    
    });
    $("#dutch_right").poshytip({
        content: "Pass the dutchie to the <b>right</b> on side.<span class='ui-icon ui-icon-arrowthick-1-e' style='float:none;'></span>",
        className: 'tip-yellowsimple',
        showOn: 'mouseover',        
        alignTo: 'target',
        alignX: 'center',
        alignY: 'bottom',    
        showTimeout: 100    
    });


    $('#ec').show();

    $("#RTF").prop("checked", false);
    
    if ($('#editor-container').length) {        
        QUILL = new Quill('#editor-container', {
            placeholder: 'Enter your Document here...',
            theme: 'snow',
            modules: {
                formula: true,
                syntax: true,                
                toolbar: '#toolbar-container'            
            }
        });
        Delta = Quill.import('delta');
        CHANGE = new Delta();
        
        // toggleDocument();
    }

    var rgb = $('#editor-container').css('background-color');
    if(rgb){
        DEF_BACKGROUND = RGBToHex(rgb);
        $("#fldBG").val(DEF_BACKGROUND);
        // let bg=RGBToHex('rgb(180, 169, 169)'); //<-is set in css file
        // $('#toolbar-container').css('background-color',bg);
        $('#toolbar-container').css('color',DEF_BACKGROUND);
        
    }
    var amf = $( "#amf" );//Amount Field Type dropdown
    var ec = $( "#ec" );  //Category dropdown
    $( "#amf2" ).selectmenu({style: "dropdown", width:100});
    amf.selectmenu({style: "dropdown", width:100,
        change: function( event, data ) {
        var evv =ec.val();
            if(ec.val()<2||evv==32||evv==35||data.item.value == 0){
                var sel = null;
                if(data.item.label == "Income"){ sel = 35; }
                else if(data.item.label == "Expense"){sel = 32; }
                else if(data.item.value == 0 && (evv == 35||evv==32)){sel = 1;}
                if(sel){
                    ec.val(sel);
                }
            }
        }});
    

    jQuery.fn.dispPos = function () {
        this.css("position","absolute");
        this.css("top", Math.max(0, (($(window).height() - $(this).outerHeight())-320 ) +
                                                    $(window).scrollTop()) + "px");
        this.css("left", Math.max(0, (($(window).width() - $(this).outerWidth()) / 6) - 100 +
                                                    $(window).scrollLeft()) + "px");
        this.css( "zIndex", 8 );
        return this;
    }

    jQuery.fn.dropdownPos = function (e,desc) {
        var pnl = $("#cat_desc");
        var top = e.css('top');
        var height= e.css('height');
        var width = e.css('width');
        var left = e.css('left');
        var pwidth = pnl.css('width');
            top = parseInt(top.replace(/px/, ""));
            height = parseInt(height.replace(/px/, ""));
            width = parseInt(width.replace(/px/, ""));
            left = parseInt(left.replace(/px/, ""));
            pwidth = parseInt(pwidth.replace(/px/, ""));
            top += height - 5;
            left -= (pwidth/2);
            //pnl.html("["+left+","+top+","+height+","+width+"]"+desc);
            pnl.html(desc);
            pnl.css('top', top+'px');
            pnl.css('left', left+'px');
            pnl.show();
    }

    $("#dropdown-standard a").click(function(e){
        e.preventDefault();
        var ci = $(event.target).parent(); ci = ci.attr('id');
        var lbl = $(e.target).text();
        lbl = lbl.replace(/\s*$/g, "");
        lbl = lbl + "&nbsp;".repeat(16-lbl.length);
        $("#lcat").html(lbl);
        $("#ec").val(ci);
        $("#cat_desc").show();
    }).mouseenter(function(e){
        var pr = $(event.target).parent(); pr = pr.attr('id');
        if(pr){
            var pnl = $("#cat_desc");
            var desc = $("meta[id='cats["+pr+"]']").attr('content');
            $.fn.dropdownPos($("#dropdown-standard"), desc);
        }
    }).mouseleave(function(e){$("#cat_desc").hide();});


    $("#dropdown-standard-v a").click(function(e){
        e.preventDefault();
        var ci = $(event.target).parent(); ci = ci.attr('id');
        var lbl = $(e.target).text();
        lbl = lbl.replace(/\s*$/g, "");
        lbl = lbl + "&nbsp;".repeat(16-lbl.length);
        $("#lcat_v").html(lbl);
        $("#vc").val(ci);        
        $("#cat_desc").show();        
    }).mouseenter(function(e){
        var pr = $(event.target).parent(); pr = pr.attr('id');
        if(pr){
            var pnl = $("#cat_desc");
            var desc = $("meta[id='cats["+pr+"]']").attr('content');
            $.fn.dropdownPos($("#dropdown-standard-v"), desc);
        }
    }).mouseleave(function(e){$("#cat_desc").hide();});



    $("#dropdown-standard-x a").click(function(e){
        e.preventDefault();
        var ci = $(event.target).parent(); ci = ci.attr('id');
        var lbl = $(e.target).text();
        lbl = lbl.replace(/\s*$/g, "");
        lbl = lbl + "&nbsp;".repeat(16-lbl.length);
        $("#lcat_x").html(lbl);
        $("#xc").val(ci);
        $("#cat_desc").show();
    }).mouseenter(function(e){
        var pr = $(event.target).parent(); pr = pr.attr('id');
        if(pr){
            var pnl = $("#cat_desc");
            var desc = $("meta[id='cats["+pr+"]']").attr('content');
            $.fn.dropdownPos($("#dropdown-standard-x"), desc);
        }
    }).mouseleave(function(e){$("#cat_desc").hide();});

    
    $( "#dlgValidation" ).dialog({
        dialogClass: "alert",
        buttons: [
          {
            text: "OK",
            click: function() {
              $( this ).dialog( "close" );
            }
          }
        ]
      });
    //Following is needed as the dropdown registers somewhere in lib. to show on when enter key is hit.
    $.fn.enterKey = function (fnc) {
        return this.each(function () {
            $(this).keypress(function (ev) {
                var keycode = (ev.keyCode ? ev.keyCode : ev.which);
                if (keycode == 13) {
                    fnc.call(this, ev);
                    ev.preventDefault();
                }
            })
        })
    }
    $("#rs_keys").enterKey(function (ev) {});


    $('#rs_keys').bind('keypress', function(event) {
        if(event.which === 13) {
          $(this).next().focus();
        }
      });


    setPageSessionTimer(expires);


    $(function() {        
        $( "#rs_keys, #rs_keys2" ).autocomplete({
            source: AUTOWORDS
            });
    });
    var CHK_PREV;
    
    $("#frm_log td").mouseover(function(e){
        if(e.target != 'thr'){
            var chk = $(e.target).find('input[name="chk"]');
            var tr = e.target.parentNode.closest("tr");
            if(tr.id != "summary_row" && tr.id !="brw_row"){
                if(CHK_PREV && !CHK_PREV.prop('checked')){        
                    CHK_PREV.closest("tr").removeClass("hover");
                }
                $(e.target.parentNode).closest("tr").addClass("hover");
                CHK_PREV = chk;
            }
        }
      return false;
    }).mouseout(function(e) {
        CHK_PREV = $(e.target).find('input[name="chk"]');
        if(!CHK_PREV.prop('checked')){
            $(e.target.parentNode).closest("tr").removeClass("hover");
        }
    });
    

    if($("#isInViewMode").val()>0){
        this.toggle('#div_srh', true); 
        this.toggle('#div_log', true);
    }

    $(function() {        
        $( "#rs_keys, #rs_keys2" ).autocomplete({
            source: AUTOWORDS
            });
    });

    display("Log page is ready!", 5);    
    
}

function encodeText(){
    var el = $("#frm_entry [name=log]");
    var txt = el.val();
    txt = txt.replace(/\r\n/g, "\\n");
    txt = txt.replace(/\n/g, "\\n");
    el.val(txt);
}
function decodeText(){
    var el = $("#frm_entry [name=log]");
    var txt = el.val();
        txt = txt.replace(/\\n/g, "\n");
    el.val(txt);
}

function formValidation() {
    // if ($("#ec option:selected").val() == 0) {
    //     alert("Category -> has not been selected!");
    //     return false;
    // }
    var dt = $("#frm_entry [name='date']").val();
    var i = dt.indexOf('id=');
    if(i>0){
        dt = dt.substring(0, i-1);
        $("#frm_entry [name='date']").val(dt);
    }
    return validate(dt, $("#frm_entry [name='log']").val());
}
function formDelValidation() {
return true;
}

function backToMain() {// func. required as chrome submits whole form on if buttons are not falsed.
    $("[name='confirmed']").val(0);    
    //window.location.href='main.cgi';
    history.back();
    return false;
}

function validate(dt, log) {
    var tm, msg;
    if (!Date.parse(dt)) {
        msg = "<b>Date</b> field entry -> " + dt + " is Invalid can't submit!<br>";
    }
    else{
        tm = validTime(dt.substring(dt.indexOf(" ") + 1));
        if(tm){
            msg = "<b>Date</b> field entry wrong time -> " + tm;
        }
        else{
            msg = "";
        }
    }
    if ($("#ec").val() == 0) {
        msg =  msg + "<b>Category</b> field selection hasn't been made!<br>";
    }
    if (!log) {
        msg = msg + "<b>Log</b> field entry can't be empty, can't submit!<br>";
    }
    else if (log.length>DBI_LVAR_SZ) {
        msg = msg+ "<b>Log</b> Server has an text limit of (" + DBI_LVAR_SZ +" ) Your log size is:" + log.length;
    }
    if(msg){
        return dialogModal( "Sorry Form Validation Failed", msg);
    }
    $('#frm_entry').hide();    
    encodeText();
    return true;
}

function validTime(val) {
    // regular expression to match required time format
    re = /^(\d{2}):(\d{2}):(\d{2})([ap]m)?$/;
    var fld = $("frm_entry").date;
    var msg;
    if (val != '') {
        if (regs = val.match(re)) {
            // 12-hour value between 0 and 24
            if (regs[1] < 0 || regs[1] > 23) {
                msg += " Invalid value for hours: " + regs[1];
                fld.focus();
            }
            // minute value between 0 and 59
            if (regs[2] > 59) {
                msg += " Invalid value for minutes: " + regs[2];
                fld.focus();
            }
            // seconds value between 0 and 59
            if (regs[3] > 59) {
                msg += " Invalid value for seconds: " + regs[2];
            }
        } else {
            msg = "Invalid time format: " + val;
            fld.focus();
        }
        return msg;
    }
}



function setNow() {

    var date = document.getElementById("frm_entry").date;
    var dt = new Date();
    let options = {timeZone: TIMEZONE, hour12:false};
    let [month, day, year]      = dt.toLocaleDateString(LOCALE, options).split("/")
    let [hour, minute, seconds] = dt.toLocaleTimeString(LOCALE, options).split(/:| /);
    month = fix0(month); day    = fix0(day);
    hour  = fix0(hour);  minute = fix0(minute); seconds = fix0(seconds);

    date.value =  year + "-" + month + "-" + day + " " + hour + ":" + minute + ":" + seconds;
    $("#submit_is_edit").val("0");
    toggleDoc(true);    
    EDIT_LOG_TXT = "";
    return false;
}

function fix0(v) {
    v = parseInt(v);
    if (v < 10) {
        return "0" + v;
    }
    return v;
}


function decodeToHTMLText(txt) {

    txt = txt.replace("/&#60;/g", "<");
    txt = txt.replace("/&#62;/g", ">");
    txt = txt.replace("/&#9;/g", "\t");
    txt = txt.replace(/br\s*[\/]?>/gi, "\n");
    txt = txt.replace(/\\n/g, "\n");    
    txt = txt.replace(/&#10;/g, "\n");    
    txt = txt.replace(/&#34;/g, "\"");
    txt = txt.replace(/&#39;/g, "'");
    

    return txt;
}

const REGX_BTM = /(?<o>^\<b\>)(?<title>.+)(?<c>\<\/b\>)/gi;
const REGX_BTM_SUBST = `*$2*`;

function decodeToText(txt) {
    //bug 7 fix
    txt = txt.replace(/<hr>.*RTF<\/button>/gm, "");
    txt = txt.replace(/<br\s*[\/]?>/gi, "\n");
    //If first line bolded
    
    let res = txt.matchAll(REGX_BTM);
    if(res){
       txt = txt.replace(REGX_BTM, REGX_BTM_SUBST);        
    }
    return txt;
}

function edit(row) {

    var ed_v = $("#y" + row); //date
    var et_v = $("#t" + row); //time
    var ea_v = $("#a" + row); //amount
    var tag  = $("#g" + row); //orig. tagged log text.
    var log  = $("#v" + row); //log
    var rtf  = $("#r" + row); //RTF doc
    var amt  = $("#f" + row); //Amount type.
    var sticky  = $("#s" + row); //RTF doc
    var isRTF = (rtf.val()>0?true:false);
    var isSticky = (sticky.val()>0?true:false);
    var txt;
    if(!isRTF){
            $('#rtf_doc').hide();
            $('#tbl_doc').hide();
            $('#toolbar-container').hide();
            $("#btn_load_doc").hide();
    }

    $("html, body").animate({ scrollTop: 0 }, "slow", function(){$("#el").focus()});
    if (tag.length) {
        txt = decodeToHTMLText(tag.val());

    } else {
        txt = log.html();
        txt = txt.replace(/<br>/g,"\n");
        txt = txt.replace(/^<div class=\"log\">/,"");
        txt = txt.replace(/<\/div>$/,"");
        txt = decodeToText(txt);
    }
    $("#el").val(txt); EDIT_LOG_TXT = txt;
    $("#ed").val(ed_v.val() + " " + et_v.html()); //Time field
    var val = ea_v.text();
    val = val.replace(/\,/g,"");
    $("#am").val(val); //Amount field, fix 04-08-2019 HTML input doesn't accept formatted string.
    $("#RTF").prop('checked', isRTF);
    $("#STICKY").prop('checked', isSticky);

    if(isRTF){
        display("Loading RTF: "+ ed_v.val() );
        RTF_DOC_CUR_ID = row;
        loadRTF(false, row);
    }else{
        display("Editing: "+ ed_v.val(),3);
        RTF_DOC_CUR_ID = 0;
    }

    //Select category
    var ec_lb = $("#c" + row).text();
    var ec_id = $("meta[name='"+ec_lb+"']").attr('id');
    ec_id = ec_id.replace(/^cats\[/g,'');
    ec_id = ec_id.replace(/\]$/g,'');
    $("#lcat").html(ec_lb);
    $("#ec").val(ec_id);


    $("#submit_is_edit").val(row);

    //Amount type
    ec_v = amt.val();
    $("#amf").focus();
    $("#amf").val(ec_v);
    $("#amf").selectmenu('refresh');

    $("#div_log").show();
    $("#el").focus();

    return false;
}


function selectAllLogs() {
    var chks = document.getElementsByName("chk");
    for (var i = 0, n = chks.length; i < n; i++) {
        chks[i].checked = true;
    }
    return false;
}


function submitTop(top) {
    var frm = document.getElementById("frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value  = 0;
    frm.rs_cur.value  = 0;
    frm.rs_prev.value = top;
    frm.submit_is_view.value = 1;
    frm.submit();

    return false;
}

function submitPrev(tbl_rc, limit) {

    var frm = document.getElementById("frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value = 0;
    frm.rs_cur.value = tbl_rc + limit;
    frm.rs_prev.value = tbl_rc;
    frm.submit_is_view.value = 1;
    frm.submit();

    return false;
}

function submitNext(tbl_rc, limit) {

    var frm = document.getElementById("frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value = 0;
    frm.rs_cur.value = parseInt(tbl_rc);
    frm.rs_prev.value = tbl_rc + limit;
    frm.submit_is_view.value = 1;
    frm.submit();

    return false;
}

function submitEnd(limit) {
    var frm = document.getElementById("frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value  = 0;
    frm.rs_cur.value  = limit;
    frm.rs_prev.value = limit * 2;
    frm.submit_is_view.value = 1;
    frm.submit();

    return false;
}



function viewAll() {
    display("Please Wait!");
    var frm = document.getElementById("frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value = 1;
    frm.rs_cur.value = 0;
    frm.rs_prev.value = 0;
    frm.submit_is_view.value = 1;
    frm.submit();
    
    return false;
}

function resizeLogText() {

    $("#div_log .collpsd").show(); 
    $('#div_log').show();
     
    if(TXT_LOG_ROWS == 3){
        TXT_LOG_ROWS = 10;        
    }
    else{
        TXT_LOG_ROWS = 3;
    }
    $("#el").prop("rows",TXT_LOG_ROWS)
    
}

function resizeDoc() {
    var css = $("#editor-container").prop('style');
    if(RTF_DOC_RESIZED){
        RTF_DOC_RESIZED = false;
        css.height = RTF_DOC_ORIG;
    }
    else{
        RTF_DOC_RESIZED = true;
        RTF_DOC_ORIG = css.height;
        css.height = '480px';
    }
}
function resetDoc(){
    if (RTF_SET) { QUILL.setText(""); }
    $("#submit_is_edit").val("0");
    toggleDoc(true);
    $('#btn_load_doc').hide();
}



function resetView() {
    $("#frm_srch input").val("");
    $("#srch_reset").val(1);
    $("#idx_cat").val(0);
    $('#vc>option[value="0"]').prop('selected', true);
    $('#xc>option[value="0"]').prop('selected', true);
    $("#sss_xc").prop('checked', false);
    $("#frm_srch").submit();
}

function updateSelCategory(sel) {
    if (sel.id == "ec") {
        var cat = $("#idx_cat");
        cat.value = sel.options[sel.selectedIndex].value;
    }
}

function toggleVisibility(target, ensureOff) {
    if (!ensureOff) {
        $(target).toggle();
    } else {
        $(target).hide();
    }
}


function toggleDoc(whole) {


    if(whole){
        if($("#RTF").prop('checked')){
            $("#rtf_doc").show();
            $('#tbl_doc').show();
           // $('#toolbar-container').show();
        }
        else{
            $("#rtf_doc").hide();
            $('#tbl_doc').hide();
            //$('#toolbar-container').hide();
        }
    }
    else{
        $("#rtf_doc").toggle();
    }

    if (!RTF_SET) {

        CHANGE = new Delta();
        QUILL.on('text-change', function(delta) {
            CHANGE = CHANGE.compose(delta);
        });

        setInterval(function() {
            if (CHANGE.length() > 0) {
                console.log('Saving changes', CHANGE);
                CHANGE = new Delta();
            }
        }, 10 * 1000);
        RTF_SET = true;
    }


}


function hide(id) {
    $(id).hide();
    return false;
}

function show(id) {
    $(id).show();
    return false;
}

function toggle(id, mtoggle) {
   //Menu button untoggle it up first. Complex interaction situation.
    if(mtoggle){
        if(!$(id+" .collpsd").is(":visible")){
            $(id+" .collpsd").show();
            $(id).show();
        }
        else{
            var distance = $(id).offset().top;
            if($(this).scrollTop() <= distance){
                $(id).toggle();
            }        
        }
    }
    else{
        $(id).toggle();
    }
    $("html, body").animate({ scrollTop: 0 }, "fast");
    return false;
}


function showAll() {

   show("#menu_page");
   
   if(_show_all){
        $("#lnk_show_all").text("Hide All");   
        show("#div_log");
        show("#div_srh");
        show("#tbl_hlp");
        show("#tbl_doc");
        _show_all = false;
   }
   else{
        $("#lnk_show_all").text("Show All");
        hide('#cat_desc');
        hide("#div_log");
        hide("#div_srh");
        hide("#tbl_hlp");
        hide("#tbl_doc");
        _show_all = true;
   }


   $("html, body").animate({ scrollTop: 0 }, "fast");
   
    return false;
}

function display(desc, times){
    var pnl = $("#cat_desc");
    if(!times){
        times = 1;
    }
    pnl.html(desc);
    pnl.dispPos(true);
    pnl.show();
    pnl.fadeOut(1000*times);
    $('#menu_page').css('visibility','visible');
}

function moveMenuLeft (){
    $('#menu_page').css('margin-left','.5vw');
    $('#dutchie_chime').trigger('play');
return false;
}
function moveMenuRight (){
    $('#menu_page').css('margin-left','90.5vw');
    $('#dutchie_close_chime').trigger('play');
return false;
}

function viewRTFLogs(btn){
    $("#vrtf").val(1);
}

function viewByAmountType(btn) {
    var aa = $("#amf2 option:selected");
        aa.val(parseInt(aa.val())+1);
}

function viewByCategory(btn) {
    $("#rs_keys").value = "";
    $("#xc").val(0);
}
function viewExcludeCategory(btn) {
    $("#rs_keys").value = "";
    $("#vc").value = "0";
}

function addInclude() {
    var vc = $("#vc").val();
    var lst = $("#vclst");
    if(vc == 0){
        return dialogModal("Can't add include!", "Must select a category to add to a list of includes.");
    }

    var sel = $("meta[id='cats["+vc+"]']").attr('name');
    var div = $('#divvc');
    var tagged = $('#divvc').text();
    var reg = new RegExp(sel);

    if(!tagged.match(reg)){
        $('#divvc_lbl').show();
        if(tagged.length>0){
            div.text(tagged + ',' + sel);
            lst.val(lst.val() + ',' + vc);
        }
        else{
            div.text(sel);
            lst.val(vc);
        }
    }
return false;
}

function removeInclude() {
    var vc = $("#vc").val();
    var xlst = $("#xclst");
    if(vc == 0){
        return dialogModal("Can't remove exclude!", "Must select a category to remove from list of includes.");
    }
    var sel = $("meta[id='cats["+vc+"]']").attr('name');
    //var sel = $('#vc option:selected');
    var div = $('#divvc');
    var tagged = $('#divvc').text();
    var tagids = xlst.val();
    var reg = new RegExp(sel);
    if(tagged.match(reg)){
            tagged = tagged.replace(reg,'');
            tagged = tagged.replace(/\,\,/,'\,');
            tagged = tagged.replace(/^\,+|\,+$/g,'');
            tagids = tagids.replace(vc,'');
            tagids = tagids.replace(/\,\,/,'\,');
            tagids = tagids.replace(/^\,+|\,+$/g,'');
            if(tagged.length==0){
                $('#divvc_lbl').hide();
            }
            div.text(tagged);
            xlst.val(tagids);
    }

return false;
}

function addExclude() {
    var xc = $("#xc").val();
    var xlst = $("#xclst");
    if(xc == 0){
        return dialogModal("Can't add exclude!", "Must select a category to add to a list of excludes.");
    }

    var sel = $("meta[id='cats["+xc+"]']").attr('name');
    var div = $('#divxc');
    var tagged = $('#divxc').text();
    var reg = new RegExp(sel);

    if(!tagged.match(reg)){
        $('#divxc_lbl').show();
        if(tagged.length>0){
            div.text(tagged + ',' + sel);
            xlst.val(xlst.val() + ',' + xc);
        }
        else{
            div.text(sel);
            xlst.val(xc);
        }
    }

return false;
}

function removeExclude() {
    var xc = $("#xc").val();
    var xlst = $("#xclst");
    if(xc == 0){
        return dialogModal("Can't remove exclude!", "Must select a category to remove from list of excludes.");
    }
    var sel = $("meta[id='cats["+xc+"]']").attr('name'); //_CATS_NAME_MAP.get(xc.val());
    //var sel = $('#xc option:selected');
    var div = $('#divxc');
    var tagged = $('#divxc').text();
    var tagids = xlst.val();
    var reg = new RegExp(sel);
    if(tagged.match(reg)){
            tagged = tagged.replace(reg,'');
            tagged = tagged.replace(/\,\,/,'\,');
            tagged = tagged.replace(/^\,+|\,+$/g,'');
            tagids = tagids.replace(xc,'');
            tagids = tagids.replace(/\,\,/,'\,');
            tagids = tagids.replace(/^\,+|\,+$/g,'');
            if(tagged.length==0){
                $('#divxc_lbl').hide();
            }
            div.text(tagged);
            xlst.val(tagids);
    }

return false;
}

function resetInclude(){
  $("#vc").val(0);
  $('#divxc').text("");
  $("#vclst").val("");
  $("#lcat_v").html("&nbsp;&nbsp;&nbsp;<font size=1>-- Select --</font></i>&nbsp;&nbsp;&nbsp;");
  $("#amf2").val(0);
  $("#amf2").selectmenu('refresh');
  return false;
}

function resetExclude(){
    $("#xc").val(0);
    $('#divxc').text("");
    $("#lcat_x").html("&nbsp;&nbsp;&nbsp;<font size=1>-- Select --</font></i>&nbsp;&nbsp;&nbsp;");
    $("#xclst").val("");
    return false;
}

function viewByDate(btn) {
    //	alert(btn.value);
}

function submitNewCategory() {

    var frm = $("#frm_config");    
    $("#frm_config [name='cchg']").val(2);
    return true;
}

function deleteSelected() { 
    display("Please Wait!",150);
    $("#opr").val(0);  
    $("#del_sel").click();
    display("Please Wait!",150);
    return false;
}
function dateDiffSelected() {
    display("Please Wait!");
    $("#opr").val(1);
    return true;
}
function exportSelected() {
    display("Please Wait!");
    $("#opr").val(2);
    return true;
    
}
function viewSelected() {
    display("Please Wait!");
    $("#opr").val(3);
    return true;
}



function exportToCSV(dat, view){
    var csv;
    if(dat == 'cat'){  csv = view ? 4:3;  }
    else
    if(dat == 'log'){  csv = view ? 2:1;  }
    window.location = "config.cgi?csv="+csv;
}

function sumSelected() {
    var chks = document.getElementsByName("chk");
    var sum = 0; var amount=0; var html="";
    for (var i = 0, n = chks.length; i < n; i++) {
        if (chks[i].checked) {
            let id = chks[i].value;
            let am = $("#a"+id).text();
            let ct = $("#c"+id).text();
            let at = $("#f"+id).val();           

            am = am.replace(/\,/g,"");//rem formatting
            if(ct=='Expense' || at=='2'){
                sum = sum - Number(am);
                html += "-"+am+"<br>";
            }else
            if(ct=='Income' || at=='1'){ //marked as income or category is income type for amount.
                sum = sum + Number(am);
                html += "+"+am+"<br>";
            }else{
                amount += Number(am);
                html += "<i>"+am+"</i><br>";
            }
        }
    }
    if(amount!=0){amount = "Amount sum: <i>"+amount+"</i> <b>Accounting sum: "}else{amount="<b>Accounting sum: "}
    html += amount + sum.toFixed(2)+"</b>";
    $("#summary").html(html);
    return false;
}




/* <button id="loading-modal-demo" class="mdl-button mdl-js-button mdl-button--raised mdl-js-ripple-effect mdl-button--accent">

$('#loading-modal-demo').click(function () {
        showLoading();
        setTimeout(function () {
            hideLoading();
        }, 2500);
    }); */

var RTF_SUBMIT = false;

function saveRTF(id, action) {
    // alert(JSON.stringify(QUILL.getContents()));

    //Strip amount to show plain number.
       var am = $("#am").val().trim();
           am = am.replace(/[^\d\.]/g,"");
       $("#am").val(am);

    var is_submit = (id==-1);
    if (id < 1) {
        id = $("#submit_is_edit").val();        
    }


    
    if(is_submit && (EDIT_LOG_TXT && $('#el').val() !== EDIT_LOG_TXT)){

        if(formValidation()){ //If it is false, failed. That needs to altered by the user first.

            $('<div></div>').dialog({
                modal: true,
                title: "You are Editing an Previous Log Entry",
                width: "40%",
                show: { effect: "clip", duration: 500 },
                hide: { effect: "fold", duration: 1500},
                open: function() {
                    var sel = $("#bck input[type=radio]:checked").val();
                    $(this).html('<div>Are you sure you want to submit your edit?</div><div>To make a copy of the current whole entry. '+
                    'Click on the No button, and then on Now button on the form.</div>');
                },
                buttons: [

                    { text: "Yes",                    
                      icons: { primary: "ui-icon-circle-check" },
                        click: function() {                            
                            $( this ).dialog( "close" );
                            $("#frm_entry").submit();
                        }
                    },
        
                    { text: "No",
                        click: function() {
                            decodeText();
                            $( this ).dialog( "close" );                        
                            return false;
                        }
                    }
                ]
            });

        }
        return false;
    }
    else
    if(is_submit && !$("#RTF").prop('checked')){           
       return true;//we submit normal log entry
    }
    RTF_SUBMIT = true;
    var bg = $("#fldBG").val();
    $.post('json.cgi', {action:'store', id:id, bg:bg, doc: JSON.stringify(
            QUILL.getContents())},saveRTFResult).fail(
                 function(response) {
                     dialogModal("Service Error: "+response.status,response.responseText);
                }
                                                 );
    if(is_submit){        
        $("#idx_cat").value = "SAVING DOCUMENT...";
        $("#idx_cat").show();
        //we must wait before submitting actual form!
        setTimeout(delayedSubmit, 200);
    }
    return false;
}

function saveRTFResult(result) {    
    //console.log("Result->" + result);
    var json = JSON.parse(result);    
    $("html, body").animate({ scrollTop: 0 }, "fast");
    
    let msg = json.response;
    if(json.log_id==0){
        console.log(msg = "Saved to Buffer");  

    }else{
        console.log(msg = "Saved document by lid -> "+json.log_id);        
    }
    display(msg, 5);

    if(json.log_id>0){
        //update under log display
        if($("#q-rtf"+json.log_id).is(":visible")){
            loadRTF(true, json.log_id);
        }
    }else{
        $('#btn_zero_doc').show();
    }
    RTF_SUBMIT = false;
}

function delayedSubmit(){
    if(RTF_SUBMIT){
        setTimeout(delayedSubmit, 200);
        return;
    }
    $("#frm_entry").submit();
}

function dispFullLog(id){
    let $log = $("#h"+id).val();
    $("#v"+id).html('<div class="log">'+$log+'</div>');
    return false;
}


function loadRTF(under, id){

    //show under log entry the document
    if(under){

        if($("#q-rtf"+id).is(":visible")){
            $("#q-rtf"+id).hide();
            return false;
        }
        QUILL_PNL = new Quill('#q-container'+id, {
            scrollingContainer: '#q-scroll'+id,
            placeholder: 'Loading Document...',
            readOnly: true,
            //theme: 'bubble'
          });
          //console.log("Panel query json.cgi action -> load, id:" + id);
          $.post('json.cgi', {action:'load', id:id}, loadRTFPnlResult);
          $("#q-rtf"+id).show();
          display("Load id -> " + id + " issued!", 1);
        return false;
    }else{
        $("#rtf_doc").show();
        $("#el").focus();
    }

    if(id==-1){
       id = RTF_DOC_CUR_ID; // btn_load_rtf clicked
    }

    QUILL.setText('Loading Document...\n');    
    $.post('json.cgi', {action:'load', id:id}, loadRTFResult).fail(
           function(response) {dialogModal("Service Error: "+response.status,response.responseText);}
    );

    $("#rtf_doc").show();
    $('#tbl_doc').show();
    $('#toolbar-container').show();

    return false;
}

function loadRTFPnlResult(content, result, prms) {
    loadRTFResult(content, result, prms, QUILL_PNL);
}

function loadRTFResult(content, result, prms, quill) {
    console.log(content);
    var json = JSON.parse(content);
    if(!quill)quill=QUILL;

    $('#fldbg').val(json.content.bg);
       quill.setContents(json.content.doc);
    if(quill===QUILL){
        $("#fldBG").val(json.content.bg);
        editorBackground(false);
    }
    else{
        var id = json.log_id;
        var cls = $("#q-scroll"+id).parent().parent().attr("class");
       // alert(css);
        $("#q-scroll"+id).attr('class',cls);
        var css = $("#q-scroll"+id).prop('style');
        $("#q-scroll"+id).attr('class',cls);
        if(css){
            css.backgroundColor = DEF_BACKGROUND; //Removing colours makes it inherit from parent these properties.
            css.foregroundColor = "";//json.content.fg;            
        }
    }

    let msg = json.response;
    if(json.error){
        dialogModal("Service Error", json.error);
    }
    if(json.log_id==0){
        console.log(msg = "Loaded in Buffer");
        $('#btn_zero_doc').show();                
    }else{
        console.log(msg = "Loaded in document by lid -> "+json.log_id);
        $('#btn_load_doc').show();
    }
    display(msg, 3);    
}




function editorBackground(reset){
    var css = $("#editor-container").prop('style');
    if(reset){
        css.foregroundColor = black;
        css.backgroundColor = DEF_BACKGROUND;
        $("#fldBG").val(DEF_BACKGROUND);
    }
    else{
        css.foregroundColor = black;
        css.backgroundColor = $("#fldBG").val();
    }
}


function RGBToHex(rgb) {
    // Choose correct separator
    var sep = rgb.indexOf(",") > -1 ? "," : " ";
    // Turn "rgb(r,g,b)" into [r,g,b]
    rgb = rgb.substr(4).split(")")[0].split(sep);

    var r = (+rgb[0]).toString(16),
        g = (+rgb[1]).toString(16),
        b = (+rgb[2]).toString(16);

    if (r.length == 1)  r = "0" + r;
    if (g.length == 1)  g = "0" + g;
    if (b.length == 1)  b = "0" + b;

    return "#" + r + g + b;
}

function fetchBackup() {    
    window.location = "config.cgi?bck=1";    
    setTimeout("location.reload(true);", 5000);
}
function deleteBackup() {
    $('<div></div>').dialog({
        modal: true,
        title: "Please Confirm?",
        width: "40%",
        show: { effect: "clip", duration: 1000 },
        hide: { effect: "explode", duration: 1000},
        open: function() {
            var sel = $("#frm_bck input[type=radio]:checked").val();
          $(this).html("Are you sure you want to delete file:<br><b>"+sel+"</b>");
        },
        buttons: [
             {  text: "Yes",
                icon: "ui-icon-trash",
                click: function() {
                  $( this ).dialog( "close" );
                    var sel = $( "#frm_bck input[type=radio]:checked").val();
                    window.location = "config.cgi?bck_del="+sel+"#backup";
                }
              },

            { text: "No",
                click: function() { $( this ).dialog( "close" );
                return false;
                }
            }
        ]
    });
}


function setPageSessionTimer(expires) {

    var timeout;
    var now = new moment();
    var val = expires.replace(/\+|[A-Z]|[a-z]/g, '');
    
    if(expires.indexOf("h")>0){
        timeout = moment(now).add(val, "h");
    }
    else
    if(expires.indexOf("m")>0){
        if(val<2){val=2};
        timeout = moment(now).add(val, "m");
    }
    else
    if(expires.indexOf("s")>0){
        if(val<60){val=2}; 
        timeout = moment(now).add(val, "s");
    }
    else{
        if(val<2){val=2};
        timeout = moment(now).add(val, "m");
    }
    var WARNED =0;
    var timer   =  setInterval(function() {
            var now = new moment();
            var dif = timeout.diff(now);
            var min = Math.floor(dif / 60000);
            var sec = ((dif % 60000) / 1000).toFixed(0);
            var out = (min < 10 ? '0' : '') + min + ":" + (sec < 10 ? '0' : '') + sec;
            var tim = new moment().tz(TIMEZONE).format("hh:mm:ss a");
            var sty = "";if(min<2){sty="style='color:red'";
            if(!WARNED){WARNED=1;
                if($('#auto_logoff').val()=='0'){
                   $('#au_door_chime').trigger('play');
                }else{
                    $('#btnLogout').click();
                }
                display("<span id='sss_expired'>Session is about to expire!</span>",10);}
            }
            var dsp = "<font size='1px;'>[" + tim + "]</font><span "+sty+"> Session expires in " + out + "</span>";                
            $("#sss_status").html(dsp);
            if(now.isAfter(timeout)){
                $("#sss_status").html("<span id='sss_expired'><a href='login_ctr.cgi'>Page Session has Expired!</a></span>");
                clearInterval(timer);
                $("#ed").prop( "disabled", true );
                $("#el").prop( "disabled", true );
                $("#am").prop( "disabled", true );
                if($('#auto_logoff').val()=='1'){                    
                      dialogModal("Page Session has Expired","Please login again!", true);                    
                }
            }

        }, 1000);
	}

 function  checkConfigCatsChange(){
     var e1 = $('#frm_config input[name="caid"]').val();
     var e2 = $('#frm_config input[name="canm"]').val();
     if(e1.length>0 && e2.length>0){
     return dialogModal("Sorry Categories Config Validation Failed",
                        "Did you fail to clear or add a new category first? ->" + e2);
     }
     return true;
 }

 function dialogModal(title, message, logout) {
    
    if(logout) {
        $('<div></div>').dialog({
            modal: true,
            title: title,
            width: "40%",
            show: { effect: "clip", duration: 400 },
            open: function() {
            $(this).html(message);
            },
            buttons: {
                Logout: function() {
                    $( this ).dialog( "close" );
                    location.reload();
                }
            }    
        });
    }else {      
    
            $('<div></div>').dialog({
                modal: true,
                title: title,
                width: "40%",
                show: { effect: "clip", duration: 400 },
                open: function() {
                $(this).html(message);
                },
                buttons: {
                    Ok: function() {
                    $( this ).dialog( "close" );
                    }
                }
            });
    }
return false;
 }

