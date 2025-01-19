document.write("<html><head></head><title>codedit</title><body>")
const code = function(value){
if(value=="") return ifCode.document.write(`<h3>No code</h3>`);
else {
ifCode.document.write("<hr>Ejecutando c&oacute;digo<hr>")+"\n"
return value;
}
}
var preScript = `\
\n\
<script>\n\
onerror = function(m,s,l,c,e){\n\
var msg = "\
msg: "+m+"<br>\
line: "+(l-9)+"\
&nbsp;&nbsp;\
col: "+c+"<br>\
"+s+"<br>\
"\n\
document.write(msg)\n\
}\n\
</script>\n\
\n\
\
`

var script = "<script>"
var _script = "</script>"


writeln(`\
\
<div style="width:100%;height:50%;margin:auto;border:solid 1px green;" id="G1">\
<div id='line'>\
<input \
type="button" \
value="exec" \
onclick=" if(getId('lang').value == 'javascript'){\
script = '<script>';\
_script = '</script>';\
} else if(getId('lang').value == 'html'){\
script = '';\
_script = '';\
} \
ifCode.open('about:blank','ifCode');\
ifCode.document.write(\`\`+preScript+\`\`+script+\`\`+code(getId('code').value)+\`\`+_script+\`\`);ifCode.document.close()"\
ifCode.document.close()"\
>\
<select name="lang" id="lang"><option value="html">HTML</option><option value="javascript" selected>JavaScript</option></select>\
</div>\
<textarea name="code" id="code" style="width:100%;height:100% ;padding:5px;">\
$1=\`helo\`\n\
document.write($1)\n\
alert(this)\n\
</textarea>\
</div>\
<div style="width:100%;height:50%;margin:0;border:solid 1px red;" id="G2">\
<iframe name='ifCode' style="border:0;width:100%;height:100%"></iframe>\
</div>\
\
`)

onload = function(){

getId('code').style.height =  getId('G1').offsetHeight - getId('line').offsetHeight


}




document.writeln("</body></html>")




