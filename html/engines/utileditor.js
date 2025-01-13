

function   solicitar_revision (param){
	
confirmz =	confirm("Enviar el artículo a revisión");

if(!confirmz) {

	alert("Cancelado envío a revisión")

} else {

	ajax({
		location:"/engines/jcore.php",
		datas:"edit=article&action=revisar",
		method:"POST",
		eval:true,
		handler:false,
		block:false
	})
}


}





function ext_show_json(xdatas="edit=showjson"){

ajax({
	datas:xdatas,
	location:"/aps/econo/jcore.php",
	id:"showjson",
	method:"POST",
	block:false,
	handler:false,
	eval:false
	});	


}