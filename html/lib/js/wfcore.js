

const write = function (txt){
document.write(txt)
}

const writeln = function (txt){
document.write(txt+"<br>")
}

const lnwrite = function (txt){
document.write("<br>"+txt)
}



defId = function(){
return "idcreator."+Version
}

defIdBodys = function(n){
if(!n) return 0
else return n
}


defIdTags = function(n,tag){
return tag+"_"+n
}


function getId(id){
return document.getElementById(id)
}


function debug(msg,param=DEBUG){
return false
if(param) return console.log(msg)
else return console.log(param+" [LEVEL DEBUG:"+param+"]")
}



function getId(id){
return document.getElementById(id)
}


const echo = function(value=defEcho){
document.body.innerHTML += value
}

const echoln = function(value=defEcho){
document.body.innerHTML += value + "<br>"
}

const lnecho = function(value=defEcho){
document.body.innerHTML += "<br>" + value
}

const b = function(val){
return document.write("<b>"+val+"</b>")
}

const bold = function(val){
return "<b>"+val+"</b>"
}


const selector = function(param){
return document.body.querySelector(param);
}

const loadIfApp = function(browserCode='default',object){

str = ""
code = navigator.appCodeName

reg = new RegExp(browserCode,'si')
res = reg.exec(navigator.userAgent)

if(res === null && browserCode != 'default') return;

for([key,value] of Object.entries(object)){
switch(key){
case 'css':
case 'style':
case 'styles':
case 'stylesheet':
str += `<link rel='stylesheet' href='${value}' type='text/css'>`
break;
case 'script':
case 'javascript':
case 'js':
str += `<script src='${value}' type='text/javascript'></script>`
break;
}
}

document.write(str);

}


const opener = function(txt=''){
opener = txt
this.write = function(txt){
write(e)
}
}

function dmenu(divid,classname){
    var dcls=document.getElementsByClassName(classname);
    for(i=0;i<dcls.length;i++){
    if(dcls[i].id!==divid){
    dcls[i].style.visibility="hidden";
    dcls[i].style.display="none";
    }else{
    dcls[i].style.visibility="visible";
    dcls[i].style.display="block";
     }
   }
 }
 
 
const display =  function (id){
if(!id) return "Undefined";
id = document.getElementById(id)
dsplay = id.style.display
if(dsplay=='block') id.style.display = "none"
else id.style.display = "block"
return dsplay
}


const temp = function(javascript='alert("funcion temp inframe.js")',type='out',time='2000'){

this.temp = temp
this.temp.clear = function(javascript){
return clearInterval(javascript)
}
if(type=='interval') return setInterval(``+javascript+``,time)
if(type=='timeout') return setTimeout(``+javascript+``,time)
else return false
}




const emulaClick =  function(emulado){
var y = document.querySelector(emulado);
y.click();
return;
}


const clickId = function (emulado){
var y = document.querySelector(emulado);
y.click();
return;
}



const objKeyExists = function(object,key){

for (const property in object) {
objectis=Object.is(property,key)
debug(object+"."+property+" = "+Object.is(property,key),'verbose')
if(property==key) {
 debug("TRUE: "+property+":"+key,'verbose')
 return true;
} else  {
 debug("FALSE: "+property+":"+key,'verbose')
}
}
return false
}


const events = function(resource){

resource.addEventListener("mouseover", function(e){

debug("MOUSEOVER: "+resource,'verbose,events,mouseover')

}, false);


resource.addEventListener("mouseout", function(e){

debug("MOUSEOUT: "+resource.id,'verbose,events,mouseout')

}, false);

resource.addEventListener("click", function(e){

debug("CLICK: "+resource.id,'verbose,events,click')

}, false);


resource.addEventListener("input", function(e){

debug("INPUT: "+resource.id,'verbose,events,input')

}, false);



  resource.addEventListener('DOMContentLoaded', () => {
    // Get the element by id
    
    debug("DomContentLoad","verbose,events")
    
    // Add the ondragstart event listener
 
  });


}





























/*CORE*/



init = 0;
DEBUG = 1
Version = "osiris"
console.log("wfcore :"+Version)
debug("Init Debug wfcore Versión:"+Version)
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


var BODY = function(HTML=CLONE){

cb = document.createElement("body")
cb.id= $[nb] = "BODY_"+defIdBodys(nb)
HTML.append(cb.id)
document.body = cb
body[nb] = getId(cb.id)
nb++
return cb
}


const Active = function(aBODY){
document.body = aBODY;
return aBODY
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
const addPanel = function(type="div",option="beforebegin",resourcein=document.body,rhtml=""){


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

const newWindow = function(className="DEFAULTDEV"){
js = `\
\
\
HTML.document.body.getElementsByClassName("`+className+`")[`+win+`].contentDocument.body.id ="BODY_`+win+`";\
events(HTML.document.body.getElementsByClassName("`+className+`")[`+win+`].contentDocument);\
alert(HTML.document.body.getElementsByClassName("`+className+`")[`+win+`].contentDocument.body.outerHTML)\
\
\
`
windows[1][win] = addPanel({TAG:"iframe",width:"100%",style:"border:solid 2px #102060;width:95%;margin:1% 1% 1% 1%;padding:1% 1% 1% 1%",name:"winsfrms_"+win+"",click:""+js+""})
windows[1][win].id = "newWin_"+win
windows[1][win].editable = true
windows[1][win].className = className

debug(windows,"verbose,core,windows")

events(windows[1][win])

jsx = `\
\
\
\
<script src=loadnet.js></script>\
\
\
\
`


js = `\
\
ActiveWinName = 'winsfrms_`+win+`';\
ActiveWin = winsfrms_`+win+`.document.body;\
if(!winctl[`+win+`]) {winctl[`+win+`] = false;}\
id = getId('`+windows[1][win].id+`');\
if(!winctl[`+win+`]) {id.src ="javascript:void(0);\``+jsx+`\`";}\
dmenu('`+windows[1][win].id+`','`+className+`','ERRvisibility');\
winctl[`+win+`] = "opened";\
\
\
\
\
`

windows[0][0][win] = addPanel({TAG:"div"})
windows[0][1][win] = addPanel({TAG:"button",click:""+js+""})
windows[0][0][win].className = "pestanas"
windows[0][1][win].className = "linker"
windows[0][1][win].innerHTML = "Pesta&ntilde;a "+parseInt(win+1)

moveTag(windows[0][1][win],windows[0][0][win])
moveTag(windows[0][0][win],GroupWindows)
moveTag(windows[1][win],GroupIframes)

win++

return windows[1][win]

}




const objAssignIf = function(object=object,prop,value="undefined") {


keyExists = objKeyExists(object,prop);


this.prop = prop




if(!keyExists) {


} else {
return object
}


}



const evalInstance = function(object=undefined,instance=undefined,value=undefined,type=""){



if(!object||!instance||!value){
if(Object.is(instance,instance)){
object = "Objeto existe pero falta valor:"+object;
} else if(!Object.is(instance,instance)){
object = "No existe la instancia en:"+object;
}
return object
} else {
if(type=="style") {


evalExpresion =  ''+object+'.style.'+instance+' = `'+value+'`'
eval(evalExpresion)

} if(type=="events") {




/*EVENTOS*/


}

else evalExpresion =  ''+object+'.'+instance+' = `'+value+'`'
return eval(evalExpresion)
}
}







function newwin2(inject="Inject Code",target,options=666){
(target?target:this.target)
this.open(`javascript:void(0);\``+inject+`\``,target,options);
this.document.close()
}

















