init = 0;
DEBUG = 0
Version = "jSa 0.2 beta"
console.log("Init idcreator Versión:"+Version)
debug("Init Debug Versión:"+Version)
gt = 0
rsc = 0
nb = 1;
$ = new Object()
newTag = new Array() 
getTag = new Array() 
body = new Object({bodyDocument:""+Version+""})
fin = 0

var ActiveWin = false

Doc = "html"

debug("$ as Object:")+debug($)

var HTML = function(){
HTML = document.createElement(Doc)
HTML.id="$".id=defId()
HTML.document = HTML.ownerDocument
HTML.ownerDocument.id = HTML.id
this.node = HTML.id
events(HTML.ownerDocument)
return HTML
}


//console.log(HTML)

CLONE = HTML()

debug("Init HTMLDocument:"+HTML)
debug("HTML as CLONE:"+CLONE)
//console.log(HTML)
//console.log(CLONE)


//HTML.new("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")

BODY = "body"



var BODY = function(HTML=CLONE){
const BODY = document.createElement("body")
BODY.id= $[nb] = "BODY_"+defIdBodys(nb)
HTML.append(BODY.id)
document.body = BODY
body[nb] = getId(BODY.id)
nb++
events(getId(BODY.id))
return   BODY
}


const Active = function(aBODY){
BODY = aBODY
document.body = BODY;
return BODY
}


const createTag = function(tag){
/* Crea un Tag nuevo  */
gtr = gt
newTag[gtr] = document.createElement(tag)
newTag[gtr].type = tag
switch(tag){
case 'meta':
case 'charset':

/* Reservado para etiquetas meta*/

break;
default:
newTag[gtr].style = "auto"
newTag[gtr].id = defIdTags(gtr,tag)
//newTag[gtr].draggable = true 
break;
}

gt++
return newTag[gtr]
}


const addTag = function(resource,option="beforebegin",resourcein=BODY){
/* inserta un elemento origen en la posicion adyacente elemento destino
                                 origen, posicion, destino           
 */
gtr = rsc
getTag[gtr] = resourcein.insertAdjacentElement(option,resource)
moveTag(resource,resourcein)
events(getTag[gtr])
rsc++
return getTag[gtr]
}

const addNewTag = function (tag,option="beforebegin",resourcein=BODY){
/* insterta un tag  */
return addTag(createTag(tag),option,resourcein)
}

const addNewTagIn = function(tag,resource,option='beforebegin') {

Create = addNewTag(tag,option,resource)
/* insterta un tag  */
moveTag(Create,resource)
return Create
}


const moveTag = function(resource1,resource2){
return resource2.append(resource1)
}



/*
function object(name,value) {
  return this.name = value
}
*/

mm = new Array()
z=0

panel = new Object();
pnl = 100000;
const addPanel = function(type="div",option="beforebegin",resourcein=BODY,rhtml=""){


snl = pnl
/* dsign Panel  */
_default = pnl
create =true
panel[snl] = new Array()


if(Object.is(type,type)){
ObjectType = type

for([key,value] of Object.entries(type)){
if(key=="TAG") {
panel[snl] = addNewTag(value,option,resourcein)
create = false;
break;
}
}
if(create===true) panel[snl] = addNewTag("div",option,resourcein)


debug("addPanel type: \n"+type,"vervose,core,panel")
debug(type,"vervose,core,panel")

for(const [key, value] of Object.entries(type)) {

switch(key){

case 'click':
panel[snl].addEventListener("click", function(e){
debug(value,'verbose')
eval(value)
} , false);

break;
case 'TAG':
panel[snl].tag = value;
break;
default:


if(!value) xvalue = undefined
else xvalue = value

if(ret = objAssignIf(panel[snl],key,xvalue)){


if(key != 'comentario') evalInstance('panel['+snl+']',key,xvalue)
else {
debug("COMENTARIO<<<<<<<<<<<<<<<"+value)
this.panel[snl].comentario = comentario
}

}

break;
}
debug(key+" => "+value,'verbose')
z++
} } else {
panel[snl] = addNewTag(type,option,resourcein)
}
if(rhtml) panel[snl].innerHTML = rhtml //parametro obsoleto - eliminar en futuro
panel[snl].id=_default
//panel[snl].name=_default
//Object.freeze(panel[snl]);
pnl++
return panel[snl];
}


/* create win panel and return resource HTMLElement*/

win = 0;
windows = new Array("makerWins")
windows[0] = new Array(0)
windows[0][0] = new Array()
windows[0][1] = new Array()
windows[1] = new Array()
winctl = new Array();
winsfrms = new Array()


ActiveWinName = "DEV"


jsp = new Array()
jspm = 0

const newWindow = function(className="DEFAULTDEV"){



windows[1][win] = addPanel({TAG:"iframe",style:"border:solid 2px #102060;width:100%;margin:0;padding:0",contentEditable:"true",name:"winsfrms_"+win+""})
windows[1][win].id = "newWin_"+win
sEval(`windows[1].winsfrms_`+win+` = `+(win + 1)+``)
windows[1][win].linker = "linker_"+win
windows[1][win].className = className

debug(windows,"verbose,core,windows")

events(windows[1][win])

jsx = `\
\
\
\
<script src=net.js></script>\
\
\
\
`


js = `\
ActiveWinId = 'newWin_`+win+`'\n\
ActiveWinName = 'winsfrms_`+win+`'\n\
ActiveWin = winsfrms_`+win+`.document.body\n\
if(!winctl[`+win+`]) {winctl[`+win+`] = false}\n\
id = getId('`+windows[1][win].id+`')\n\
if(!winctl[`+win+`]) {id.src ="javascript:void(0);\``+jsx+`\`"}\n\
dmenu('`+windows[1][win].id+`','`+className+`','ERRvisibility')\n\
winctl[`+win+`] = "opened"\n\
AnimeWinOpt.innerHTML = "Seleccionada Pesta&ntilde;a `+(win + 1)+`"\n\
listTags(windows[1][`+win+`])\n\
\
\
\
\
\
`

windows[0][0][win] = addPanel({TAG:"div"})
windows[0][1][win] = addPanel({TAG:"button",click:""+js+""})
windows[0][0][win].className = "pestanas"
windows[0][1][win].className = "linker"
windows[0][1][win].id = "linker_"+win
windows[0][1][win].innerHTML = "Pesta&ntilde;a "+parseInt(win+1)

moveTag(windows[0][1][win],windows[0][0][win])
moveTag(windows[0][0][win],GroupWindows)
moveTag(windows[1][win],GroupIframes)

retWin = windows[1][win]

win++

return retWin

}



desagrupa = ds = false

function listTags(winobj,xnm){


anm = sEval('windows[1].'+winobj.name+'')

jsz4 = `\
\
\
\
\
if(!desagrupa) dmenu('AnimeWin','iframes');\
newwin2(\`<script>if(!parent.desagrupa) {parent.ActiveWin=false;}taskN = '`+anm+`'</script><script src=xhr.js></script><script src=animall.js></script>\`,'AnimeWin','width=555,height=666')\
\
\
\
`

animar = ` \
<button onclick="`+jsz4+`" style='color:#040432;border:solid 1px #23554'>Animar Pesta&ntilde;a</button>\
\
\
`


jsz4 = `\
\
\
if(!desagrupa) {\
getId('AnimeWin').className = 'desagrupaanw';\
getId('AnimeWin').style.visibility='visible';\
getId('AnimeWin').style.background='#ffffff';\
getId('AnimeWin').style.resize='both';\
getId('AnimeWin').style.display='inline-block';\
getId('AnimeWin').style.float='left';\
getId('AnimeWin').style.border='0';\
getId('AnimeWin').style.overflow ='hidden';\
getId('AnimeWin').style.border = 'solid 2px green';\
getId('AnimeWin').style.resize='vertical';\
this.innerHTML = ds = 'Agrupar';desagrupa = true\
}\
else {\
getId('AnimeWin').className = 'iframes';\
getId('AnimeWin').style.display='none';\
this.innerHTML = ds = 'Desagrupar';desagrupa=false;\
}\
\
\
\
\
`

if(!ds) ds = "Desagrupar"

desagrupar = `\
\
<button onclick="`+jsz4+`" style='color:#040432;border:solid 1px #23554'>`+ds+`</button>\
\
`


if(!xnm) xnm = winobj.id


if(winobj.name == 'winsfrms_'+(anm-1)) {txt = "Pesta&ntilde;a Seleccionada"}
else {txt='Activar Pesta&ntilde;a'}

src = ` <a href='javascript:void(0);' style='color:#daea0f;' onclick='alert(`+winobj.name+`.document.body.outerHTML);'> [html]</a> `+animar+desagrupar

wina = ` <a href='javascript:void(0);' style='color:#daea0f;' onclick="ActiveWin = `+winobj.name+`.document.body;clickId('#linker_`+(anm-1)+`');AnimeWinOpt.innerHTML = 'Pesta&ntilde;a Activa `+anm+`'" id='activewin'>[`+txt+` `+(anm)+`]</a>`

TimeLine.style.display = 'block'
TimeLine.innerHTML = "<div style='width:100%;color:#daea0f;'><button style='position:relative;' onclick='if(getId(\"TagIframes\").style.display==\"block\"){getId(\"TagIframes\").style.display=\"none\";this.innerHTML =\"↓↓\"}else{getId(\"TagIframes\").style.display=\"block\";this.innerHTML = \"ocultar\"}'>ocultar</button>"+wina+" "+src+"</div>"

writes = ""

for([k,v] of Object.entries(ad)){

if(ad[k].win == winobj.name) {

if(ad[k].id=='erased') continue

writes += "<div style='background:white'>"+adILT(ad[k])+"</div>"

internalsgen++
}

}


TagIframes.innerHTML = writes

}

/** Delete Transition - Elimina una transición y renueva el array de trasiciones (collection)**/


function deleteTransition(id,position){


ad[id].animacionCollection[position] = "erased"
 
getControl(id)



}



/** getControl - escribe control de transiciones */



function getControl(param){


x = new Array()
n=0
for(values of ad[param].animacionCollection){

if(values=="erased") continue
else {
x[n] = values
n++
}
}

ad[param].animacionCollection = new Array()

ad[param].animacionCollection = x

data=`\
\
 Transiciones `+(ad[param].animacionCollection.length) +` [  \
\
`


n = 0

for(key in ad[param].animacionCollection){

if(ad[param].animacionCollection[key] == "erased") continue

data += ` <a href="javascript:deleteTransition(`+param+`,`+key+`)">`+(n+1)+`</a> `
n++
}


data+= " ] "



document.getElementById("animel_"+param).innerHTML = "Collection id "+param+data
document.getElementById("animel_"+param).style.display = "block";


}



function avt(param,id){

alert("Esta operación está en fase de desarrollo")
ad[id].animationToTransition = param

}



function adILT(obj){


st = 'width:100%;font-size:14px;border:solid red 0.4%;text-align:left;cursor:default;padding:1px 0 1px 0;clear:both;background:#dbdbaa;'




jsz3 = `\
\
\
\
if(!desagrupa){dmenu('AnimeWin','iframes')};void(0)\n\
newwin2(\`<script>if(!parent.desagrupa) {parent.ActiveWin=false;};IdAnim = `+obj.id+`</script><script src=anim.js></script>\`,'AnimeWin','')\n\
\
\
\
`

animarElemento =`\
`

animarElementoTL =`\
<div id='animel_`+obj.id+`' style='display:inline-block;width:flex;margin:1px auto 1px auto;padding:2px;overflow:auto;background:#ffffff;clear:both;display:none;'></div>\
`


animarElemento += `\
<div title="Ajustar Animación a Velocidad de Transiciones"  style="background:white;padding:1px 1px 2px 1px;margin:1px;height:13px;border:0;float:right;display:inline-block"><input style="margin:0" type="checkbox" onclick="avt(this.checked,`+obj.id+`)">avt</div>\
 <button title="Animar id:`+obj.id+`" onclick="`+jsz3+`" class="botones_tags" style="margin:0;"> Animar </button> \
\
`







if(obj.tag != 'body') {

del = ` <button class="botones_tags" onclick='if(confirm("¿eliminar?")) {delIdAd(ad[`+obj.id+`],"et_`+obj.id+`")}'>eliminar</button> `

if(obj.anidable)  { 

//tag anidable
//del += ` <b style="float:right">anidable</b> `

}
}
else del = ""



xttag = firstToUpper(obj.tag)


return `<div id='et_`+obj.id+`' style='`+st+`'> `+xttag+` `+animarElemento+` <button onclick="idEdit(`+obj.id+`,EditPropertiers,CONTROLS,internalsgen)" class="botones_tags" id='edit_`+obj.id+`' title='Editar id:`+obj.id+`'> editar </button> `+del+` `+animarElementoTL+`  </div>`

}


editing = false


function delIdAd(obj,remove){

if(!ActiveWin){clickId('#activewin');alert("Eliminar elementos fuera de pestaña seleccionada no permitido\n Se ha seleccionado la pestaña correspondiente\nVuelva a pulsar eliminar objeto");return;  }
ad.slice(obj.id,1); 
ActiveWin.ownerDocument.getElementById(obj.id).remove();
n = obj.id
ad[obj.id].id = 'erased';

if(editing == n){
IdEdit.innerHTML='Eliminado id: '+n;
EditPropertiers.innerHTML='Eliminado id: '+n;
}
document.getElementById(remove).remove();
}



const makeTagDragDrop = function(xtag,tagx,controls){

xtag.ondragstart = function(){
stopDD = false
debug('start dragstar event en video tag ','pruebas,verbose')
if(!aw()) {
if(!document.getElementById('activewin')) {alert('Active una pestaña para realizar operaciones');stopDD = true;}
else{clickId('#activewin');}
}
}

xtag.ondragend = function(){

if(stopDD) {return false}

if(ad.length) drk = ad.length 
else drk = 0;

debug('end'+ActiveWin)
ad[drk] = addPanel(tagx)
ad[drk].id = drk
ad[drk].idad = false
ad[drk].animationToTransitions = false
if(tagx.TAG=="div") ad[drk].anidable = "true"
events(ad[drk])
ad[drk].win = ActiveWinName 


moveTag(ad[drk],ActiveWin)

TagIframes.innerHTML += adILT(ad[drk],ActiveWin)
TagIframes.className = "DYNEDITOR"
TagIframes.style = "border:solid 2px red ; overflow:hidden;resize:vertical;"
idEdit(ad[drk].id,EditPropertiers,controls,internalsgen)
internalsgen++
/* // habilita edicion de id en mouseover
ad[drk].onmouseover = function (){
idEdit(this.id,EditPropertiers,controls,internalsgen)
internalsgen++
}
*/
//drk++
}

}





function rgb(r, g, b, a="") {
  return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

function rgba(r,g,b,a=""){return rgb(r,g,b,a="")}

//alert(rgbToHex(0, 51, 255)); // #0033ff




const addControl = function(obj,property,control,def,internal,xprop){


if(control){
var width = "100%"
var type = "text"
if(xprop == 'styles') var event = "onkeyup"
else if(xprop == 'propertiers') var event = "onchange"
else{/*NADA*/}
//var mstyle = "margin:auto 1px auto 3px;"
var attrbs = ""
var value = `value='`+def+`'`
var masjs = "void(0);";
var classx = "controles_input"
if(control == '<units>') {}
else if(control == '<text>') {}
else if(control == '<select>') {}
else if(control == '<flex>') {}
else if(control == '<color>') {
event = "onchange";
type = "color";
classx = "controles_color"
attrbs = ``




xv = `ad[`+obj.id+`].`+property+``


xv = sEval(xv)

if(xv.match(/^rgb+/si)) {
value = `value = '`+sEval(xv)+`'`
}
} 



if(control == '<textarea>') {


classx = "controles_textarea"

disid = ""
if((property=='innerHTML' || property=='innerText') && ad[obj.id].tag=='body') disid = "disabled"


type = "textarea"
value=def

jsz1 = 'ad['+obj.id+']'
val = `\
\
<`+type+` `+disid+` id="CONTROL_`+mas1+`" `+event+`="if(!aw(ActiveWin)|| ActiveWinName != 'winsfrms_'+(winN-1)){clickId('#xrmst1')}evalInstance(jsz1,'`+property+`',this.value,'`+xprop+`');`+masjs+`" class="`+classx+`" `+attrbs+`> `+value+`</`+type+`>\
\
`


} else {

disid = ""

if(property=='id') disid = "disabled"
if(property=='animacion') disid = "disabled"
jsz2 = 'ad['+obj.id+']'
val = `\
\
<input `+disid+`  alt="`+obj.id+`" title="`+property+`" type="`+type+`" id="CONTROL_`+mas1+`" `+event+`="if(!aw(ActiveWin) || ActiveWinName != 'winsfrms_'+(winN-1)){clickId('#xrmst1')}evalInstance(jsz2,'`+property+`',this.value,'`+xprop+`');`+masjs+`" `+value+` class="`+classx+`" `+attrbs+`>\
\
`



}

mas1++
return val
}

}


//acprop = {paddingLeft:"<units>"}


function idEdit(id,panel,CONTROLS,internalsgen){


editing = id
addPan = ""
wd = ad[id]
panel.innerHTML = ""
coll = ""

s = ""
rs = ""




if(coll = ad[id].animacionCollection) { coll = ad[id].animacionCollection.length  }

if(coll){
coll = getControl(id)
} else if(coll == undefined) coll = ""

winN = sEval('windows[1].'+wd.win+'')




workw = `<div style='width:100%;background:#101010;padding:0;'><div title="Grabación" style='border:3px outset #da2939;width:18px;height:16px; border-radius: 35%;background:#ff190c;cursor:pointer;margin:0;' onclick="if(!aw(ActiveWin)|| ActiveWinName != 'winsfrms_'+(winN+1)){if(!desagrupa){clickId('#xrmst1')}}advancedControls('`+id+`','animacion','ad[`+id+`].animacion','',0);closectrl(`+id+`)"></div></div><div style="font-size:14px;text-align:right;background:#534793;color:#DAeEEE;border-right:solid 0px #fafafa;border-left:solid 0px #fafafa;padding:4px 0 3px 0px;width:100%;font-size:15px;text-align:center;">trabajando con id: <b>`+id+`</b> :<a href="javascript:void(0);" onclick="clickId('#linker_`+(winN -1)+`');AnimeWinOpt.innerHTML = 'Trabajando con Pesta&ntilde;a `+winN+`'" id='xrmst1' style="background:white;">Pesta&ntilde;a `+winN+`</a>: `+wd+` </div><div id='animacion'></div>`

//wd.style.borderColor = "#ef45ef"

rsm = new Object();
defrsm = 0;



for([key,valueControls]  of Object.entries(CONTROLS)){


rsm[key] = new Object();


if(key == "styles") {

objctl = valueControls
obj = wd.style
objEval = "wd.style"
comp = "style."
idp = "estilos"
s = `<div class="menu_edit"  onclick="display('ID_`+key+`')">Estilos</div>`


} else if(key =='propertiers') {


objctl = valueControls
obj = wd
objEval = "wd"
comp = ""
idp = "propiedades"

s = `<div class="menu_edit" onclick="display('ID_`+key+`')">Propiedades</div>`



} else if(key =='events') {


objctl = valueControls
obj = wd
objEval = "wd"
comp = ""
idp = "eventos"

s = `<div class="menu_edit" onclick="display('ID_`+key+`')">Eventos</div>`



} else {idp = "ctrliddefault"}




mas=0

for (const property in obj) {


if(isNaN(property)){

if(property.length < 10) br = "<br>";
else br = ""

if(property.indexOf("-") < 0){


 if(value = objKeyExists(objctl,property,"returnvalue")){


c = objEval+'.'+property+''

def = sEval(objEval+'.'+property+'')

if(!def && key == "styles") {
if(property=="color") def = "#000000";
else if(property == "backgroundColor") def = "#ffffff";
else if(property == "borderColor") def = "#ffffff";
else def = "none"
} else if(!def) def = "";


if(!internals) internal = 0;

control =  addControl(wd,comp+property,value,def,internal,key)


rsm[key][property] = new Object()

rsm[key][property]['html'] = `<div class="area_controles"  title="`+property+`"><div><span style='cursor:pointer;float:left;padding:2px;display:inline-block;' onclick='advancedControls("`+id+`","`+property+`",ad[`+id+`].`+property+`,"",`+internal+`)'>`+property+`</span></div><div style="display:block-inline;">`+control+`</div><div id='internals_`+internal+`' class='container_controles_avanzados'></div></div>`

rsm[key][property]['value'] = def


internal = internals++;

}

} 


}

mas++
}


rsm[key]['PANEL'] = `<div class="paneles">`+s+`<div style='border:red solid 0px;width:100%;border-right:0;border-left:0;'><div  id="ID_`+key+`" style="height:auto;overflow-y:auto;width:99%;text-align:center;background:rgba(0,0,0,0.5);"><br clear=both></div></div></div> `



}


//console.log(rsm)

IdEdit.innerHTML = workw


adids = new Object();

for(prop in rsm){



	switch(prop){
	
	case 'styles':
       
	IdEdit.innerHTML  += `<div id="PANEL_`+prop+`" class='paneles'><div id='PANEL_ANIMATION' class='paneles_edit'></div><div id="PANEL_FONTS" class='paneles_edit'></div><div id='PANEL_FAVORITOS' class='paneles_edit'></div><div id='PANEL_VARIOS' class='paneles_edit'></div></div>`
	break;
       
              
	default:

	IdEdit.innerHTML  += `<div id="PANEL_`+prop+`" class="paneles"></div>`
	break;	
	}





for(mprop in sEval('rsm.'+prop+'')){


if(mprop == 'PANEL') {

panel.innerHTML  += sEval('rsm.'+prop+'.PANEL')
       
} else {        
        
       
msid = "ID_"+prop

if(prop == 'styles'){

switch(mprop){


case 'transition':
case 'animation':
case 'animationDelay':
case 'animationDirection':
case 'animationDuration':
case 'animationFillMode':
case 'animationIterationCount':
case 'animationName':
case 'animationPlayState':
case 'animationTimingFunction':
msid = "PANEL_ANIMATION"
break;

case 'textIndent':
case 'textDecoration':
case 'font':
case 'fontFace':
case 'fontSize':
case 'fontFamily':
case 'fontWeight':
case 'letterSpacing':
case 'wordSpacing':
case 'lineHeight':
case 'color':
case 'backgroundColor':
case 'borderColor':
case 'borderWidth':
msid = 'PANEL_FONTS'
break;

case 'top':
case 'left':
case 'right':
case 'bottom':
case 'width':
case 'height':
case 'margin':
case 'padding':
case 'border':
msid = 'PANEL_FAVORITOS'
break;


case 'overflow':
case 'position':
case 'zIndex':
case 'background':
case 'float':
case 'visibility':
case 'resize':
case 'filter':
case 'transform':

msid = 'PANEL_VARIOS'

break;

default:
msid = msid
break;
}

}


value2 = sEval('rsm.'+prop+'.'+mprop+'.value')
htmlxx = sEval('rsm.'+prop+'.'+mprop+'.html')
 
if(!adids[msid]) adids[msid] = htmlxx
else adids[msid] += htmlxx

}
}
}



for(key2 in adids){
evk = ""
evk = sEval('adids.'+key2+'')
if(evk) document.getElementById(key2).innerHTML = evk

} 


}







function advancedControls(id,key,value,pos,internal) {



advanced_control = advancedControl(id,key,pos,internal)



if (key == "animacion") iid = "animacion"
else iid = 'internals_'+internal


inhtml = `<div class="controles_avanzados" id='ctrl_`+key+`'><a  onclick="display('`+iid+`')" style=color:red;cursor:pointer;float:right;top:0;>[close]</a><br clear=both>`
inhtml += `<div style="padding:5px;">`+advanced_control+`</div>` 
inhtml += `<div style='margin:10px 0 10px 0;'>Advanced Controls</div></div>`



getId(iid).style.display ='block';
getId(iid).style.height = 'auto';
getId(iid).style.width = '100%';


getId(iid).innerHTML = inhtml

}





function advancedControl(id,key,pos,internal){



switch(key){


case 'transition':

advanced = "TRANSITION ADVANCED CONTROL"



break;



case 'animacion':


advanced = animacion_control(id,pos,internal)


break;


case 'src':

advanced = "<iframe frameborder=0 src='https://vtwitt.com/plugin.php?plugin=youtubedl' width=100% height=100%></iframe>" //animacion_control(id,pos,internal)


break;


default:


advanced = `Esta propiedad no tiene control avanzado`

break;
}


return advanced;


}




ctrla = 0;




function closectrl(id){

if(ad[id].animacion == 'Recording'){

document.getElementById('ctrl_animacion').style.display = "none"

}

}



function animacion_control(id,pos,internal){


if(ada = ad[id].animacion){


switch(ada){



case 'START':


ad[id].animacionCollection = new Array();

ad[id].animacion = "Recording"

animacion_control(id,pos,internal)



break;

case 'Recording':

rtsr = transitions(id,ad[id].animacionCollection,internal)



//mktm = make_timeline(id,ad[id].animacionCollection[rtsr[1]])


//def = "Grabada Transición "+(rtsr[1])+" para id:"+id+"<br>"+mktm[1]
def = "recording"
getControl(id)

break;


case 'LAYERS':

alert("L")

break;


case 'PAUSE':

mktm = make_timeline(id)

return mktm[1]

break;


}



} else {




 def = `<div style='font-size:14px;'>Establezca propiedades y estilos de inicio<br> y pulse <a onclick="if(!aw(ActiveWin)){clickId('#activewin')};idEdit('`+id+`',EditControls,CONTROLS,'`+internal
+`');advancedControls('`+id+`','animacion',ad[`+id+`].animacion = 'START','',`+internal+`);closectrl(`+id+`)" style="cursor:pointer;text-decoration:underline;color:#1222dd">Grabar</a></div>`

}



return `\
\
<div><b style='font-size:10px;'>ANIMACION_CONTROL ID `+id+`</b><br>`+def+`</div>\
\
`
}

rts = new Array();
rts[0] = new Array();

function transitions(id,obj,pos,internal){


//alert(obj.length)

if(typeof rts[0][id]=='undefined') {
rts[0][id] = 0
}
else {
rts[0][id]++
}


r1 = {}


for(property in CONTROLS){

r1[property] = {}

value = sEval('CONTROLS.'+property+'');

for(key in value){

if(property =="styles") ev = sEval('ad['+id+'].style.'+key+'')
else ev = sEval('ad['+id+'].'+key+'')





if(ev) {
r1[property][key] = ev;
 
// debug(" "+key+":"+ev)
 
 }
}

}


//console.log(r1)



rts[1] = rts[0][id]
rts[2] =  id


rts[3] = r1


ad[id].animacionCollection[ad[id].animacionCollection.length] = r1

rts[1] = ad[id].animacionCollection.length

//console.log(rts)

return rts;


}

rmt = new Array()

function make_timeline(id,obj){

rmt[0] = obj


jsz3 = `\
\
\
\
\
newwin2(\`<script>parent.ActiveWin=false;IdAnim = `+id+`</script><script src=anim.js></script>\`,'AnimeWin','')\
\
\
\
`



jsz4 = `\
\
\
\
\
newwin2(\`<script>parent.ActiveWin=false;IdAnim = `+id+`</script><script src=animall.js></script>\`,'AnimeWin','')\
\
\
\
`


rmt[1] = `\
\
\
\
\
\
`

rmt[2] = id

return rmt

}








































