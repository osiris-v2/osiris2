document.write("<html><head><title>WorkSys</title></head><body>")



//echo("TEXTO") - escribe en body con innerHTML

defEcho = "undefined"

const echo = function(value=defEcho){
document.body.innerHTML += value
}

const debug = function(value="undefined value",debug=0){
if(debug) console.log(value)
}

const echoln = function(value=defEcho){
document.body.innerHTML += value + "<br>"
}

const lnecho = function(value=defEcho){
document.body.innerHTML += "<br>" + value
}

document.write("<script src=zero2.js></script>")


debug(echo("<h2>DEBUG</h2>"),1)


js = `\
\
\
jwl   = open("loadwinframes.html","jwl","width="+screen.width+",height="+screen.height+",0,0,0,0");\
\
\
`

echoln ("<a href='javascript:void(0);`<script>"+js+"</script>`'>Aplicaci&oacute;n</a>","+")

//echo ("<a href='javascript:void(0);`<script src=work.js></script>`'>ReCarga</a>")
//alert()

defTag = "div"

const genTag = function(tag){

if(!tag) tag = defTag


}



//$ = `innerHTML`



//document.body.$ = "XIMER"



