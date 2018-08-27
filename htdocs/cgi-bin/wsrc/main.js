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
	date.value = dt.getFullYear()+"-"+dt.getMonth()+"-"+dt.getUTCDate() + " " + dt.getHours() + ":" dt.getMinutes() +":"+dt.getSeconds();

return false;
}
