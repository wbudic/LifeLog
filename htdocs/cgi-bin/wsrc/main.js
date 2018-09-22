function loadedBody(){
	document.frm_log.log.focus();
}

function formValidation(){
  
var date = document.frm_log.date;
var log  = document.frm_log.log;

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

	var date = document.frm_log.date;
	var dt = new Date();
	date.value = dt.getFullYear()+"-"+dt.getMonth()+"-"+dt.getUTCDate() + " " + dt.getHours() + ":" + dt.getMinutes() +":"+dt.getSeconds();

return false;
}

function edit(el){
	var row = el.nextSibling.value;

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

return false;
}
