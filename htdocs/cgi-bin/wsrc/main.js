function loadedBody(toggle){
	document.getElementById("frm_log").log.focus();
	if(toggle){
		toggleSearch(document.getElementById("btn_srch"));
	}
}

function formValidation(){
  
var date = document.getElementById("frm_log").date;
var log  = document.getElementById("frm_log").log;

return validDate(date.value) && validLog(log.value);

}

function validDate(dt){
	if(!Date.parse(dt)){
		alert("Date -> '" + dt +"' is Invalid can't submit!");
		return false;
	}
return true;
}

function validLog(log){
	if(log==""){

		alert("Log -> entry can't be empty, can't submit!");
		return false;
	}
return true;
}


function setNow(){

	var date = document.getElementById("frm_log").date;
	var dt = new Date();
	date.value = dt.getFullYear()+"-"+(dt.getMonth()+1)+"-"+dt.getUTCDate() + " " + dt.getHours() + ":" + dt.getMinutes() +":"+dt.getSeconds();

return false;
}

function edit(row){

	var ec_v = document.getElementById("c"+ row).innerText;
	var ec   = document.getElementById("ec");

	var ed_v = document.getElementById("y"+ row); 
	var et_v   = document.getElementById("t"+ row); 
	var ev_v = document.getElementById("v"+ row); 

	
	document.getElementById("el").value = ev_v.innerText;
	document.getElementById("ed").value = ed_v.innerText + " " +  et_v.innerText;

	for(var i = 0, j = ec.options.length; i < j; ++i) {
	        if(ec.options[i].innerHTML === ec_v) {
			           ec.selectedIndex = i;
				   break;
	         }
	}
	document.getElementById("submit_is_edit").value = row;
	document.getElementById("frm_log").log.focus();

return false;
}

function submitNext(tbl_rc){

	var frm = document.getElementById("frm_log");
	    frm.submit_is_view.value = 1;
	    frm.rs_all.value = 0;
	    frm.rs_cur.value = tbl_rc;
	    frm.submit_is_view.value = 1;
	    frm.submit();

	return false;
}

function submitPrev(tbl_rc){

	var frm = document.getElementById("frm_log");
	    frm.submit_is_view.value = 1;
	    frm.rs_all.value = 0;
	    frm.rs_cur.value = tbl_rc;
	    frm.rs_prev.value = tbl_rc;
	    frm.submit_is_view.value = 1;
	    frm.submit();

	return false;
}

function viewAll(){

	var frm = document.getElementById("frm_log");
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
	    if (d.style.display === "none" || d.style.display ==="") {
		  d.style.display = "block";
		  btn.innerText="Hide Search";
	   } else {
	          d.style.display = "none";
		  btn.innerText="Show Search";
	   }
}

function resetView(){
		
	    var f = document.getElementById("frm_srch");
	    f.keywords.value = "";
}
