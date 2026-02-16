
button0.onmouseover = function () {

	menuApp.style.display = "block"
}

button0.onmouseout = function () {

	menuApp.style.display = "none"
}





//  document.addEventListener("DOMContentLoaded", function() {


menuApp.addEventListener("mouseenter", function () {
	menuApp.style.display = "block";
});

menuApp.addEventListener("mouseleave", function () {
	menuApp.style.display = "none";
});


//});





const __a1 = function () {
	dmenu('regInf', 'dispApp')
	ajax({
		datas: "nodata",
		method: "POST",
		location: "/engines/rusr.php",
		id: "regInf",
		eval: false,
		handler: "UNIKH",
		block: true,
		method: "POST"
	});
}



/*enlace id  a1*/
/* Enlaza a div id regInf class disApp*/

a1.onclick = function () {
	__a1()
}

a1.innerHTML = ` usr / Login`
a1.className = "lmenu"







//a4 Directorio

a4.innerHTML = "Directorio"

a4.className = "lmenu"


a4.onclick = function () {

	if (Directorio.src == "about:blank") {
		Directorio.src = "app/freedirectory/index.php"
	}

	dmenu('Directorio', 'dispApp')


}



a5.innerHTML = "miTv"

a5.className = "lmenu"


a5.onclick = function () {

	if (miTv.src == "about:blank") {
		miTv.src = "app/mitv"
	}

	dmenu('miTv', 'dispApp')


}




a6.innerHTML = "Datas Info"

a6.className = "lmenu"


a6.onclick = function () {

	if (datasInfo.src == "about:blank") {
		datasInfo.src = "ws://" + window.location.hostname + ":8081"
	}

	dmenu('datasInfo', 'dispApp')


}



a7.innerHTML = "JsAnimator"
a7.className = "lmenu"
a7.onclick = function () {
	if (JSA.src == "about:blank") {
		JSA.src = "https://" + window.location.hostname + "/app/jsa"
	}
	dmenu('JSA', 'dispApp')
}





a8.innerHTML = "C21 Editor"
a8.className = "lmenu"


a8.onclick = function () {

	if (EDITORc21.src == "about:blank") {
		EDITORc21.src = "https://compostela21.com/varios/datas/adm/"
	}
	EDITORc21.sandbox = "allow-scripts allow-same-origin allow-forms allow-modals allow-popups allow-iframes"
	dmenu('EDITORc21', 'dispApp')


}

function n_menu(obj) {
	obj.id.innerHTML = obj.innerHTML
	obj.id.className = obj.className
	obj.id.onclick = function () {
		if (obj.bind.src == "about:blank") {
			obj.bind.src = obj.location
		}
		dmenu(obj.name, 'dispApp')
	}
}


n_menu({
	id: a9,
	bind: DOC,
	name: "DOC",
	location: "https://" + window.location.hostname + "/img/tmp",
	innerHTML: "Temporales",
	className: "lmenu"
})

n_menu({
	id: a10,
	bind: WEBIRC,
	name: "WEBIRC",
	location: "https://" + window.location.hostname + "/app/widgets/webirc.html",
	innerHTML: "WebIRC",
	className: "lmenu"
})

n_menu({
	id: a11,
	bind: DOCS,
	name: "DOCS",
	location: "https://" + window.location.hostname + "/documentation/index.php",
	innerHTML: "Documentación",
	className: "lmenu"
})




a12.innerHTML = "GoyimZ"
a12.className = "lmenu"
a12.onclick = function () {
	if (GOYIMZ.src == "about:blank") {
		GOYIMZ.src = "https://" + window.location.hostname + "/app/goyimz/index.goy"
	}
	dmenu('GOYIMZ', 'dispApp')
}












/* Estilos*/

addStyle(`

.lmenu{
    background:#181324;display:block;
    padding:5px;margin-right:8px;margin-bottom:7px;
	color:#e4dece;
	font-size:1.9vh;
	width:100%;border:solid 0px #ceaddc;cursor:pointer;

}

.dispApp{


border:0;
top:5vh;
z-index:77;left:10vw;
position:fixed;
height:95vh;width:90vw;
font-size:1.9vh;overflow-y:auto;
	
	background:white;
}

	`, `cssstyleadd1`);













