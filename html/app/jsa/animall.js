//alert("Ventana Activa:"+eval('parent.'+parent.ActiveWinName+'').document.body.outerHTML+"<br>")


var confSound = ""
Doc = "html"




var HTML = function(){
HTML = document.createElement(Doc)
HTML.id = 100000011001110
HTML.document = HTML.ownerDocument
HTML.ownerDocument.id = HTML.id
this.node = HTML.id
return HTML
}


var BODY = function(HTML=CLONE){
const BODY = document.createElement("body")
HTML.append(BODY)
document.body = BODY
return   BODY
}

HTML = HTML()

nb=0




const Active = function(aBODY){
BODY = aBODY
document.body = BODY;
return BODY
}



someAnim = false

msid = new Array();
md = new Array()
v =new Array()
code = ""
acode = ""
f=0
constn = 0;
elements = new Array();

jscode = ""


end = 0;




for(ik=0;ik<opener.ad.length;ik++){ //leemos todos los objetos a&ntilde;adidos a la ventana
/*defecto animacion */

animationDuration = "10s"
animationDelay = "0s"
animationIterationCount = "1"
animationFillMode = "forwards";

translength = 0;


if(opener.ad[ik].win != parent.ActiveWinName)  continue //anima solo ventana activa

if(opener.ad[ik].id=='erased' && opener.ad[ik].tag!='body') continue // salta tags eliminados


if(id = opener.ad[ik].id) {  //id es el id del objeto (tag) - existe objeto con su id


/*Valores para animación (ultimo valor dado al elemento) */

if(opener.ad[ik].style.animationDuration) animationDuration = opener.ad[ik].style.animationDuration
else opener.ad[ik].style.animationDuration = animationDuration
if(opener.ad[ik].style.animationDelay) animationDelay = opener.ad[ik].style.animationDelay
else opener.ad[ik].style.animationDelay = animationDelay 
if(opener.ad[ik].style.animationIterationCount) animationIterationCount = opener.ad[ik].style.animationIterationCount
else opener.ad[ik].style.animationIterationCount = animationIterationCount
if(opener.ad[ik].style.animationFillMode) animationFillMode = opener.ad[ik].style.animationFillMode
else opener.ad[ik].style.animationFillMode = animationFillMode

if(!opener.ad[id].animacionCollection) {


//ELEMENTOS SIN TRANSICIONES
//document.write("<br>Elemento sin colecion animacion: "+opener.ad[id])


//code = getCode(opener.ad[id],'unique',id)

//alert(code)

//continue


} else if(translength = opener.ad[id].animacionCollection.length) {


someAnim = true


code += getCode(opener.ad[id].animacionCollection,translength,id,opener.ad[id].tag)




//alert(opener.ad[ik].tag)


if(opener.ad[ik].tag == "body"){

bodyDoc = BODY(HTML)


bodyDoc.id = opener.ad[ik].tag+"_"+opener.ad[ik].id


//deshabilitado propiedades para body
//jscode += readObj(opener.ad[ik],'propertiers',opener.ad[ik].id,opener.ad[ik].tag)


if(this.name =='AnimeWin') bodyDoc.style = "position:absolute;margin:0;width:100%;height:100%;margin:0;overflow:auto"




continue



} else {
msid[constn] = document.createElement(opener.ad[ik].tag);
msid[constn].id = opener.ad[ik].tag+"_"+opener.ad[ik].id
msid[constn].tag = opener.ad[ik].tag
if(opener.ad[ik].className) cnm = opener.ad[ik].className
else cnm = opener.ad[ik].tag
msid[constn].className = cnm
/*damos estilos de inicio*/


constn++
}



}


if(translength) {


jscode += readObj(opener.CONTROLS.propertiers,'propertiers',opener.ad[ik].id,opener.ad[ik].tag)

}

} else {  /* Objeto vacio (array) */   }




/*FIN for 1*/

}







function getCode(objX,mkType,id,tag){




//document.write("<br>Elemento con colecion animacion: "+opener.ad[id])
//document.write("<br>longitud: "+mkType)
//document.write(" AnimacionCollection:"+objX+"<br>")




switch(mkType){
case 'unique':
return ''
break;
default:
translength = mkType
break;
}



initval = ""
keyframe = "     @keyframes "+tag+"_"+id+"{\n"
a1=0
objlen = translength
ftg = 0
code = ''
da = ''
loop = 0

for(keyint of objX){



for(propertier in keyint) {






obj = eval('keyint.'+propertier+'') // obtenemos valores grabados en el objeto animacionCollection

if(propertier == 'styles'){  

mx = '.style.';


da=0





//time = value.match(/[0-9\.]{1,}(ms|s)/gi, '')



if(a1 == 0){



 initval = readObj(obj,propertier);
// keyframe += "\n0%{"+readObj(obj,propertier)+"}\n" 


 } /* else if((1+a1)!=objlen) {
 
 kt = ((((a1+1)*100)/objlen))



 keyframe += "\n"+(kt.toFixed(3))+"% {"+readObj(obj,propertier)+"}\n" 

 ftg++
 
 }  else {


keyframe += "\n100%{"+readObj(obj,propertier)+"}\n" 




 
}

*/


 if(a1<objlen) {
 
 kt = ((((a1)*100)/(objlen-1)))

 if(isNaN(kt)) kt = 100

 keyframe += "\n"+(kt.toFixed(3))+"% {"+readObj(obj,propertier)+"}\n" 

 ftg++
 
 } 


 a1++
 

 } else if(propertier=='propertiers') {


mx = '.';



//  disable collection propertiers js code 
// jscode += readObj(obj,propertier,id)
 
 
 
 } 
 


}


}


return keyframe+`\n} #`+tag+`_`+id+` { `+initval+`  animation-iteration-count:`+animationIterationCount+`; animation-duration: `+animationDuration+`;  animation-fill-mode: `+animationFillMode+`; animation-delay:`+animationDelay+`; animation-name: `+tag+`_`+id+`; } `


}





if(!someAnim){
document.write("<h2>No hay elementos con transiciones grabadas para la Pesta&ntilde;a "+taskN+"</h2>")
}




function readObj(obj,prop,id,tag){





var ret = ""

for([key,value] of Object.entries(obj)){

console.log(key+":"+value)

if(prop=='styles') {
if(key == 'animation') continue
else if(key == 'animationDuration') continue
else if(key == 'animationIterationCount') continue
else if(key == 'animationDirection') continue
else if(key == 'animationFillMode') continue
else if(key == 'animationName') continue
else if(key == 'animationDelay') continue
else if(key == 'animationPlayState') continue
else if(key == 'animationTimingFunction') continue
else if(key == 'transition') continue
ret += ''+translatecss(key)+':'+value+';'
}
else if(prop=='propertiers'){ 
if(key == 'animacion') continue
if(key == 'id') continue

value = eval('opener.ad[id].'+key+'')

if(!value) continue

if(tag == 'video' || tag == 'audio'){

if(key == 'autoplay'){


confSound += 'document.getElementById("'+tag+'_'+id+'").muted=false;document.getElementById("'+tag+'_'+id+'").autoplay=true;document.getElementById("'+tag+'_'+id+'").play();'}
}

ret += 'document.getElementById("'+tag+'_'+id+'").'+key+'= unescape(`'+escape(value)+'`);'

}



}


return ret

}






function translatecss(key){


dic = {

animationDuration:"animation-duration",
animationDirection:"animation-direction",
animationFillMode:"animation-fill-mode",
animationName:"animation-name",
animationDelay:"animation-delay",
animationIterationCount:"animation-iteration-count",
animationPlayState:"animation-play-state",
animationTimingFunction:"animation-timing-function",

backgroundColor:"background-color",
backgroundImage:"background-image",


borderColor:"border-color",
borderStyle:"border-style",
borderWidth:"border-width",


clipPath:"clip-path",

fontFace:"font-face",
fontSize:"font-size",
fontWeight:"font-weight",
fontFamily:"font-family",

letterSpacing:"letter-spacing",


marginBottom:"margin-bottom",
marginLeft:"margin-left",
marginTop:"margin-top",
marginRight:"margin-right",


paddingBottom:"padding-bottom",
paddingLeft:"padding-left",
paddingTop:"padding-top",
paddingRight:"padding-right",


transformStyle:"transform-style",
transformOrigin:"transform-origin",


textAlign:"text-align",

textDecoration:"text-decoration",
textIndent:"text-indent",
wordSpacing:"word-spacing",

zIndex:"z-index"

}


val = eval('dic.'+key+'')

if(val) ret = val
else ret = key


return ret

}


























//code = acode



if(confSound) {



mascode1 = `\n\n\
\nfunction actsv(){\n\
`+confSound+`\n\
}\n\
\n\
\n\
`


mxhtml = ``

//mxhtml = `\ndocument.body.innerHTML += \`<div style='background:#a0d0b0;color:#e554d5;font-weight:bold;z-index:9999999;padding:5px;position:fixed;top:0;left:0;text-align:center;font-weight:bold;font-family:arial;line-height:20px;' id='fgtht1221'><a href='javascript:void(0);' onclick='`+mascode1+`;actsv();document.getElementById("fgtht1221").remove()' style="color:#e554d5;"> [Archivo con audio/vídeo] <br> ACTIVAR</a></div>\`;`



} else {mascode1 = "";mxhtml=""}


HTMLSource= eval('opener.'+opener.ActiveWinName+'.document.body.outerHTML')



codecss = "<style type='text/css'>"+code+"</style>"
codejs = mxhtml+jscode








v = new Array()

onload = function(){



for(i=0;i<constn;i++){


if(msid[i].tag!="body") {document.body.append(msid[i])}

v[i] = document.getElementById(msid[i].tag+"_"+msid[i].id)

//HTML.append(doc)
//HTML.doc


}

//alert(document.body.id)

//alert(jscode)
//document.write("<hr>")





injectx = `<!DOCTYPE html><html><head><meta charset="utf-8">`+codecss+`<script type="text/javascript">onload=function(){`+codejs+`}</script></head>\
`+document.body.outerHTML+`\
</html>\
\
`


opener.injectx = injectx

document.body.innerHTML += codecss


opener.AnimeWinOpt.innerHTML = "Animando Pesta&ntilde;a  "+taskN

opener.AnimeWinOpt.innerHTML += "<a href='javascript:void(0)' onclick='\
\
copen = open(\"about:blank\",\"copen\",\"width=555,height=666\");\n\
copen.document.write(\"<div><textarea style=width:100%;height:80px;>\"+unescape(escape(injectx))+\"</textarea></div>\"+unescape(escape(injectx)));\n\
copen.document.close();\n\
copen.focus();\n\
' style='background:rgba(255,25,255,1);filter:hue-rotate(0deg);position:relative;top:0px;right:0;z-index:9999999999999999'>SourcE</a><div id='svr' style='float:right;position:relative;z-index:9999999;display:inline-block'> <button onclick=\"savename=prompt('Guardar Como... .html',''); ajax('savename='+encodeURIComponent(savename)+'&code='+encodeURIComponent(injectx),'svr','scode.php','POST') \">save as HTML</button></div>  "


eval(''+codejs+'')



}













const objDiff = function(objPrev,objNext){



for(key in objNext){

console.log(key)

}






}


