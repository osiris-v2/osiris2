
button0.onmouseover = function(){

	menuApp.style.display = "block"
}

button0.onmouseout = function(){

	menuApp.style.display = "none"
}





//  document.addEventListener("DOMContentLoaded", function() {
  

  menuApp.addEventListener("mouseenter", function() {
    menuApp.style.display = "block";
  });

  menuApp.addEventListener("mouseleave", function() {
    menuApp.style.display = "none";
  });


//});






/*enlace id  a1*/  
/* Enlaza a div id regInf class disApp*/

a1.onclick = function(){
dmenu('regInf','dispApp')
ajax({
datas:"nodata",
method:"POST",
location:"/engines/rusr.php",
id:"regInf",
eval:false,
handler:"UNIKH",
block:true,
method:"POST"
});
}

a1.innerHTML=` usr / Login`
a1.className = "lmenu"







//a4 Directorio

a4.innerHTML = "Directorio"

a4.className = "lmenu"


a4.onclick = function(){

if(Directorio.src=="about:blank"){
	Directorio.src="app/freedirectory/index.php"
}

dmenu('Directorio','dispApp')


}



a5.innerHTML = "miTv"

a5.className = "lmenu"


a5.onclick = function(){

if(miTv.src=="about:blank"){
	miTv.src="app/mitv"
}

dmenu('miTv','dispApp')


}




a6.innerHTML = "Datas Info"

a6.className = "lmenu"


a6.onclick = function(){

if(datasInfo.src=="about:blank"){
	datasInfo.src="https://"+window.location.hostname+":8081/datas/index.007.html"
}

dmenu('datasInfo','dispApp')


}



a7.innerHTML = "JsAnimator"
a7.className = "lmenu"
a7.onclick = function(){
if(JSA.src=="about:blank"){
	JSA.src="https://"+window.location.hostname+"/app/jsa"
}
dmenu('JSA','dispApp')
}


a8.innerHTML = "C21 Editor"
a8.className = "lmenu"


a8.onclick = function(){

if(EDITORc21.src=="about:blank"){
	EDITORc21.src="https://compostela21.com/varios/datas/adm/"
}
EDITORc21.sandbox="allow-scripts allow-same-origin allow-forms allow-modals allow-popups allow-iframes"
dmenu('EDITORc21','dispApp')


}



a9.innerHTML = "Documentación"
a9.className = "lmenu"
a9.onclick = function(){
if(DOC.src=="about:blank"){
	DOC.src="https://"+window.location.hostname+"/app/freedirectory/web/2"
}
dmenu('DOC','dispApp')
}


a10.innerHTML = "Web IRC"
a10.className = "lmenu"
a10.onclick = function(){
if(WEBIRC.src=="about:blank"){
	WEBIRC.src="https://"+window.location.hostname+"/app/widgets/webirc.html"
}
dmenu('WEBIRC','dispApp')
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

	`,`cssstyleadd1`);














