
MAINPANEL = {

TAG:"main",
className:"panel_principal",

}





INTRO_APP = {

TAG:"div",
innerHTML:`<h1>LOADING....</h1>`,
style:`display:flex;resize:both`

}



SPLASH = {


TAG:"button",
innerHTML:"Menú",
click:`document.getElementById('splash-container').style.display = 'block';`,



}


SPLASH_CONTAINER = {

TAG:"div"


}


SPLASH_CONTENT = {

TAG:"div",

innerHTML:`
<div style='border:solid 0px #dd3333;position:relative;padding:5vh;background:rgba(5,5,5,.4);display:inline-block'>
<button type="button" class='mbuton' onclick="document.getElementById('iftvx2').src='tv/player2.php?chn=../channels/main/live-ts/master_ultrafast.m3u8'">Osiris TV</button>
<button type="button" class='mbuton' onclick="document.getElementById('iftvx2').src='https://osiris000.duckdns.org/app/widgets/hlstv.html'">WdTV</button>
<button type="button" class='mbuton' onclick="document.getElementById('iftvx2').src='tv/app.php'">Canales Tv</button>
<button type="button" class='mbuton' onclick="document.getElementById('iftvx2').src='../freedirectory/video/cartelera.php'">Cartelera</button>
<button type="button" class='mbuton' onclick="document.getElementById('webirc-container').style.display='block';document.getElementById('webirc-container').style.visibility='visible';"> IRC - Chat </button>
</div>
`,
style:"width:auto;display:block;"

}


CLOSE_SPLASH = {

TAG:"button",
innerHTML:`<button onclick="document.getElementById('splash-container').style.display = 'none';" style="color:#a93333;margin:0.5vw">[Cerrar]</button>`,
click:`document.getElementById('splash-container').style.display = 'none';`,
className:`mbuton`
}
