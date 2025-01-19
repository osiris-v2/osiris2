//xnew = BODY()



s = loadIfApp("firefox",{css:"firefox.1.css"})
if(s) document.write(s) 

s = loadIfApp("chrome",{css:"chrome.1.css"})
if(s) document.write(s) 


//loadIfApp("chrome",{css:"chrome.styles.css"})


i = "i"
JS = `\
\
<input type='button' onclick='Active(DOC)' value='VOLVER A BODY Principal'>\
\
\
`

d2txt = {object:{object:``+JS+``}}

HTML.DOC2 = BODY();
HTML.DOC2.style = "width:80%;margin:0 auto 0 auto;background:#cfaed9;text-align:center;position:absolute;font-size:24px;width:95%;height:90%;margin:0;";
HTML.DOC2.id= "BODY_DOC2"



const xPANEL = createTag('div');
HTML.DOC2.append(xPANEL);
HTML.DOC2.title = HTML.DOC2.id
HTML.DOC2.innerHTML += "<h5 style='color:#4f931a;'>[ "+d2txt.object.object+" ]</h5>"


/*
DOC1 = BODY();
DOC1.style = "font-size:33px;width:95%;height:90%;margin:0;bottom:3px;right:3px;";
DOC1.id= "BODY_"+body.length
const xPANEL1 = createTag('div');
DOC1.append(xPANEL1);
DOC1.title = DOC1.id
*/

//console.log(HEAD)

control_tags = new Array()
count670749 = 0

const tag = function(tagx) {
if(!count670749) c = count670749 = 0
this.tag = tag
tag.info = "Object constructor"
tag.resource = createTag(tagx)
if(Reflect.defineProperty(this.tag, tagx, {
  value: ""+tag.resource+"",
  writable: false,
  length: ""+c+""
})) { 
c=count670749++
control_tags[c] = {resource:""+tag.resource+"",tag:""+tagx+""}
length = c.length
this.info = "TAGS CONTROLS"
//alert(r)
/*ERROR*/
 return tag.resource
} else {
tag.info = 'ERROR CREANDO INSTANCIA'+this
}
}





console.log(fin)

onload = function(){
/*
DefWin.resource = DefWin.contentDocument
dc = DefWin.resource
//alert(dc)
dc.body.style="background:red;"
dc.body.innerHTML ="<h1 style='color:#21da31;'> Js Winframes Framework JWF.jwf</h1>"
*/




tint = 5000
setInterval("clog()",tint);


dmenu('IniWin','iframes')


}
temp = 0
sum = 0
function clog(){
console.log('Temporizador onload <'+temp+":"+sum+" ms past>")
temp++
sum = temp * tint
}

//console.log(DefWin.contentDocument)
//console.log(WinPanel.childNodes)









