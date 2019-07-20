/*
 Programed in vim by: Will Budic
 Open Source License -> https://choosealicense.com/licenses/isc/
*/

var _MAP = new Map();
var MNU_SCROLLING = false;
var SRCH_VISIBLE = true;

var QUILL;
var Delta;
var RTF_SET = false;
var CHANGE;

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

function showFloatingMenu() {
    $("#menu").show();
    $("#div_log").toggle();
    return false;
}

function hideLog() {
    $("#div_log").hide();
    return false;
}

function hideSrch() {
    $("#div_srh").hide();
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

    var date = $("#frm_entry").date;
    var dt = new Date();
    var mm = fix0(dt.getMonth() + 1);
    var dd = fix0(dt.getDate());
    date.value = dt.getFullYear() + "-" + mm + "-" + dd + " " +
        fix0(dt.getHours()) + ":" + fix0(dt.getMinutes()) + ":" + fix0(dt.getSeconds());
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
    txt = txt.replace(/<br\s*[\/]?>/gi, "\n");
    return txt;
}

function edit(row) {

    var ed_v = $("#y" + row); //date
    var et_v = $("#t" + row); //time    
    var ea_v = $("#a" + row); //amount
    var tag = $("#g" + row); //orig. tagged log text.
    var log = $("#v" + row); //log
    $("html, body").animate({ scrollTop: 0 }, "slow");
    if (tag.length) {
        $("#el").val(decodeToHTMLText(tag.val()));

    } else {
        $("#el").val(decodeToText(log.text()));
    }
    $("#ed").val(ed_v.val() + " " + et_v.html());
    $("#am").val(ea_v.html());

    //Select category
    var ec_v = $("#c" + row).text();
    $("#ec option:contains(" + ec_v + ")").prop('selected', true);
    $("#submit_is_edit").val(row);
    $("#el").focus();

    return false;
}



function selectAllLogs() {
    var frm = $("#frm_log");
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

    var frm = $("#frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value = 0;
    frm.rs_cur.value = tbl_rc;
    frm.submit_is_view.value = 1;
    frm.submit();

    return false;
}

function submitPrev(tbl_rc) {

    var frm = $("#frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value = 0;
    frm.rs_cur.value = tbl_rc;
    frm.rs_prev.value = tbl_rc;
    frm.submit_is_view.value = 1;
    frm.submit();

    return false;
}

function viewAll() {

    var frm = $("#frm_entry");
    frm.submit_is_view.value = 1;
    frm.rs_all.value = 1;
    frm.rs_cur.value = 0;
    frm.rs_prev.value = 0;
    frm.submit_is_view.value = 1;
    frm.submit();

    return false;
}

function toggleDocument() {
    $('#tbl_doc').toggle();
    $('#toolbar-container').toggle();
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

function saveRTF() {
    if (RTF_SET) {
        $.post('json.pl?m=1', { doc: JSON.stringify(QUILL.getContents()) });
    }
}

function toggleSearch() {
    $("html, body").animate({ scrollTop: 0 }, "slow");
    if (SRCH_VISIBLE) {
        $("#div_srh").show();
        $("#btn_srch").text("Hide Search");
        SRCH_VISIBLE = false;
    } else {
        $("#div_srh").hide();
        $("#btn_srch").text("Show Search");
        SRCH_VISIBLE = true;
    }
}

function resetView() {
    var f = $("#frm_srch");
    f.keywords.value = "";
    $("#idx_cat").value(0);
    $('#vc>option[value="0"]').prop('selected', true);
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
var _collpsd_toggle = false;
var _collpsd_toggle2 = false;

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

    var frm = $("#frm_config");
    var cid = frm.caid;
    frm.cchg.vak(cid.value);
    return true;
}

function dateDiffSelected() {
    $("#datediff").value = 1;
    return true;
}

function saveRTF(id, action) {
    // alert(JSON.stringify(QUILL.getContents()));
    //Disabled on new log entry. Save and edit, obtains id. For now. @2019-07-20
    //if (id > 0) {
    $.post('json.cgi?action=' + action + '&id=' + id, { doc: JSON.stringify(QUILL.getContents()) }, saveRTFResult);
    //}
}

function saveRTFResult(result) {
    alert("Result->" + result);
    console.log(result);
}