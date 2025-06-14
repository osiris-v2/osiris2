// Función para procesar la variable
/* AJAX */
function uploadFile(options) {
  const fileInput = document.getElementById(options.fileInput);
  const file = fileInput.files[0];
  if (!file) {
    document.getElementById(options.fileOutput).innerHTML = "Por favor, selecciona un archivo.";
    return;
  }
  const fileExtension = file.name.split('.').pop().toLowerCase();
  const fileMimeType = file.type;

  if (!options.allowedExtensions.includes(fileExtension) || !options.allowedMimeTypes.includes(fileMimeType)) {
    document.getElementById(options.fileOutput).innerHTML = "Tipo de archivo no permitido.";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "upload.php", true); // Reemplaza con tu URL de servidor
  xhr.onload = function() {
    if (xhr.status === 200) {
      document.getElementById(options.fileOutput).innerHTML = " " + xhr.responseText;
    } else {
      document.getElementById(options.fileOutput).innerHTML = "Error al subir el archivo: " + xhr.status;
    }
  };
  xhr.onerror = function() {
    document.getElementById(options.fileOutput).innerHTML = "Error de red al subir el archivo.";
  };
  xhr.upload.onprogress = function(e) {
    if (e.lengthComputable) {
      const progress = Math.round((e.loaded / e.total) * 100);
      document.getElementById(options.fileProgress).innerHTML = "Progreso:"+ progress + "%"
      console.log("Progreso:", progress + "%");
      // Actualizar una barra de progreso aquí (opcional)
    }
  };
  xhr.send(formData);
}























$ajax = [{

info:`

Función ajax para facilitar el uso de ajax (XMLHttpRequest)

Formato:

array ajax( object  )

o abreviando ajax({})

métodos:

handler,location,method,async,datas,id,block


`,

version:0.1

}]


const ajax = function (ajax, auto_index = $ajax.length) {
    ajax.handler ? auto_index = ajax.handler : auto_index = auto_index;

    if ($ajax[auto_index]) {
        if ($ajax[auto_index].block == true && $ajax[auto_index].end !== true) {
            console.log("BLOCKED:", auto_index);
            return "blocked handler";
        }
    } else {
        $ajax[auto_index] = new Array();
    }

    $ajax[auto_index] = {
        xhr: [new XMLHttpRequest()] || false,
        location: ajax.location || "",
        async: ajax.async || true,
        datas: ajax.datas || false,
        method: ajax.method || "GET",
        id: ajax.id || false,
        eval: ajax.eval || false,
        handler: auto_index,
        block: ajax.block || false,
        end: false,
        prejs:ajax.prejs || false,
    };

    if ($ajax[auto_index].method.toUpperCase() == "GET") {
        $ajax[auto_index].location = $ajax[auto_index].location + "?" + $ajax[auto_index].datas;
    }

    $ajax[auto_index].xhr[0].open($ajax[auto_index].method, $ajax[auto_index].location, $ajax[auto_index].async);


           if($ajax[auto_index].prejs != false){
            
            //  PREJS
            
             console.log("Ejecutando Js:",$ajax[auto_index].prejs)
             new Function($ajax[auto_index].prejs)();
           
           
           }
 

    $ajax[auto_index].xhr[0].onreadystatechange = function () {
        console.log("ID" + $ajax[auto_index].id);
        console.log("Ready State:" + $ajax[auto_index].xhr[0].readyState);


          if ($ajax[auto_index].xhr[0].readyState == 4) {
                        

           if($ajax[auto_index].eval == true){        
   
                    new Function($ajax[auto_index].xhr[0].responseText)();

          }

            if ($ajax[auto_index].id) {
                if ($ajax[auto_index].id.charAt(0) === '+') {
                    document.getElementById($ajax[auto_index].id.substring(1)).innerHTML += $ajax[auto_index].xhr[0].responseText;
                } else {
                    document.getElementById($ajax[auto_index].id).innerHTML = $ajax[auto_index].xhr[0].responseText;
                }
            }
        

        
            $ajax[auto_index].end = true;
        }
    };

    if ($ajax[auto_index].method.toUpperCase() == "POST") {
        $ajax[auto_index].xhr[0].setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        $ajax[auto_index].xhr[0].send($ajax[auto_index].datas);
    } else {
        $ajax[auto_index].xhr[0].send();
    }

    console.log($ajax[auto_index]);

    return $ajax[auto_index];
};


/*compatibilidad con vieja ajaxPost*/

ajaxPost = function(datas="",id="",location="",method=""){
return ajax({
datas:datas,
id:id,
location:location,
method:method,
handler:"BLOCKED_POST",
block:true
})
}


/*end Ajax*/










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


function getIdValue(id){
return document.getElementById(id).value
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
document.body.innerHTML = "<br>" + value + document.body.innerHTML 
}

function b(val){
return document.write("<b>"+val+"</b>")
}

const bold = function(val){
return "<b>"+val+"</b>"
}


const selector = function(param){
return document.body.querySelector(param);
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



function clearHTML(id){
if(!id) return "Undefined";
id = document.getElementById(id)
id.innerHTML = "";
}


const emulaClick =  function(emulado){
var y = document.querySelector(emulado);
y.click();
return;
}


const clickId = function (emulado){
var y = document.querySelector("#"+emulado);
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


const wfcore = function (param) {

    const info = {
        version: 1
    };
    const obj = {
        parseIni: function (input) {        
                    function processVariable(input) {
                      const lines = input.trim().split('\n');
                      const stack = [];
                      const adp = []
                      let output = '';

                      for (let line of lines) {
                        const [element, depth] = parseLine(line);
                              
                        while (stack.length > depth) {
                            stack.pop();
                        }
                        var regex = /(.+?)(?:\s(.*))?$/;
                        var coincidencia = element.trim().match(regex);
              
                        if(!coincidencia) continue 
                          def_tag = "div"
                        autoclass=false
                        ptr = /^(\*)([^\d]+)([0-9]+)/
                        //    alert(coincidencia.length)
                        if(ptr.test(coincidencia[1])){ 

                           def_tag = coincidencia[1].match(/[a-zA-Z]/g);
                           n = coincidencia[1].match(/[0-9]/g);

                       //   alert(def_tag)
                       coincidencia[1] = def_tag.join("")+""+n.join("")
                       autoclass = def_tag.join("")+"_auto"
                       def_tag = def_tag.join("").toLowerCase()
                          }

                        coincidencia[2]  ?  coincidencia[2] = new Function('return ' + coincidencia[2])() : coincidencia[2] = {TAG:def_tag} 
                        adp[stack.length] =  addPanel(coincidencia[2]);
                        adp[stack.length].id = coincidencia[1]
                        if(autoclass){
                          adp[stack.length].className = autoclass
                            }

                        if (stack.length > 0) {
                        moveTag(adp[stack.length],adp[stack.length-1])
                        } else {
                        moveTag(adp[stack.length],document.body);
                        console.log("ID:"+element.id)
                        }

                        stack.push(element);
                      }

                      return output;
                    }

                    function parseLine(line) {
                      const match = line.match(/^(>+)(.+)/);
                      if (match) {
                        const depth = match[1].length;
                        const element = match[2].trim();
                        return [element, depth];
                      } else {
                        return [line.trim(), 0];
                      }
                    }

              const result = processVariable(input);
              console.log(result)
           }

      };

   const nuevoDocumento = document.implementation.createHTMLDocument();
   const body = nuevoDocumento.querySelector("body");
    // Asignar un ID al cuerpo del nuevo documento
    param ? body.id = param : body.id = "WFC3";
    // Crear un nuevo documento HTML en la página actual
    document.open();
    document.write(nuevoDocumento.documentElement.outerHTML);
    document.close();
    //return nuevoDocumento
    return obj;

};



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

var HTML = function(Doc){
HTMLX = document.createElement(Doc)
HTMLX.id="$".id=defId()
HTMLX.document = HTMLX.ownerDocument
HTMLX.ownerDocument.id = HTMLX.id
this.node = HTMLX.id
events(HTMLX.ownerDocument)
return HTMLX
}



var BODY = function(HTMLX=CLONE){

cb = document.createElement("body")
cb.id= $[nb] = "BODY_"+defIdBodys(nb)
HTMLX.append(cb.id)
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


openwins = Array()
nw = 0  ;

function htmlwin(inject="Inject Code",target,options=666){
(target?target:this.target)
this.open(`javascript:void(0);\``+inject+`\``,target,options);
this.document.close()
}



function newwin(inject="Inject Code",target,options=666){
(target?target:this.target)
win = this.open(inject,target,options);
this.document.close()
openwins[nw++] = {name:target,options:options,location:inject}
console.log(openwins[nw])
return win
}



function newwin2(inject="Inject Code",target,options=666){
(target?target:this.target)
this.open(`javascript:void(0);\``+inject+`\``,target,options);
this.document.close()
}



function domStyle(id,classx,style){

id.querySelectorAll(classx).forEach((elemento) => {
  elemento.style = style
});

}



function getRand(min, max) {
//  alert()
  return Math.random() * (max - min) + min;
}



function addStyle(css,id=""){
if(document.getElementById(id)) {console.log("css exists:",id);return;}
var css_fg1 = document.createElement("style");
css_fg1.type = "text/css";
if(id) css_fg1.id = id 
css_fg1.appendChild(document.createTextNode(css));
moveTag(css_fg1,xbody);

}






/* fdr*/

function display2(divid,classname){
rt = getId(divid).style.display
    var dcls=document.getElementsByClassName(classname);
    for(i=0;i<dcls.length;i++){
    if(dcls[i].id!==divid){
    disp = "none"
    dcls[i].style.display=disp
    cl = getId(dcls[i].id)
    cl.innerHTML = ""
    }else{
    disp = "block"
    dcls[i].style.display=disp
     }
   }
 return rt
}



// Variable global para asegurar que la función se ejecute una sola vez
var auto_liapp = 0; 

const loadIfApp = function(config) {
    // 1. Evitar ejecuciones duplicadas
    if (auto_liapp === 1) {
        console.warn("[Osiris loadIfApp] ⚠️ La función ya se ha ejecutado. Evitando una segunda ejecución.");
        return []; // Devolver un array vacío o lo que sea apropiado si ya se ejecutó
    }

    const userAgent = navigator.userAgent.toLowerCase();
    const loadedFiles = []; // Para almacenar los archivos que realmente se cargaron
    let debugMessages = []; // Para acumular mensajes de depuración

    // Función auxiliar para registrar mensajes de depuración
    const log = (message) => {
        debugMessages.push(`[Osiris loadIfApp] ${message}`);
        console.log(`[Osiris loadIfApp] ${message}`);
    };

    log(`Iniciando detección de navegador y carga de archivos. User-Agent detectado: ${userAgent}`);

    // Función auxiliar para cargar archivos (CSS o JS) dinámicamente
    const appendFile = (fileUrl, type, conditionName) => {
        if (typeof fileUrl === 'string' && fileUrl.trim() !== '') {
            if (type === 'css') {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = fileUrl;
                document.head.append(link);
                log(`Cargado CSS: '${fileUrl}' para '${conditionName}'`);
                loadedFiles.push({ type: 'css', file: fileUrl });
            } else if (type === 'js') {
                const script = document.createElement('script');
                script.src = fileUrl;
                script.type = 'text/javascript';
                script.defer = true; // Recomendado para que el script se cargue sin bloquear el parseo del HTML
                document.head.append(script);
                log(`Cargado JS: '${fileUrl}' para '${conditionName}'`);
                loadedFiles.push({ type: 'js', file: fileUrl });
            }
        } else {
            log(`Advertencia: URL de archivo inválida o vacía para tipo '${type}': '${fileUrl}'`);
        }
    };

    // Función que procesa la configuración de archivos para una condición dada
    const loadFilesForCondition = function(filesConfig, conditionName = 'Default') {
        if (!filesConfig) {
            log(`No hay archivos definidos en la configuración para la condición: '${conditionName}'.`);
            return;
        }

        // Manejar archivos CSS (puede ser un string o un array de strings)
        if (filesConfig.css) {
            const cssFiles = Array.isArray(filesConfig.css) ? filesConfig.css : [filesConfig.css];
            cssFiles.forEach(f => appendFile(f, 'css', conditionName));
        }

        // Manejar archivos JS (puede ser un string o un array de strings)
        if (filesConfig.js) {
            const jsFiles = Array.isArray(filesConfig.js) ? filesConfig.js : [filesConfig.js];
            jsFiles.forEach(f => appendFile(f, 'js', conditionName));
        }
    };

    // --- Definición de Patrones de Detección de Navegadores y Prioridad ---
    // El ORDEN es CRUCIAL. Los patrones más específicos deben ir PRIMERO.
    // Ej: Edge y Opera contienen "Chrome" en su User-Agent, por eso van antes que Chrome.
    // Móviles y Tablets se intentan detectar primero, antes de los navegadores de escritorio específicos.
    const browserDetectors = [
        // 1. Detección de dispositivos móviles y tablets (la más amplia y prioritaria)
        {
            name: 'Dispositivo Móvil/Tablet',
            regex: /(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|rim)|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino|ipad|playbook|silk/i,
            configKey: 'mobile'
        },
        // 2. Navegadores de escritorio específicos (ordenados por especificidad para evitar falsos positivos)
        {
            name: 'Microsoft Edge',
            regex: /(edge|edg)\//i, // 'Edge' para Edge Legacy, 'Edg' para Chromium Edge
            configKey: 'edge'
        },
        {
            name: 'Opera',
            regex: /(opera|opr)\//i, // 'Opera' para Presto, 'Opr' para Chromium Opera
            configKey: 'opera'
        },
        {
            name: 'Chrome',
            regex: /chrome\//i,
            configKey: 'chrome'
        },
        {
            name: 'Firefox',
            regex: /firefox\//i,
            configKey: 'firefox'
        },
        {
            name: 'Safari', // Este patrón es general y debe ir después de los basados en Chromium
            regex: /safari\//i, // Si incluye 'CriOS' o 'FxiOS' es Chrome/Firefox en iOS, no Safari puro.
                                // Para simplificar, asumimos que si no es de los anteriores y tiene 'Safari', es Safari.
            configKey: 'safari'
        },
        {
            name: 'Internet Explorer',
            regex: /(msie|trident)\//i, // 'msie' para IE < 11, 'trident' para IE 11
            configKey: 'ie' // Puedes usar 'msie' o 'ie' como key en tu config
        },
        // Puedes añadir más si necesitas, ej: 'samsungbrowser', 'ucbrowser', 'electron', etc.
    ];

    let matched = false;
    for (const detector of browserDetectors) {
        if (detector.regex.test(userAgent)) {
            log(`Intento de coincidencia: '${detector.name}' - User-Agent coincide.`);
            if (config[detector.configKey]) {
                log(`¡Coincidencia y configuración encontrada! Cargando archivos para: '${detector.name}' (Key: '${detector.configKey}')`);
                loadFilesForCondition(config[detector.configKey], detector.name);
                matched = true;
                break; // Detenerse en la primera coincidencia y carga exitosa
            } else {
                log(`Coincidencia para '${detector.name}', pero no hay una configuración definida con la key '${detector.configKey}'.`);
            }
        }
    }

    // 3. Si no se encontró ninguna coincidencia específica, cargar la configuración por defecto
    if (!matched) {
        log('No se detectó una configuración de navegador/dispositivo específica.');
        if (config.default) {
            log('Cargando configuración por defecto.');
            loadFilesForCondition(config.default, 'Default (No Match)');
        } else {
            log('Advertencia: No se encontró una configuración por defecto para cargar. Ningún archivo cargado.');
        }
    }

    // Marcar la función como ejecutada
    auto_liapp = 1; 

    log('--- Proceso de carga de archivos finalizado por loadIfApp ---');
    log('Archivos cargados con éxito:');
    if (loadedFiles.length > 0) {
        loadedFiles.forEach(f => log(`- Tipo: ${f.type.toUpperCase()}, URL: ${f.file}`));
    } else {
        log('- Ninguno.');
    }
    log('------------------------------------------------------------');

    return loadedFiles; // Devuelve la lista de archivos cargados para posible uso externo
};

// --- FIN DE LA FUNCIÓN loadIfApp ---



const AppScreenInfo = {
    // 1. Orientación de la pantalla (más ancho que alto o más alto que ancho)
    isLandscape: false, // true si es apaisado (ancho > alto)
    isPortrait: false,  // true si es vertical (alto > ancho)

    // 2. Rango de pantalla (para tu diseño responsivo, sin inferir dispositivo)
    // 'small', 'medium', 'large' - Puedes cambiar los nombres si quieres.
    screenSize: 'large', 

    // Puntos de quiebre (breakpoints) para los rangos de pantalla basados en el ANCHO
    // Puedes ajustar estos valores de acuerdo a tus necesidades específicas.
    responsiveBreakpoints: {
        smallMax: 767,   // Ancho hasta 767px (inclusive) = 'small'
        mediumMax: 1199  // Ancho hasta 1199px (inclusive) = 'medium'. Más = 'large'
    },

    // Variables adicionales para información detallada
    currentWidth: 0,
    currentHeight: 0,
    aspectRatio: 0,       // Relación Ancho / Alto
    hasTouch: false,      // true si el dispositivo tiene capacidad táctil

    // Función principal para actualizar toda la información de la pantalla
    updateScreenInfo: function() {
        this.currentWidth = window.innerWidth;
        this.currentHeight = window.innerHeight;
        this.aspectRatio = this.currentWidth / this.currentHeight;

        // --- Detección de Orientación (Nivel 1) ---
        // Usamos la Screen Orientation API si está disponible para mayor precisión
        if (screen.orientation && screen.orientation.type) {
            this.isPortrait = screen.orientation.type.startsWith('portrait');
            this.isLandscape = screen.orientation.type.startsWith('landscape');
        } else {
            // Fallback para navegadores antiguos o entornos sin la API
            this.isLandscape = this.currentWidth > this.currentHeight;
            this.isPortrait = this.currentHeight > this.currentWidth;
        }

        // --- Determinación del Rango de Pantalla (Nivel 2: Tres Puntos de Cambio) ---
        // Clasificamos el tamaño de la pantalla según los breakpoints definidos.
        if (this.currentWidth <= this.responsiveBreakpoints.smallMax) {
            this.screenSize = 'small';
        } else if (this.currentWidth <= this.responsiveBreakpoints.mediumMax) {
            this.screenSize = 'medium';
        } else {
            this.screenSize = 'large';
        }

        // --- Capacidad Táctil (información adicional, no para clasificación de rango) ---
        // Útil para adaptar interacciones (ej. "toca" vs "haz clic")
        this.hasTouch = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

        // --- Log en consola para depuración y visualización en tiempo real ---
        console.log('--- Estado de la Pantalla de Osiris Actualizado ---');
        console.log(`Ancho (Viewport): ${this.currentWidth}px, Alto (Viewport): ${this.currentHeight}px`);
        console.log(`Orientación: ${this.isLandscape ? 'Apaisada (Horizontal) ↔️' : 'Vertical (Retrato) ↕️'}`);
        console.log(`Rango de Pantalla: ${this.screenSize.toUpperCase()} 📏`);
        console.log(`Relación de Aspecto (Ancho/Alto): ${this.aspectRatio.toFixed(2)}`);
        console.log(`Capacidad Táctil Detectada: ${this.hasTouch ? 'Sí 👍' : 'No 👎'}`);
        console.log('-------------------------------------------');

        // Disparamos un evento personalizado para que otras partes de tu aplicación
        // puedan reaccionar a estos cambios de manera centralizada.
        document.dispatchEvent(new CustomEvent('AppScreenInfoUpdated', {
            detail: {
                isLandscape: this.isLandscape,
                isPortrait: this.isPortrait,
                screenSize: this.screenSize, 
                currentWidth: this.currentWidth,
                currentHeight: this.currentHeight,
                aspectRatio: this.aspectRatio,
                hasTouch: this.hasTouch
            }
        }));
    },

    // Función de inicialización para establecer los listeners
    init: function() {
        this.updateScreenInfo(); // Ejecuta la detección inicial al cargar la página

        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.updateScreenInfo();
            }, 200); // Pequeña demora para optimizar el rendimiento en redimensionado continuo
        });

        // Escucha cambios de orientación, muy importante para dispositivos móviles
        if (screen.orientation && screen.orientation.addEventListener) {
            screen.orientation.addEventListener('change', () => {
                this.updateScreenInfo();
            });
        }
        // Fallback para navegadores que no soportan la API moderna
        else if ('onorientationchange' in window) {
             window.addEventListener('orientationchange', () => {
                this.updateScreenInfo();
            });
        }
    }
};