Version = "0.1.1a"
init = 0;
gt = 0
rsc = 0
nb = 1;
newTag = new Array() 
getTag = new Array() 
body = new Array()
fin = 0

Doc = "html"
Version = "auto"
defId = function(){
return "idCreator"+Version
}

defIdBodys = function(n){
return n
}


defIdTags = function(n,tag){
return tag+"_"+n
}



var HTML = function(){
HTML = document.createElement(Doc);
HTML.id="$".id=defId()
HTML.document = HTML.ownerDocument
HTML.ownerDocument.id = HTML.id
this.node = HTML.id
events(HTML.ownerDocument)
return HTML
}


//console.log(HTML)


console.log(HTML)

//HTML.new("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")





$ = new Array()

var BODY = function(HTML=CLONE){
var BODY = document.createElement("body");

BODY.id= $[nb] = "BODY_"+defIdBodys(nb)
HTML.append(BODY.id)
document.body = BODY
body[nb] = BODY
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
newTag[gtr].id = defIdTags(gtr,tag)
newTag[gtr].style = "auto"
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


function object(name,value) {
  return this.name = value
}

mm = new Array()
z=0

panel = new Array();
pnl = 0;
const addPanel = function(type="div",option="beforebegin",resourcein=BODY,rhtml=""){


snl = pnl
/* dsign Panel  */
_default = "dpanel_"+pnl
create =false
panel[snl] = new Object()


if(Object.is(type,type)){
ObjectType = type


for([key,value] of Object.entries(type)){
if(key=="TAG") {
panel[snl] = addNewTag(value,option,resourcein)
create = true;
break;
}
}
if(!create) panel[snl] = addNewTag("div",option,resourcein)

for (const [key, value] of Object.entries(type)) {



switch(key){
case 'innerHTML':
panel[snl].innerHTML = value
break;
case 'style':
panel[snl].style = value
break;
case 'class':
panel[snl].class = value
break;
case 'type':
panel[snl].type = value
break;
case 'value':
panel[snl].value = value
break;
case 'click':
panel[snl].addEventListener("click", function(e){
console.log(value)
eval(value)
} , false);

break;
case 'TAG':
panel[snl].tag = value;
break;
default:
Object.defineProperty(panel[snl], key, {
  value: ""+value+"",
  writable: true
});
break;
}
console.log(key.trim()+" => "+value.trim())
z++
} } else {
panel[snl] = addNewTag(type,option,resourcein)
}


if(rhtml) panel[snl].innerHTML = rhtml
panel[snl].id=_default
panel[snl].name=_default
pnl++
return panel[snl];
}


/* create panel and return resource HTMLElement*/






