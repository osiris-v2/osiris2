



//document.write("Ventana Activa:"+parent.ActiveWinName+"<br>")


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

//alert(IdAnim)



for(ik=0;ik<opener.ad.length;ik++){ //leemos todos los objetos añadidos a la ventana
/*defecto animacion */

animationDuration = "10s"
animationDelay = "0s"
animationIterationCount = "1"
animationFillMode = "forwards";

translength = 0;

if(opener.ad[ik].id != IdAnim)  continue 

if(opener.ad[ik].win != opener.ActiveWinName)  continue //anima solo ventana activa

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

document.write("<h3>No hay transiciones grabadas para,<br>Tag: "+opener.ad[id].tag+"<br>Id: "+IdAnim+"</h3>")

//ELEMENTOS SIN TRANSICIONES
//document.write("<br>Elemento sin colecion animacion: "+opener.ad[id])


//code = getCode(opener.ad[id],'unique',id)

//alert(code)

//continue


} else if(translength = opener.ad[id].animacionCollection.length) {



code += getCode(opener.ad[id].animacionCollection,translength,id,opener.ad[id].tag)




//alert(opener.ad[ik].tag)


if(opener.ad[ik].tag == "body"){



bodyDoc = BODY(HTML)
bodyDoc.id = opener.ad[ik].tag+"_"+opener.ad[ik].id
if(this.name =='AnimeWin') bodyDoc.style = "position:absolute;margin:0;width:100%;height:100%;margin:0;overflow:auto"


continue



} else {
msid[constn] = document.createElement(opener.ad[ik].tag);
msid[constn].id = opener.ad[ik].tag+"_"+opener.ad[ik].id
msid[constn].tag = opener.ad[ik].tag
msid[constn].className = "ID_"+opener.ad[ik].id
/*damos estilos de inicio*/


constn++
}



}


if(translength) {


jscode += readObj(opener.ad[ik].animacionCollection[(translength - 1)].propertiers,'propertiers',opener.ad[ik].id,opener.ad[ik].tag)

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
s = 0
for(keyn in objX){

keyint = objX[keyn]



for(propertier in keyint) {



obj = eval('keyint.'+propertier+'') // obtenemos valores grabados en el objeto animacionCollection

if(propertier == 'styles'){  

mx = '.style.';


time = opener.ad[id].animacionCollection[keyn].styles.transition.match(/[0-9\.]{1,}(ms|s)/gi, '')

regx = /(s||ms)/g

time = time.toString().replaceAll(regx,'')

time = time.replace(",","+")

time = opener.sEval(time)

s += time

da=0










 
 if(a1<objlen) {
 
 if(a1 == 0) initval = readObj(obj,propertier)

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








function readObj(obj,prop,id,tag){





var ret = ""

for([key,value] of Object.entries(obj)){


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

if(tag == 'video' || tag == 'audio'){

if(key == 'autoplay'){


confSound += 'document.getElementById("'+tag+'_'+id+'").volume = 0.5;document.getElementById("'+tag+'_'+id+'").autoplay = "true";document.getElementById("'+tag+'_'+id+'").play();'}
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


textAlign:"text-align",

textDecoration:"text-decoration",
textIndent:"text-indent",


transformStyle:"transform-style",
transformOrigin:"transform-origin",

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



mxhtml = `\ndocument.body.innerHTML += \`<div style='background:#000000;color:white;font-weight:bold;z-index:9999999;position:fixed;top:0;left:0' id='fgtht1221'><a href='javascript:void(0);' onclick='`+mascode1+`;actsv();document.getElementById("fgtht1221").remove()' style="color:white;">ACTIVAR SONIDO [audio/vídeo multimedia]</a></div>\`;`



} else {mascode1 = "";mxhtml=""}


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


injectx = `<!DOCTYPE html><html><head>`+codecss+`<script type="text/javascript">onload=function(){`+codejs+`}</script></head>\
`+document.body.outerHTML+`\
</html>\
\
`


document.body.innerHTML += "<a href='javascript:void(0)' onclick='\
\
copen = open(\"about:blank\",\"copen\",\"width=555,height=666\");\n\
copen.document.write(\"<div><textarea style=width:100%;height:80px;>\"+unescape(escape(injectx))+\"</textarea></div>\"+unescape(escape(injectx)));\n\
copen.document.close();\n\
copen.focus();\n\
' style='background:rgba(255,255,255,.4);position:fixed;margin:0;bottom:1px;right:1px;z-index:9999999999999999'>SourcE</a>"+codecss


opener.AnimeWinOpt.innerHTML = "Animando Id: "+IdAnim


//alert(codejs)

eval(''+codejs+'')



}



