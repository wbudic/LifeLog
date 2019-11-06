/*
 Programed by: Will Budic
 Open Source License -> https://choosealicense.com/licenses/isc/
*/

var _MAP = new Map();
var MNU_SCROLLING = false;

var QUILL, QUILL_PNL;
var Delta;
var RTF_SET = false;
var CHANGE;

var _show_all = true;

var DEF_BACKGROUND = 'white';

var RTF_DOC_RESIZED = false;
var RTF_DOC_ORIG;


function loadedBody(toggle, rs_cur) {



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
        content: "This is the log entry, can't be left empty.",
        className: 'tip-yellowsimple',
        showOn: 'focus',
        alignTo: 'target',
        alignX: 'left',
        alignY: 'center',
        offsetX: 5,
        showTimeout: 100
    });
    $('#am').poshytip({
        content: "Symbolic ammount in your local or preferred currency. Can be left empty.",
        className: 'tip-yellowsimple',
        showOn: 'focus',
        alignTo: 'target',
        alignX: 'center',
        alignY: 'bottom',
        offsetX: 5,
        showTimeout: 100
    });


    $("input[type=submit], input[type=reset], .ui-widget-content, button, .a_").button();
    $("#btn_save_doc").button();



    $(window).scroll(function() {
        if (!MNU_SCROLLING) {
            $('#floating_menu').fadeOut(2000, function() {
                $('#floating_menu').show();
                MNU_SCROLLING = false;
            });
            MNU_SCROLLING = true;
        }
    });
    $("#menu_close").poshytip({
        className: 'tip-yellowsimple',
        showOn: 'focus',
        alignX: 'left',
        alignY: 'bottom',
    });

    $("#menu_close").click(function() {
        $("#menu").effect("shake", {}, 1000, function() {
            $("#menu").effect("drop", { direction: "down" }, 1500, function() {
                $("#menu").hide();
            })
        })
    });


    $("#log_submit").click(encodeText);


    var kidz = $("#cat_lst").children();
    for (var i = 0; i < kidz.length; i++) {
        _MAP.set(kidz[i].id, kidz[i].innerHTML);
    }

    $('#ec').show();

    $("#RTF").prop("checked", false);
    // $('#tbl_doc').toggle();
    // $('#toolbar-container').toggle();
    if ($('#editor-container').length) {
        QUILL = new Quill('#editor-container', {
            modules: {
                formula: true,
                syntax: true,
                toolbar: '#toolbar-container'
            },
            placeholder: 'Enter your Document here...',
            theme: 'snow'
        });
        Delta = Quill.import('delta');
        CHANGE = new Delta();
        // toggleDocument();
    }

    var rgb = $('#editor-container').css('background-color');
    if(rgb){
        DEF_BACKGROUND = RGBToHex(rgb);
        $("#fldBG").val(DEF_BACKGROUND);
        var amf = $( "#amf" );//Amount Field Type dropdown
        var ec = $( "#ec" );  //Category dropdown

        $( amf ).selectmenu({style: "dropdown", width:120,
          change: function( event, data ) {
            var evv =ec.val();
            if(ec.val()<2||evv==32||evv==35||data.item.value == 0){
                var sel = null;
                if(data.item.label == "Income"){ sel = 35; }
                else if(data.item.label == "Expense"){sel = 32; }
                else if(data.item.value == 0 && (evv == 35||evv==32)){sel = 1; }
                if(sel){
                    ec.val(sel);
                   // ec.selectmenu("refresh");
                }
            }
          }});
    }
}


function encodeText(el){
    var el = $("#frm_entry [name=log]");
    var txt = el.val();
    txt = txt.replace(/\r\n/g, "\\n");
    txt = txt.replace(/\n/g, "\\n");
    el.val(txt);
}


function formValidation() {
    if ($("#ec option:selected").val() == 0) {
        alert("Category -> has not been selected!");
        return false;
    }
    return validDate($("#frm_entry [name='date']").val()) && validLog($("#frm_entry [name='log']").val());
}

function formDelValidation() {

}


function validDate(dt) {
    if (!Date.parse(dt)) {
        alert("Date -> '" + dt + "' is Invalid can't submit!");
        return false;
    }
    return validTime(dt.substring(dt.indexOf(" ") + 1));
}

function validTime(val) {
    // regular expression to match required time format
    re = /^(\d{2}):(\d{2}):(\d{2})([ap]m)?$/;
    var fld = $("frm_entry").date;
    if (val != '') {
        if (regs = val.match(re)) {
            // 12-hour value between 0 and 24
            if (regs[1] < 0 || regs[1] > 23) {
                alert("Invalid value for hours: " + regs[1]);
                fld.focus();
                return false;
            }
            // minute value between 0 and 59
            if (regs[2] > 59) {
                alert("Invalid value for minutes: " + regs[2]);
                fld.focus();
                return false;
            }
            // seconds value between 0 and 59
            if (regs[3] > 59) {
                alert("Invalid value for seconds: " + regs[2]);
                fld.focus();
                return false;
            }
        } else {
            alert("Invalid time format: " + val);
            fld.focus();
            return false;
        }
        return true;
    }
}

function validLog(log) {
    if (log == "") {
        alert("Log -> entry can't be empty, can't submit!");
        return false;
    }
    return true;
}


function setNow() {

    var date = document.getElementById("frm_entry").date;
    var dt = new Date();
    var mm = fix0(dt.getMonth() + 1);
    var dd = fix0(dt.getDate());
    date.value = dt.getFullYear() + "-" + mm + "-" + dd + " " +
        fix0(dt.getHours()) + ":" + fix0(dt.getMinutes()) + ":" + fix0(dt.getSeconds());
    $("#submit_is_edit").val("0");
    toggleDoc(true);    
    return false;
}

function fix0(v) {
    if (v < 10) {
        return "0" + v;
    }
    return v;
}


function decodeToHTMLText(txt) {

    txt = txt.replace("/&#60;/g", "<");
    txt = txt.replace("/&#62;/g", ">");
    txt = txt.replace("/&#9;/g", "\t");
    txt = txt.replace(/&#10;/g, "\n");
    txt = txt.replace(/\\n/g, "\n");
    txt = txt.replace(/&#34;/g, "\"");
    txt = txt.replace(/&#39;/g, "'");
    txt = txt.replace(/br\s*[\/]?>/gi, "\n");

    return txt;
}

function decodeToText(txt) {
    txt = txt.replace(/`RTF$/, "");
    txt = txt.replace(/<br\s*[\/]?>/gi, "\n");
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
    if(!isRTF){
            $('#rtf_doc').hide();
            $('#tbl_doc').hide();
            $('#toolbar-container').hide();
    }


    $("html, body").animate({ scrollTop: 0 }, "slow");
    if (tag.length) {
        $("#el").val(decodeToHTMLText(tag.val()));

    } else {
        var txt = log.html();
        txt = txt.replace(/<br>/g,"\n");
        $("#el").val(decodeToText(txt));
    }

    $("#ed").val(ed_v.val() + " " + et_v.html()); //Time field
    var val = ea_v.text();
    val = val.replace(/\,/g,"");
    $("#am").val(val); //Amount field, fix 04-08-2019 HTML input doesn't accept formated string.
    $("#RTF").prop('checked', isRTF);
    $("#STICKY").prop('checked', isSticky);

    if(isRTF){
        loadRTF(false, row);
    }

    //Select category
    var ec_v = $("#c" + row).text();
    $("#ec option:contains(" + ec_v + ")").prop('selected', true);
    $("#submit_is_edit").val(row);

    //Amount type
    ec_v = amt.val();
    $("#amf").focus();
    $("#amf").val(ec_v);
    //$("#amf").selectmenu('refresh');

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

function deleteSelected() {
    $("#del_sel").click();
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
    frm.rs_cur.value = tbl_rc;
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

    var frm = document.getElementById("frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value = 1;
    frm.rs_cur.value = 0;
    frm.rs_prev.value = 0;
    frm.submit_is_view.value = 1;
    frm.submit();

    return false;
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
    if (RTF_SET) {
        QUILL.setText("");     
    }
    $("#submit_is_edit").val("0");
    toggleDoc(true);
}



function resetView() {
    $("#frm_srch input").val("");    
    $("#idx_cat").val(0);
    $('#vc>option[value="0"]').prop('selected', true);
    $('#xc>option[value="0"]').prop('selected', true);

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
            $('#toolbar-container').show();
        }
        else{
            $("#rtf_doc").hide();
            $('#tbl_doc').hide();
            $('#toolbar-container').hide();
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
                /* 
                Send partial changes
                $.post('/your-endpoint', { 
                  partial: JSON.stringify(change) 
                });
              
                Send entire document
                $.post('/your-endpoint', { 
                  doc: JSON.stringify(QUILL.getContents())
                });
                */
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
            $(id).toggle();
        }         
        
    }
    else{    
        $(id).toggle();
    }
    
    $("html, body").animate({ scrollTop: 0 }, "fast");
    return false;
}


function showAll() {

   show("#menu");

   if(_show_all){
        $("#lnk_show_all").text("Hide All");
        show('#cat_desc');
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

function helpSelCategory(sel) {
    
    var desc = _MAP.get(sel.options[sel.selectedIndex].value);
    if (!desc) {
        desc = "<font color='red'>Please select a Category!</font>";
    }
    display(desc);
}

function display(desc){
    var pnl = $("#cat_desc");
    pnl.html(desc);
    pnl.show();
    pnl.fadeOut(5000);
}

function viewByCategory(btn) {
    $("#rs_keys").value = "";
    $("#vx").value = "0";
}
function viewExcludeCategory(btn) {
    $("#rs_keys").value = "";
    $("#xc").value = "0";
}

function viewByDate(btn) {
    //	alert(btn.value);
}

function submitNewCategory() {

    var frm = document.getElementById("frm_config");
    var cid = frm.caid;
    frm.cchg.value = cid.value;
    return true;
}

function dateDiffSelected() {
    document.getElementById("datediff").value = 1;
    return true;
}

function sumSelected() {
    var chks = document.getElementsByName("chk");
    var sum = 0;
    for (var i = 0, n = chks.length; i < n; i++) {
        if (chks[i].checked) {
            var id = chks[i].value;
            var am = $("#a"+id).text();
            var ty = $("#c"+id).text();
            am = am.replace(/\,/g,"");//rem formatting
            if(ty=='Expense'){
                sum = sum - Number(am);
            }
            else{
                sum = sum + Number(am);
            }
        }
    }
    $("#summary").html(sum.toFixed(2));
    return false;
}

var RTF_SUBMIT = false;

function saveRTF(id, action) {
    // alert(JSON.stringify(QUILL.getContents()));
    var is_submit = (id==-1);
    if (id < 1) {
        id = $("#submit_is_edit").val(); 
    }
    if(is_submit && !$("#RTF").prop('checked')){
        return true;//we submit normal log entry
    }
    RTF_SUBMIT = true;
    var bg = $("#fldBG").val();
    $.post('json.cgi', {action:'store', id:id, bg:bg, doc: JSON.stringify(QUILL.getContents())}, saveRTFResult);
    if(is_submit){
        //we must wait before submitting actual form!
        $("#idx_cat").value = "SAVING DOCUMENT...";
        $("#idx_cat").show();        
        setTimeout(delayedSubmit, 200);
    }
    return false;    
}

function delayedSubmit(){
    if(RTF_SUBMIT){
        setTimeout(delayedSubmit, 200);
        return;
    }
    $("#frm_entry").submit();
}

function saveRTFResult(result) {
    //alert("Result->" + result);
    console.log("Result->" + result);
    var obj = JSON.parse(result);
    //alert(obj.response);  
    $("html, body").animate({ scrollTop: 0 }, "fast");
    display(obj.response);
    if(obj.log_id>0){
        //update under log display
        if($("#q-rtf"+obj.log_id).is(":visible")){
            loadRTF(true, obj.log_id);
        }
    }
    RTF_SUBMIT = false;
}

function loadRTF(under, id){
    
    //show under log entry the document
    if(under){
        

        if($("#q-rtf"+id).is(":visible")){
            $("#q-rtf"+id).hide();
            return false;
        }

        
        QUILL_PNL = new Quill('#q-container'+id, {
            /*
            modules: {
              toolbar: [
                [{ header: [1, 2, false] }],
                ['bold', 'italic', 'underline'],
                ['image', 'code-block']
              ]
            },*/
            scrollingContainer: '#q-scroll'+id, 
            placeholder: 'Loading Document...',
            readOnly: true,
            //theme: 'bubble'
          });         

          $.post('json.cgi', {action:'load', id:id}, loadRTFPnlResult);
          $("#q-rtf"+id).show();
        return false;
    }
    
    //var json = "[{'insert': 'Loading Document...', 'attributes': { 'bold': true }}, {'insert': '\n'}]";    
    QUILL.setText('Loading Document...\n');
    $.post('json.cgi', {action:'load', id:id}, loadRTFResult);
    $("#rtf_doc").show();
    $('#tbl_doc').show();
    $('#toolbar-container').show();
    
    return false;
}

function loadRTFPnlResult(content, result, prms) {
    loadRTFResult(content, result, prms, QUILL_PNL);
}

function loadRTFResult(content, result, prms, quill) {
    console.log("Result->" + content);
    var json = JSON.parse(content);
    if(!quill)quill=QUILL;

    $('#fldbg').val(json.content.bg);
       quill.setContents(json.content.doc);
    if(quill===QUILL){
        $("#fldBG").val(json.content.bg);
        editorBackground(false);
    }
    else{
        var id = json.content.lid;
        var css = $("#q-scroll"+id).prop('style'); 
        css.backgroundColor = json.content.bg
    }
    //alert(obj.response);
}

 


function editorBackground(reset){
    var css = $("#editor-container").prop('style');
    if(reset){
        css.backgroundColor = DEF_BACKGROUND;
        $("#fldBG").val(DEF_BACKGROUND);
    }
    else{css.backgroundColor = $("#fldBG").val();}
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


function exportToCSV(dat, view){
    var csv;
    if(dat == 'cat'){  csv = view ? 4:3;  }
    else
    if(dat == 'log'){  csv = view ? 2:1;  }
    window.location = "config.cgi?csv="+csv;
}

