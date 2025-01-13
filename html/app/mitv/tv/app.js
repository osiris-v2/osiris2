/* Carga js externos */
var script = document.createElement("script");
script.src = "//cdn.jsdelivr.net/npm/hls.js@latest"

//script.src = "https://compostela21.com/ydl/hls.js/dist/hls.js" 
script.type = "text/javascript"
document.head.append(script)


/*App*/
var script = document.createElement("script");
script.src = "source.js"
script.type = "text/javascript"
document.head.append(script)
