/* CPANEL*/


CPANEL = {

innerHTML:`<div style='text-align:center;margin:2px;padding:0;'><input type='button' onclick='if(confirm("¿Salir sin guardar?")){Active(HTML.DOC2)} else{alert("No disponible")}' value='Salir' style='font-weight:bold;color:#ac3ce6;'></div>`

}
 

/*ELEMENTS*/  

ELEMENTS = {style:"margin:0 auto 0 auto;width:95%;vertical-align:middle;text-align:center;"}


/*IMG_TAG*/

IMG_TAG = {TAG:'div',title:'Tag HTML <img>',draggable:"true",
innerHTML:`<div class="in_tags">IMG</div>`,
align:'center',name:'control_img',className:"elements_tags"}



IMG_TAG_DEF = {

TAG:"img",

src:"imgTag.png",

title:"Tag HTML <image>",

style:"transition:all 12s ease 0s;width:140px;height:90px;"


}


/*VIDEO_TAG*/

VIDEO_TAG = {TAG:'div',
title:'Tag HTML <video>',draggable:"true",align:"middle",
name:'control_video',comentario:"no",
innerHTML:`<div class="in_tags">VIDEO</div>`,
className:"elements_tags"
}



VIDEO_TAG_DEF = {

TAG:"video",

poster:"videoTag.png",
title: "Tag HTML <video>",
controls:"true",
currentTime:"0.01",
src:"https://vtwitt.com/jsa/media/video/er404.mp4",
style:"transition:all 6s ease 0s;width:220px;height:110px;",

}


DIV_TAG = {TAG:'div',draggable:"true",innerHTML:`<div class="in_tags">DIV</div>`,
title:'add DIV TAG',align:"middle",
name:'control_div',comentario:"ninguno",className:"elements_tags"}


DIV_TAG_DEF = {

TAG:"div",


contentEditable:"false",

innerHTML:"<b>DIV Editable</b>",

title:"Div Editable",

anidable:"ANIDE",

style:"transition:all 6s ease 0s;width:auto;height:auto;min-height:1px;"


}




CANVAS_TAG = {TAG:'div',draggable:"true",innerHTML:`<div class="in_tags">CANVAS</div>`,title:'add CANVAS TAG',align:"middle",name:'control:div',comentario:"ninguno",className:"elements_tags"}



CANVAS_TAG_DEF = {

TAG:"canvas",


contentEditable:"true",

innerHTML:"<b>CANVAS Editable</b>",

title:"Canvas editable",

style:"transition:all 6s ease 0ms;width:320px;height:90px;min-height:1px;"


}


IFRAME_TAG = {TAG:'div',draggable:"true",innerHTML:`<div class="in_tags">IFRAME</div>`,title:'add IFRAME TAG',align:"middle",name:'control_iframe',comentario:"ninguno",className:"elements_tags"}



IFRAME_TAG_DEF = {

TAG:"iframe",

scrolling:"auto",

contentEditable:"true",

innerHTML:"<b>IFRAME Editable</b>",

title:"Iframe editable",

style:"transition:all 6s ease 0s;width:320px;height:90px;min-height:1px;"


}


EMBED_TAG = {TAG:'div',draggable:"true",innerHTML:`<div class="in_tags">EMBED</div>`,title:'add EMBED TAG',align:"middle",name:'control:embed',comentario:"ninguno",className:"elements_tags"}



EMBED_TAG_DEF = {

TAG:"embed",


contentEditable:"true",

innerHTML:"<b>EMBED Editable</b>",

title:"Embed editable",

style:"transition:all 6s ease 0s;width:320px;height:70px;"


}


OBJECT_TAG = {TAG:'div',draggable:"true",innerHTML:`<div class="in_tags">OBJECT</div>`,title:'add OBJECT TAG',align:"middle",name:'control_object',comentario:"ninguno",className:"elements_tags"}



OBJECT_TAG_DEF = {

TAG:"object",


contentEditable:"false",

title:"HTML object Tag",

style:"transition:all 6s ease 0s;width:320px;height:70px;"


}




AUDIO_TAG = {TAG:'div',draggable:"true",innerHTML:`<div class="in_tags">AUDIO</div>`,title:'add audio TAG',align:"middle",id:'XDCDCDX',name:'control:audio',comentario:"ninguno",className:"elements_tags"}



AUDIO_TAG_DEF = {

TAG:"audio",



contentEditable:"true",
controls:"true",


title:"audio editable",

style:"transition:all 6s ease 0s;width:360px;height:50px;"


}


MARQUEE_TAG = {TAG:'div',draggable:"true",innerHTML:`<div class="in_tags">MARQUEE</div>`,title:'add marquee TAG',align:"middle",id:'XDCDCDX',name:'marquee:svg',comentario:"ninguno",className:"elements_tags"}



MARQUEE_TAG_DEF = {

TAG:"marquee",

innerHTML:"marquee HTML Tag",


contentEditable:"false",

title:"marquee editable",

style:"transition:all 6s ease 0s;width:360px;height:50px;"


}



A_TAG = {TAG:'div',draggable:"true",innerHTML:`<div class="in_tags">A</div>`,title:'add a TAG',align:"middle",id:'',name:'a_element',comentario:"ninguno",className:"elements_tags"}



A_TAG_DEF = {

TAG:"a",



contentEditable:"true",

title:"a editable",

style:"transition:all 6s ease 0s;width:360px;height:50px;"


}






/*EDITCONTROLS*/

EDITPROPERTIERS = ({TAG:"span",style:"max-width:100%;margin:0;padding:0;width:100%;"})

EDITCONTROLS = {TAG:"div",style:"position:absolute;width:100%;height:auto;border:solid 3px #12437a;margin:0px 10%  10%;padding:5px;display:none;top:0;font-size:16px;"}






/* GROUPPANEL	 */

GROUPPANEL = {}

/*WINEDIT*/


GROUPEDIT = {style:"background:#122553;padding:0px;width:100%;"}

IDEDIT = {innerHTML:`<div style='font-size:18px;font-family:arial;padding:10px;color:white'>Editor de Animaciones CSS JsAnimator <br>Versión: `+Version+`</div>
<center><iframe scrolling="no" src='media/records/today.html' frameborder="0" style="width:100%;height:320px" scrolling="false"></iframe></center>

`}

TIMELINE = {}



htmltxt =`\
\
<div id="closeme" style="clear:both;text-align:justify;font-size:16px;padding:0;background:#602360;height:auto">\
<a style='color:af3223;cursor:pointer;float:right;margin-right:25px;' onclick='getId("closeme").style.display="none"'><u><h4>CERRAR</h4></u></a>\
<p style="clear:both;font-weight:bold;color:#fcfcfc;padding:5% 10% 5% 10%;border:dashed 0px red;width:80%">Esta versión está en fase de desarrollo.<br>Borra los archivos temporales de internet. Para acceder a la última <br>versión<br>`+Version+`</p> \
<!--iframe frameborder='0' style="width:100%;height:auto;overflow:hidden" src="media/records/wew3.html"></iframe-->\
\
</div>\
\
`

WINEDIT = {innerHTML:``+htmltxt+``}




/*MENUPANEL*/

MENUPANEL = {}




/*WINPANEL*/

WINPANEL = {}

/* WORKWINFRAMES */ 

WORKWINFRAMES = {}


/*DEFWIN*/

DEFWIN = {TAG:'iframe',className:'iframes',src:"about:blank",style:"width:100%;max-width:100%,margin:0;",align:"center"}



/* GROUPWINDOWS */

GROUPWINDOWS = {TAG:'div',style:"background:#c4a1c2;width:100%;margin:0;height:23px;"}



/* GROUPIFRAMES */ 

GROUPIFRAMES = {}




js = `\
\
\
\
ret = newWindow("iframes")\n\
clickId("#"+ret.linker)\n\
\
\
\
`

LINKERIFRAMEWIN = {TAG:"button",innerHTML:"[+]",className:"botonMas",click:``+js+``}

NEWIFRAMEWIN = {TAG:"iframe",style:"display:none;border:solid 0.4% green;width:99.2%"}




MENU1 = {innerHTML:"",style:"border:solid 0px #facfce;color:red;background:#090913;margin:0;font-size:15px;font-weight:bold;text-align:left;"}



GROUPMENU1 = {style:"width:100%;background:#235234;"}


js = `

dmenu('IniWin','iframes');
/*newwin2(\`<a href="javascript:void(0);parent.ActiveWin=false;parent.dmenu('ProbeWin','iframes')">README</a>  <html><head></head><body></body></html>\`,'IniWin',0,1)*/

`


bs = "color:#1d1a25;background:#f6f6f6;margin:0px;font-size:15px;font-weight:bold;cursor:pointer;padding:0px 2px 0px 2px;border:solid 1px #ae9d9a;";

BOTON1 = {TAG:"a",innerHTML:"Inicio",click:""+js+"",type:"href",style:""+bs+""}



js = `
devwin(\`<script src=xhr.js></script><script src=testnet.js></script>\`)
`
BOTON2 = {TAG:"a",innerHTML:"Conectividad",type:"href",click:""+js+"",style:""+bs+""}

js = `\
\
\
\
ActiveWin=false\n\
dmenu('FileWin','iframes')\n\
\
\
\
`
BOTON3 = {TAG:"a",innerHTML:"Archivo",click:""+js+"",style:""+bs+""}

js = `\
\
\
\
devwin(\`<script src=wfcore.js></script><script src='code.js'></script>\`)\
\
\
\
`

BOTON4 = {TAG:"a",innerHTML:"CodEdit",click:""+js+"",style:""+bs+""}





CONTROLS = {

propertiers:{

animacion:"<units>",

autoplay:"<text>",

align:"<units>",


alt:"<text>",

allow:"<text>",
audioTracks:"<flex>",

behavior:"<flex>",

bgcolor:"<flex>",

border:"<flex>",

className:"<text>",

contentEditable:"<text>",
controls:"<text>",
contentDocument:"<textarea>",
contentWindow:"<textarea>",
crossOrigin:"<flex>",
csp:"<flex>",
currentSrc:"<flex>",
currentTime:"<flex>",
data:"<flex>",

defaultMuted:"<flex>",

direction:"<flex>",
duration:"<flex>",

draggable:"<text>",

disabled:"<text>",

ended:"<flex>",


featurePolicy:"<flex>",
fetchpriority:"<flex>",


frameBorder:"<units>",

height:"<units>",

hspace:"<flex>",

href:"<flex>",
id:"<units>",

innerHTML:"<textarea>",

loop:"<text>",

mediaGroup:"<flex>",

muted:"<text>",

poster:"<flex>",
preload:"<units>",


scrolling:"<flex>",

scrollAmount:"<flex>",

scrollDelay:"<flex>",

seekable:"<flex>",

setSkinId:"<flex>",

skinId:"<flex>",

src:"<flex>",

srcset:"<flex>",

target:"<flex>",
textTracks:"<flex>",

title:"<text>",

trueSpeed:"<flex>",

type:"<text>",


videoTracks:"<flex>",

volume:"<units>",

vspace:"<flex>",

width:"<units>"


}

,

styles: 

   {

animation:"<flex>",



animationDelay:"<flex>",
animationDirection:"<flex>",
animationDuration:"<flex>",
animationFillMode:"<units>",
animationIterationCount:"<units>",
animationName:"<units>",
animationPlayState:"<units>",
animationTimingFunction:"<units>",


animationDuration:"<flex>",

background:"<flex>",
backgroundColor:"<color>",
backgroundImage:"<flex>",
backgroundSize:"<flex>",
border:"<text>",
borderStyle:"<select>",
borderWidth:"<units>",
borderColor:"<color>",

bottom:"<units>",
clipPath:"<text>",
color:"<color>",
content:"<flex>",

display:"<select>",


fill:"<flex>",
float:"<units>",
getContext:"<units>",


filter:"<flex>",
flex:"<text>",


font:"<flex>",
fontFace:"<flex>",
fontFamily:"<flex>",
fontSize:"<units>",
fontWeight:"<units>",


height:"<units>",

left:"<units>",
letterSpacing:"<units>",
lineHeight:"<units>",
mask:"<flex>",
margin:"<text>",
marginLeft:"<units>",
marginRight:"<units>",
marginBottom:"<units>",
marginTop:"<units>",
marginInline:"<text>",

opacity:"<units>",
overflow:"<units>",
overflowX:"<units>",
overflowY:"<units>",

padding:"<text>",
paddingLeft:"<units>",
paddingRight:"<units>",
paddingBottom:"<units>",
paddingTop:"<units>",

perspective:"<flex>",

position:"<text>",

resize:"<units>",
right:"<units>",

textAlign:"<text>",

textDecoration:"<flex>",

textIndent:"<text>",
textShadow:"<flex>",

top:"<units>",
transition:"<flex>",
transform:"<flex>",
transformOrigin:"<text>",
transformStyle:"<text>",

verticalAlign:"<text>",
visibility:"<select>",
width:"<units>",
wordSpacing:"<units>",
zIndex:"<units>"
}

,

events: {

onclick:"<textarea>",

click:"<textarea>"

}


}





anidables = {

div:['div','span','video','audio','embed','object','br','hr'] ,
video:['source']

}


