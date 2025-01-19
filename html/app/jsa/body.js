document.write("<html><title>body.js</title><head><meta charset='utf-8'></head><body style='padding:0;margin:0;position:fixed;width:100%;height:100%;'>")
document.write(`\
\
\
\
`)
document.write(`\<div style="position:fixed;width:98%;height:98%;padding:1% 1%;overflow:auto;" id="xid"></div>
\
\
\
`)


document.write("</body></html>")
//lnecho(bold("DEBUG: "+DEBUG))
//lnecho(bold(document.body.id))


ajax("opt=how","xid","xhr.php","GET")

