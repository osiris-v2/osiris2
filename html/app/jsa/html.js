document.write("<!DOCTYPE html><html>")
document.write("<head>")
document.write("<title>")
document.write("winFrames")
document.write("</title>")
document.write("<meta charset='utf-8'>")
document.write("<meta name='lang' content='es,en'>")
document.write("<script src='wfcore.js'></script>")
document.write("<script src='head.js'></script>")
document.write("</head>")
document.write("<script src='zero.html.js'></script>")
nobody = `<div class="nobody"><b>Men&uacute; nobody</b><br>` + ` \
 <button onclick="\
 getId('iframe').style.width = '100%' ; display('A')\
\
\
\
\
  " style='position:fixed;top:0;left:0;boder:0;margin-left:0;border:solid 1px #e7f6e7;font-weight:bold;background:rgba(137,55,66,0.5)' >\
  &lt;&lt;  \
  </button>\
 ` + `<br>` +
location +  `<br>` +
document.body +  `<br>` +
window + `<br></div>` 
document.write(nobody)
document.write(`<body><div id='A' style='z-index:1;position:absolute;top:0;left:0;border:solid 1px 666600;background:rgba(99,78,99,0.4);display:none;'><button onclick='xpand(1);display("A")' style='background:rgba(255,255,255,0.5)'><b>&gt;&gt;</b></button></div>`)


document.write("<iframe name='iframe' src='index.html' style='background:#334433;float:right;position:fixed;right:0;top:0;height:100%;width:85%' id='iframe'></iframe>")
document.write("</body>")
document.write("</html>")



