

onload = function (){

document.write(`
<!DOCTYPE html><html><head><title>net.js</title></head><body class='windows' id='`+this.name+`'  style='position:absolute;transition:all 6s;width:100%;height:100%;margin:0;overflow:auto'>\
\
\
`)


parent.debug("Loaded net.js")


if(parent.ad.length) td = parent.ad.length 
else td = 0;




parent.ad[td] = document.body
parent.ad[td].id = td
parent.ad[td].tag = "body"
parent.ad[td].win = this.name
parent.ActiveWinName = this.name
parent.ActiveWin = this.document.body




document.write(`</body></html>`)


parent.listTags(this,parent.ActiveWinId)

internalsgen = parent.internalsgen
parent.idEdit(td,parent.EditPropertiers,parent.CONTROLS,internalsgen)
parent.internalsgen++
}

parent.debug("Loading net.js")



