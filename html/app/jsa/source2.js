HELPhtml = "<h3>Hhtml</h3>"

HTML.DOC2.innerHTML +=  "\
\
\
\
<p style='font-weight:bold'>\
\
IdCreator Versi&oacute;n:\
"+Version+"\
<i style='color:red;'>\
\
</i>\
</p>\
\
<style>\
\
a.z{margin:10px;font-size:15px;font-weight:bold;text-decoration:none;} \
\
</style>\
\
<br>\
<a onclick='javascript:newwin2(`<script>location.href=\"README\"</script>`,`README`,`width="+screen.width/1.5+",height="+screen.height/1.5+",0,0,0`);' class='z' style='cursor:pointer;color:#0000ff;text-decoration:underline;'>\
README\
</a>\
\
<a href='javascript:void(0)' onclick='alert(`XHR Conection`)' class='z'>Compobar Actualizaciones</a> \
<a href='javascript:void(0)' onclick='alert(`Online Support`)' class='z'>Soporte Online</a>  \
\
\
"

ESTEx = false;

HTML.DOC2.innerHTML += " <h4>Opciones de Inicio - Winid HTML/Frames</h4> \
<a href='javascript:newwin(`<script src=html.js></script>`,this.name)'>\
<b style='font-size:21px;'>Nuevo WinIframes</b>\
</a>\
<input type='button' onclick='location.reload()' value='Editor' \
 style='margin:5px;font-size:28px;left:33px;top:36px;bottom:10px;'> \
<input type='button' onclick='alert(`onDev`);return true;if(ESTEx) {ESTEx.remove() }; \
ESTEx = addPanel(\"div\",\"beforebegin\",xPANEL,HELPhtml); \
ESTEx.style.fontSize=\"18px\";' onmouseover='events(this)' id='INTERTAG' \
 value='HELP' style='margin:5px;font-size:28px;'> "
 
 
 

