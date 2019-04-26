/*
 Programed in vim by: Will Budic
 Open Source License -> https://choosealicense.com/licenses/isc/
*/

function loadedBody(toggle) {
    var el = document.getElementById("frm_entry");
    el.log.focus();
    if (toggle) {
        toggleSearch(document.getElementById("btn_srch"));
    }

    document.getElementById("log_submit").addEventListener("click", encodeText);
}

function encodeText(el) {
    var el = document.getElementById("frm_entry");
    var txt = el.log.value;
    txt = txt.replace(/\r\n/g, "\\n");
    txt = txt.replace(/\n/g, "\\n");
    el.log.value = txt;
}


function formValidation() {

    var date = document.getElementById("frm_entry").date;
    var log = document.getElementById("frm_entry").log;
    var cat = document.getElementById("frm_entry").cat;
    if (cat.value == 0) {
        alert("Category -> has not been selected!");
        return false;
    }

    return validDate(date.value) && validLog(log.value);

}

function validDate(dt) {
    if (!Date.parse(dt)) {
        alert("Date -> '" + dt + "' is Invalid can't submit!");
        return false;
    }
    return true;
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
    return false;
}

function fix0(v) {
    if (v < 10) {
        return "0" + v;
    }
    return v;
}

function edit(row) {

    var ec_v = document.getElementById("c" + row).innerText;
    var ec = document.getElementById("ec");

    var ed_v = document.getElementById("y" + row);
    var et_v = document.getElementById("t" + row);
    var ev_v = document.getElementById("v" + row);
    var ea_v = document.getElementById("a" + row);
    var etag = document.getElementById("tag" + row);
    if (etag) {
        var v = etag.value;
        v = v.replace(/\\n/g, '\n');
        document.getElementById("el").value = v;
    } else {
        document.getElementById("el").value = ev_v.innerText;
    }
    document.getElementById("ed").value = ed_v.value + " " + et_v.innerText;
    document.getElementById("am").value = ea_v.innerText;
    //Change selected catergory
    for (var i = 0, j = ec.options.length; i < j; ++i) {
        if (ec.options[i].innerHTML === ec_v) {
            ec.selectedIndex = i;
            break;
        }
    }
    document.getElementById("submit_is_edit").value = row;
    document.getElementById("frm_entry").log.focus();

    return false;
}



function selectAllLogs() {
    var frm = document.getElementById("frm_log");
    var chks = document.getElementsByName("chk");
    for (var i = 0, n = chks.length; i < n; i++) {
        chks[i].checked = true;
    }
    return false;
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


function toggleSearch(btn) {

    var d = document.getElementById("div_srh");
    if (d.style.display === "none" || d.style.display === "") {
        d.style.display = "block";
        btn.innerText = "Hide Search";
    } else {
        d.style.display = "none";
        btn.innerText = "Show Search";
    }
}

function resetView() {

    var f = document.getElementById("frm_srch");
    f.keywords.value = "";
}

function updateSelCategory(sel) {
    //disabled as Search View has own dreopdown since v.1.3	 
    //    var b = document.getElementById("btn_cat");
    var cat = document.getElementById("idx_cat");
    cat.value = sel.options[sel.selectedIndex].value;
    //    b.innerText = sel.options[sel.selectedIndex].text;

    //    document.getElementById("ctmsg").style.display = "none";    
}

function viewByCategory(btn) {

    document.getElementById("rs_keys").value = "";
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