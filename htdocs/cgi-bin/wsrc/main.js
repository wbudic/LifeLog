/*
 Programed in vim by: Will Budic
 Open Source License -> https://choosealicense.com/licenses/isc/
*/

var _MAP = new Map();
var MNU_SCROLLING = false;
var SRCH_TOGGLE = true;

var QUILL;
var Delta;
var RTF_SET = false;
var CHANGE;

var _collpsd_toggle = false;
var _collpsd_toggle2 = false;


function loadedBody(toggle) {


    if (toggle) {
        toggleSearch($("#btn_srch"));
    }

    $('#ed').datetimepicker({
        dateFormat: 'yy-mm-dd',
        timeFormat: 'HH:mm:ss',
        stepHour: 1,
        stepMinute: 10,
        stepSecond: 10,
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

}



function hideLog() {
    $("#div_log").hide();
    return false;
}

function hideSrch() {
    $("#div_srh").hide();
    return false;
}

function hideDoc() {
    $("#tbl_doc").hide();
    return false;
}

function encodeText(el) {
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
            // 12-hour value between 1 and 12
            if (regs[1] < 1 || regs[1] > 23) {
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
    var tag = $("#g" + row); //orig. tagged log text.
    var log = $("#v" + row); //log
    var rtf = $("#r" + row); //RTF doc
    var isRTF = (rtf.val()>0?true:false);
    if(!isRTF){
            $('#rtf_doc').hide();
            $('#tbl_doc').hide();
            $('#toolbar-container').hide();
    }


    $("html, body").animate({ scrollTop: 0 }, "slow");
    if (tag.length) {
        $("#el").val(decodeToHTMLText(tag.val()));

    } else {    
        $("#el").val(decodeToText(log.text()));
    }      
        
    $("#ed").val(ed_v.val() + " " + et_v.html()); //Time field
    var val = ea_v.html();
    val = val.replace(/\,/g,"");
    $("#am").val(val); //Amount field, fix 04-08-2019 HTML input doesn't accept formated string.
    $("#RTF").prop('checked', isRTF);

    if(isRTF){
        loadRTF(false, row);
    }

    //Select category
    var ec_v = $("#c" + row).text();
    $("#ec option:contains(" + ec_v + ")").prop('selected', true);
    $("#submit_is_edit").val(row);
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
}


function submitNext(tbl_rc) {

    var frm = document.getElementById("frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value = 0;
    frm.rs_cur.value = tbl_rc;
    frm.submit_is_view.value = 1;
    frm.submit();

    return false;
}

function submitPrev(tbl_rc) {

    var frm = document.getElementById("frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value = 0;
    frm.rs_cur.value = tbl_rc;
    frm.rs_prev.value = tbl_rc;
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

var RTF_DOC_RESIZED = false;
var RTF_DOC_ORIG;
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
}


function toggleSearch() {
    $("html, body").animate({ scrollTop: 0 }, "slow");
    if (SRCH_TOGGLE) {
        $("#div_srh").show();
        $("#btn_srch").text("Hide Search");
        SRCH_TOGGLE = false;
    } else {
        $("#div_srh").hide();
        $("#btn_srch").text("Show Search");
        SRCH_TOGGLE = true;
    }
}

function resetView() {
    $("#frm_srch input").val("");    
    $("#idx_cat").val(0);
    $('#vc>option[value="0"]').prop('selected', true);

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



function toggleLog() {
    if (!_collpsd_toggle) {
        $("#div_log .collpsd").hide();
        _collpsd_toggle = true;
    } else {
        $("#div_log .collpsd").show();
        _collpsd_toggle = false;
    }
}

function toggleSrch() {
    if (!_collpsd_toggle2) {
        $("#div_srh .collpsd").hide();
        _collpsd_toggle2 = true;
    } else {
        $("#div_srh .collpsd").show();
        _collpsd_toggle2 = false;
    }
}

function showCat() {
    $('#cat_desc').show();
}

function showAll() {
    $("#menu").show();
    $('#cat_desc').show();
    $("#div_log").show();
    $("#div_srh").show();
    $("#tbl_doc").show();
    _collpsd_toggle = false;
    _collpsd_toggle2 = false;
    $("#btn_srch").text("Hide Search");
    SRCH_TOGGLE = false;
    return false;
}

function helpSelCategory(sel) {
    var pnl = $("#cat_desc");
    var desc = _MAP.get(sel.options[sel.selectedIndex].value);
    if (!desc) {
        desc = "<font color='red'>Please select a Category!</font>";
    }
    pnl.html(desc);
    pnl.show();
    pnl.fadeOut(5000);
}

function viewByCategory(btn) {

    $("#rs_keys").value = "";
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
            var par = chks[i].parentNode.parentNode.childNodes;
            for (var j = 0, nn = par.length; j < nn; j++) {
                var el = par[j];
                if (el.id && el.id.indexOf('a', 0) == 0) {
                    sum = sum + Number(el.innerHTML);
                    break;
                }
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
    $.post('json.cgi', {action:'store', id:id, doc: JSON.stringify(QUILL.getContents())}, saveRTFResult);
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
    alert(obj.response);    
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

        
        var quill = new Quill('#q-container'+id, {
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
          $.post('json.cgi', {action:'load', id:id}, function (result){
                var json = JSON.parse(result);
                 console.log("Panel load result->" + result.toString());                 
                 quill.setContents(json.content);
          });
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

function loadRTFResult(result) {
    console.log("Result->" + result);
    var json = JSON.parse(result);
    QUILL.setContents(json.content);
    //alert(obj.response);
}

function editorBackgroundLighter(){
    alert("Sorry, Feature Under Development!");
}
function editorBackgroundReset(){
    alert("Sorry, Feature Under Development!");
}
function editorBackgroundDarker(){
    alert("Sorry, Feature Under Development!");
}