
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
return;
if(param == 'verbose') return false
if(param) return console.log(msg)
else return console.log(param+" [LEVEL DEBUG:"+param+"]")
}


//function object(name,value) {


const objKeyExists = function(object,key,ret=""){


for (const property in object) {

objectis=Object.is(property,key)
 
debug(object+"."+property+" = "+Object.is(property,key),'verbose')

if(property==key) {
 //console.log("TRUE"+property+":"+key)
 
 
 if(ret =="returnvalue") {
 
 
 
 for([key2,values2] of Object.entries(object)) { 
 if(key2==key) return values2

 }

 } else {return true; }  // ${object[property]}`);
} else  {
//console.log(property+":"+key)
}
}
return false

}



const objAssignIf = function(object=object,prop,value="undefined") {


keyExists = objKeyExists(object,prop);


this.prop = prop



//console.log("=>"+keyExists)


if(!keyExists) {
//console.log(":0:"+this.prop)

} else {
//console.log(":1:"+this.prop)
return object
}

/*
if(Reflect.defineProperty(object, prop, {
  value: "+value+",writable:true
})) {
debug("DefinePropertie:"+prop+":"+value)
console.log(this.prop+" = "+value)
np = []
np[0] = this.prop
np[1] = value
  return np;
} else {
debug("NOT_DefinePropertie:"+prop+":"+value)
return false;
}
*/

}





const events = function(resource){

resource.addEventListener("mouseover", function(e){

//debug("MOUSEOVER: "+resource.id,'verbose,events,mouseover')

}, false);


resource.addEventListener("mouseout", function(e){

//debug("MOUSEOUT: "+resource.id,'verbose,events,mouseout')

}, false);

resource.addEventListener("click", function(e){

debug("CLICK: "+resource.id,'verbose,events,click')

}, false);


resource.addEventListener("input", function(e){

debug("INPUT: "+resource.id,'verbose,events,input')

}, false);











}













var style = function(style=style){
this.style = style
}



function firstToUpper(str){
function toUpper(param){
return param.toUpperCase();
}
return str.replace(/^.?/si,toUpper)
}




function aw(d){

if(ActiveWin==false) {return false;}
else return ActiveWin
}


function devwin(inject="Inject Code"){

dmenu('DEV','iframes');
ActiveWin = false;
DEV.open(`javascript:void(0);\``+inject+`\``,"DEV");
DEV.document.close()


}




function newwin(inject="Inject Code",options=666){
ActiveWin = false;
this.open(`javascript:void(0);\``+inject+`\``,this.target,options);
this.document.close()
}



function newwin2(inject="Inject Code",target,options=666){
(target?target:this.target)
this.open(`javascript:void(0);\``+inject+`\``,target,options);
this.document.close()
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
sEval(evalExpresion)

} if(type=="events") {




/*EVENTOS*/


}

else evalExpresion =  ''+object+'.'+instance+' = `'+value+'`'
return sEval(evalExpresion)
}
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
return str;
}



function dmenu(divid,classname,type){
    var dcls=document.getElementsByClassName(classname);
    for(i=0;i<dcls.length;i++){
    if(dcls[i].id!==divid){
    dcls[i].style.visibility="hidden";
    if(type!='visibility') dcls[i].style.display="none";
    }else{
    dcls[i].style.visibility="visible";
    if(type!='visibility') dcls[i].style.display="block";
     }
   }
 }
 
 
const display =  function (id){
if(!id) return "Undefined";
id = document.getElementById(id)
st = id.style
if(st.display=='block') {
st.display = "none"
} else {
st.display = "block"
}
return st.display
}



function sEval(obj) {
    return Function('"use strict";return (' + obj + ')')();
}


 function clickId(emulado){
var y = document.querySelector(emulado);
y.click();
return;
}





















