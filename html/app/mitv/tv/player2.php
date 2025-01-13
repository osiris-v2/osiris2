<html><head><title>Tv Online HLS</title>
        <head>



<meta name="viewport" content="width=device-width, initial-scale=1.0">


            <style type="text/css">
    body{
        margin:0;padding:0;
        overflow:hidden;
    }
    
#splay,    #loadingText {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
  font-size: 20px;
  color: white;
  background-color: rgba(0, 0, 0, 0.7);
  padding: 10px 20px;
  border-radius: 5px;
}
    
    
    .actualizacion-tiempo-real {
  display: inline-block;
  padding: 0.36%;
  background-color: #fff;
  border: 1px solid #ddd;
  font-size: 79%;
  font-weight: bold;
  color: #333;
  border-radius: 6px;
  box-shadow: 0 1.2% 0.8% 0 rgba(0, 0, 0, 0.2);
  animation: fadein 1s ease-out;
}

@keyframes fadein {
  from { opacity: 0; }
  to   { opacity: 1; }
}

    
 #fullscreen-button {
 z-index:66;
  position: absolute;
  top: 10px;
  right: 10px;
  width: 45px;
  height: 45px;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s ease-in-out;
  background: transparent;
}

#fullscreen-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 30px;
  height: 30px;
  border-top: 10px solid white;
  border-right: 10px solid white;
  border-bottom: 10px solid transparent;
  border-left: 10px solid transparent;
}







#fullscreen-button::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 10px;
  height: 10px;
  border-top: 20px solid white;
  border-right: 20px solid white;
  border-bottom: 20px solid transparent;
  border-left: 20px solid transparent;
}   



/* botones play pause */

.ppb{

display:inline-block;

 border-radius: 5px;
 
width:32px;height:32px;margin:10px 1px 0.2px auto;padding:2px;

background:rgba(240,220,220,0.6);
}
    
    
   #controls-container {
   
   
  display: none;
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  color: #fff;
  padding: 5px;
  box-sizing: border-box;
  height:75px;
}

#play-pause-button {
float:left;
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  padding:4.3px 1px 3px 5px;

  display:inline-block;
  width:32px;height:32px;
}






#progress-bar-container, #volume-container {
  display: inline-block;
  margin-right: 10px;
}

#progress-bar-container {
  width: 50%;
}

#progress-bar, #buffer-bar {
  height: 5px;
  background-color: #fff;
}

#buffer-bar  {
opacity: 0.3;
}
 #progress-bar {
  opacity: 0.5;
}
#time-display {

font-size:12px;
font-family:"comic sans ms";
width:auto;
float:right;
  display: inline-block;
  margin: 28px 10px auto auto;
}

 #mute-unmute-button {
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  margin:3px 5px 0 5px;
  display:inline-block;
  width:30px;height:30px;
}

#volume-container {
float:left;
display:inline-block;
  position: relative;
}


#volume-bar-container {

cursor:pointer;
display:inline-block;
  position: absolute;
  top: 31px; 
  left: 47.5px;
  transform: translateY(-50%);
  width: 160px;
  height: 7.5px;
  background-color: rgba(225,212,250,0.5);
  border:solid 1px  background-color: rgba(255,222,0,0.8);
  border-radius: 2px;
}



#volume-bar {
  position: absolute;
  top: 0px;
  display:inline-block;
  left: 0;
  width: auto;
  height: 7.5px;
  background-color: rgba(20,250,6,0.4);
  border-radius: 2px;
  cursor: pointer;
}

#volume-bar::before {
  content: "";
  position: absolute;
  top: 5px;
  left: 70%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
/*  border-top: 8px solid transparent;
  border-bottom: 8px solid transparent;
  border-left: 8px solid #333;*/
}

#volume-bar::after {
  content: attr(data-volume);
 position: absolute;
  top: -1.1px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 8px;
  font-family:arial;
  color: #333afa;
}









 #progress_c {
 
width:auto;
/*max-width:80%;*/
position:absolute;

overflow:hidden;
 display:inline-block;
  height: 6px;
  
  background-image: linear-gradient(to right, red 0%, green 100%);
}






.pantalla {
  position: relative;
  width: 360px;
  height: 240px;
  margin: 0 auto;
  border: 1px solid #000;
  background-color: rgba(0, 0, 0, 0.3);
}

.fondo {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: linear-gradient(to bottom right, #33ccff, #ff99cc);
  opacity: 0.3;
}

.boton-play {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background-color: rgba(25, 255, 25, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s;
}

.boton-play:hover {
  transform: scale(1) translate(-50%, -50%);
}

.boton-play svg {
  width: 60px;
  height: 60px;
  fill: #333;
}





          
</style>
 <meta name="viewport" content="width=device-width, initial-scale=1.0">

<script src="https://cdn.jsdelivr.net/npm/hls.js@1.1.4/dist/hls.min.js"></script>

<!--script src="https://www.vtwitt.com/hls.js/dist/hls.js"></script-->
<script type="text/javascript" src="https://www.compostela21.com/tec/ajax/lib/hxr.js"></script>
        </head>
        <body>
        
        
        
        
        
            <div id="prueba"></div>

 <div style="position:relative;text-align:center;width:100%;height:auto;max-width:100%;margin:0 auto 0 auto;font-size:18px;font-family:'gill sans';font-weight:700;overflow:hidden"
 
 id="video-container"
 >


<video id="video" poster="https://vtwitt.com/img/connecting-loading.gif" style="margin:0;height:70%;width:100%;max-width:100%;background:#000;" class="skin" preload="metadata" controls loop
autoplay></video>





<div id="loadingText">




<svg width="100%" height="100%" viewBox="0 0 500 500" style="max-width:65%;max-height:65%;">
  <defs>
    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF0000" />
      <stop offset="50%" stop-color="#FFA500" />
      <stop offset="100%" stop-color="#FFFF00" />
    </linearGradient>
    <mask id="mask">
      <rect width="100%" height="100%" fill="white"/>
      <circle cx="50%" cy="50%" r="100">
        <animate attributeName="r" from="100" to="200" dur="1s" repeatCount="indefinite"/>
      </circle>
    </mask>
  </defs>
  <rect width="100%" height="100%" fill="#222" fill-opacity="0.1" />
  <circle cx="50%" cy="50%" r="150" fill="url(#gradient)" mask="url(#mask)">
    <animateTransform attributeName="transform" type="rotate" from="0 250 250" to="360 250 250" dur="2s" repeatCount="indefinite"/>
  </circle>
  <text x="50%" y="50%" fill="#FFF" font-size="22" font-weight="bold" text-anchor="middle" alignment-baseline="middle">
    <tspan>Cargando</tspan>
    <animate attributeName="fill" values="#FF0000;#FFA500;#FFFF00;#FFA500;#FF0000" dur="2s" repeatCount="indefinite" />
    <animate attributeName="letter-spacing" values="0 1 2 1 0" dur="2s" repeatCount="indefinite" />
    <animate attributeName="opacity" values="1;0;1" dur="2s" repeatCount="indefinite" />
  </text>
</svg>



</div>



<div id="splay" style="display:none;">
<div class="pantalla">
  <div class="fondo"></div>
  <div class="boton-play" onclick="video.play()" style="cursor:pointer;">
    <svg viewBox="0 0 60 60">
      <polygon points="20,15 45,30 20,45" />
    </svg>
  </div>
</div>
</div>




<div id="controls-container">



<div id="fullscreen-button" title="Pantalla Completa"></div>

<div id="progress-container"><div id="progress-bar"></div></div>



<div style="justify-content:center;align-items:center;display:flex;overflow:hidden;margin:25.8px 30px auto auto;float:right;">

<div id="buffer-container"><div id="buffer-bar"></div></div>
&nbsp;&nbsp;
  <a  href="javascript:void(0)" 
  onclick="xplayer(`<?=$_REQUEST["chn"]?>?&nocache=<?=$nocacherand?>&`)">
  <img src="img/reload.png" style="width:201x;height:20px;"></a>
&nbsp;&nbsp;&nbsp;

  <a href="javascript:void(0);" onclick="document.getElementById('video').style.height='70%';document.getElementById('m').style.display='block'; document.getElementById('webirc').style.display='none';"   style="padding:0px 3px;color: #333; text-decoration: none; border: 1px solid #333; margin:0;; border-radius: 10px; animation:fadeIn 0.5s ease-in-out; -webkit-animation-fill-mode: forwards;background:rgba(222,222,222,0.6)"> Consola </a>


</div>



      
<div id="play-pause-button"></div>

<div id="volume-container">
    <button id="mute-unmute-button"></button>
    <div id="volume-bar-container">
      <div id="volume-bar"></div>
   </div> 
</div>

<div id="time-display"></div>



</div>



</div>




 <div id="m" style="height:28.7%;padding:1.3%;background:rgba(11,11,11,0.7);overflow:hidden;display:inline-block;width:90.7%;">
 

  <div style="position:relative;z-index:666;transform:translate(1%,-5%);background-color:#fff;padding:0px;border-radius:1px;display:inline-block;padding:10px;overflow:hidden;">
   <a href="javascript:void(0);" onclick="document.getElementById('m').style.display = 'none';
                     document.getElementById('video').style.width = '100%';
                     document.getElementById('video').style.height = '100%';
                     " style="display: block; text-align: center; font-weight: bold; margin-top: 5px; color: #fff; font-size:16px; background-color: #333; padding: 5px 10px; border-radius: 5px; text-decoration: none;">Cerrar</a>
 
 </div>
 
 
<span style="font-size:3.5vh;font-weight:bold;color:#de3444;margin:18px;"> Consola </span>

 <div id="progress_c"></div>
 
 
<!--div id='quality-selector'></div-->
 
</div>

 
 <script type="text/javascript">
 













  
var m3u8=1;   

    <?php
   if($_GET["chn"]){
    
    
       
     $chn =  " \n canal = '{$_GET['chn']}' \n ";
   }    else $chn = "\n canal = 'https://tv.vtwitt.com/mitv/live/canal1.m3u8' \n ";
   echo $chn;
   ?>
       
var videoSrc = canal;


mid = document.getElementById('m');

function log(d,nd="",p=0){


if(mid.style.display=="none") return

id = document.getElementById(nd)

if(!id){

cte = document.createElement("div")
cte.id = nd
cte.style.display = "inline-block" 
cte.className = "actualizacion-tiempo-real"
mid.append(cte)
id = document.getElementById(nd)
}

if(p<1){
if(/[0-9]/.test(d)){
  d = d.replace(/([0-9]+\.?[0-9]*)/, (match, p1) => parseFloat(p1).toFixed(4));
}
}

id.innerHTML = d

}







var mut = `<svg viewBox="0 0 60 60" class="ppb"  style="padding-right:5px;">
  <circle cx="30" cy="30" r="25" fill="none" stroke="#999" stroke-width="4" stroke-opacity="0.9" />
  <rect x="10" y="15" width="10" height="30" rx="2" ry="2" fill="#666" />
  <rect x="22" y="10" width="10" height="40" rx="2" ry="2" fill="#666" />
  <rect x="34" y="5" width="10" height="50" rx="2" ry="2" fill="#666" />
  <rect x="46" y="0" width="10" height="60" rx="2" ry="2" fill="#666" />
</svg>`

var vol = `<svg viewBox="0 0 60 60" class="ppb" style="padding-right:5px;">
  <circle cx="30" cy="30" r="25" fill="none" stroke="#999" stroke-width="4" stroke-opacity="0.1" />
  <rect x="10" y="15" width="20" height="30" rx="2" ry="2" fill="none" stroke="#666" stroke-width="4" stroke-opacity="1" />
  <rect x="22" y="10" width="20" height="40" rx="2" ry="2" fill="none" stroke="#666" stroke-width="4" stroke-opacity="1" />
  <rect x="34" y="5" width="20" height="50" rx="2" ry="2" fill="none" stroke="#666" stroke-width="4" stroke-opacity="1" />
  <rect x="46" y="0" width="20" height="60" rx="2" ry="2" fill="none" stroke="#666" stroke-width="4" stroke-opacity="1" />
</svg>` 



var b_play = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 30" class="ppb">
  <circle cx="15" cy="15" r="15.5" fill="#4CAA50"/>
  <path d="M11.25 21.375l10.125-6.75L11.25 7.875v13.5z" fill="#FFF"/>
</svg>`

var b_pause = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 30" class="ppb">
  <circle cx="15" cy="15" r="15.5" fill="#f4a336"/>
  <rect x="10.5" y="8.25" width="2.25" height="13.5" fill="#FFF"/>
  <rect x="17.25" y="8.25" width="2.25" height="13.5" fill="#FFF"/>
</svg>`






var loadingText = document.getElementById("loadingText");
const controlsContainer = document.getElementById("controls-container");
const playPauseButton = document.getElementById("play-pause-button");
const progressBar = document.getElementById("progress-bar");
const bufferBar = document.getElementById("buffer-bar");
const timeDisplay = document.getElementById("time-display");
const muteUnmuteButton = document.getElementById("mute-unmute-button");
const volumeBarContainer = document.getElementById("volume-bar-container");
const volumeBar = document.getElementById("volume-bar");

playPauseButton.innerHTML = ''+b_play+'';
muteUnmuteButton.innerHTML = ''+vol+'';       


video = document.getElementById("video");

function xplayer(videoSrc){



if (Hls.isSupported()) {
  
var hls = new Hls(hlsConfig);
 
interval = false ;
var retry_time = 0 ;
var bufferSize = 0;
var elapsedTime = 0;
let counter = 0;
video.currentTime = 0;
var  currentTime = video.currentTime;
            
            
  hls.loadSource(videoSrc+"?"+Date.now());
  hls.attachMedia(video);
  hls.on(Hls.Events.MEDIA_ATTACHED, function () {
  video.muted = false;
  video.play();
});

/*Parse Manifest*/

 hls.on(Hls.Events.MANIFEST_PARSED, function () {
            
  var levels = hls.levels;
  var currentLevel = hls.currentLevel;
  for (var i = 0; i < levels.length; i++) {
    var level = levels[i];
    var option = document.createElement('option');
    option.value = i;
    option.text = level.width + 'x' + level.height + ' ' + (level.bitrate / 1000) + 'kbps';
    if (i == currentLevel) {
      option.selected = true;
    }
   log(option.text+"|"+hls.levels.length,"Q",1)
   console.log(option.text+"|"+hls.levels.length,"Q",1)
  }

 document.getElementById('quality-selector').addEventListener('change', function() {
    var selectedLevel = parseInt(this.value);
    hls.currentLevel = selectedLevel;
    log("["+selectedLevel+"]","q2")
  });
        video.play();
});
            
            

/*Manejo de Errores*/

hls.on(Hls.Events.ERROR, function(event, data) {
  if (data.type === Hls.ErrorTypes.NETWORK_ERROR && data.details === Hls.ErrorDetails.MANIFEST_LOAD_ERROR) {
    console.log('Error cargando el manifiesto');
  } else if (data.type === Hls.ErrorTypes.NETWORK_ERROR && data.details === Hls.ErrorDetails.LEVEL_LOAD_ERROR) {
    console.log('Error cargando el nivel');
  } else if (data.type === Hls.ErrorTypes.NETWORK_ERROR && data.details === Hls.ErrorDetails.FRAG_LOAD_ERROR) {
  
    console.log('Error cargando el fragmento');
    console.log('Segmento que falló:', data.frag.url);
// hls.startLoad()
  }


  if (data.fatal && data.type === Hls.ErrorTypes.NETWORK_ERROR && data.details === Hls.ErrorDetails.FRAG_LOAD_ERROR) {
    console.log('El reproductor está en bucle debido a un error de carga de segmentos.');
  }

  if (data.fatal) {
    switch(data.type) {
        case Hls.ErrorTypes.NETWORK_ERROR:
          console.log("HLS network error");
          break;
        case Hls.ErrorTypes.MEDIA_ERROR:
         // console.log("HLS media error: ", data.details);
          break;
        default:
          console.log("HLS error: ",data.details);
          break;
          }
      if (data.frag && data.frag.url) {
        console.log("HLS frag url: " ,data.frag.url);
      }
      //console.log("HLS error details: " , data);
    }


 });



/* continue*/


      
            video.addEventListener('canplay', function () {
                log("Actualizar la interfaz de usuario","PLAY")

if(video.paused){
  document.getElementById("splay").style.display = "block"
} else {

document.getElementById("splay").style.display = "none"
}

            });
            video.addEventListener('progress', function () {
                log("progress","PROGRESS")
            });
            
            
            video.addEventListener('ratechange', function () {
                log("ratechange","RATECHANGE")
            });
            
            video.addEventListener('loadeddata', (event) => {
                log("loaded data","LOADEDDATA")
            });
            
            addEventListener('emptied', (event) => {
            
            log("Empty","EMPTIED")
            
            
            });
            
            
 
            
              hls.on(Hls.Events.MEDIA_BUFFER_EMPTY, function() {
          log("EmptyBuffer","ERROR");
          
        });

const fullscreenButton = document.getElementById('fullscreen-button');


fullscreenButton.addEventListener('click', () => {
  if (video.requestFullscreen) {
    video.requestFullscreen();
  } else if (video.webkitRequestFullscreen) {
    /* Safari */
    video.webkitRequestFullscreen();
  } else if (video.msRequestFullscreen) {
    /* IE11 */
    video.msRequestFullscreen();
  }
});

         
         
       
         
 
/* time update */



            up = 0;
    video.addEventListener('timeupdate', (event) => {
            up++  ;
  log('Update:'+up,"TIMEUPDATE");
 currentTime = video.currentTime;

    checkBuffer(video)
    
    log("UPG:"+updateProgress(counter) ,"Crash")
   
  if(counter>120)   location.reload()
  
 
 
log("Current:"+currentTime,"currentTime")

retroceso = 8

  if (video.buffered.length > 0 && (currentTime > (retroceso))) {
    
    log("RT:"+(currentTime )+":"+ (retroceso * 3),"ERROR")
    
    
    var bufferEnd = video.buffered.end(video.buffered.length - 1);
    
    log("Length: "+video.buffered.length,"BUFFER")
     log("Length: "+bufferEnd,"BUFFER")
    
    var bufferTime = bufferEnd - currentTime;
   
  
    // Verificar si el tiempo restante en el búfer es suficiente para retroceder 5 segundos antes de que la línea de tiempo se pare
    if ((bufferTime < 0.5)) {
    
       loadingText.style.display = "none";
      log("ajuste: "+(bufferTime + (retroceso / currentTime) ) ,"AJUSTE-DE-BUFFER");
     
     // hls.refreshManifest();

 
  //setTimeout(function(){   hls.startLoad()},1000)

   
    //   video.currentTime =   bufferEnd  - (retroceso)
    
     // hls.loadSource(videoSrc);
    
        log("X-Time "+currentTime+":"+video.currentTime+":"+bufferEnd ,"AJUSTE-DE-BUFFER_");
    
  //  hls.flushBuffer();
     
     // hls.loadSource();
    
      
      //(currentTime - (retroceso/1.7));
    } 
   
  }

  
  
  

// Update progress bar and time display on timeupdate event


if (video.buffered.length > 0) {
   currentTime = video.currentTime;
   duration = video.duration;
   buffered_ = video.buffered.end(0);
   progressPercentage = (currentTime / duration) * 100;
   bufferPercentage = (buffered_ / duration) * 100;
  progressBar.style.width = progressPercentage + "%";
  bufferBar.style.width = bufferPercentage + "%";
  timeDisplay.innerHTML = formatTime(currentTime) + " / " + formatTime(duration);
  }
  



  
  
  });
    
    

  
  
  
  
  
   video.addEventListener('crash', (event) => {
  
    
    
    
    
    
      log("<b style='color:red'>Crash</b>","PLAY")

loadingText.style.display = "block";
  
  });
  
  
  
         
   video.addEventListener('playing', (event) => {
  
    
    
    document.getElementById("splay").style.display = "none"
    
    
      log("Playing","PLAY")

loadingText.style.display = "none";
//  video.poster = "https://vtwitt.com/img/connecting-loading.gif";

  
  });
     
        
     
video.addEventListener("waiting", function() {
  video.poster = "";
 // loadingText.style.display = "block";
});

      
        
            
            video.addEventListener('loadedmetadata', function () {
              
              playVideo(video)
              
                log("Loaded metadata","LOADEDMETADATA")
            });
            
            
         
        
         
 video.onloadedmetadata = function() {
        console.log("Duración del video: " + video.duration + " segundos");
        retry_time = video.duration
      };
      
      
hls.on(Hls.Events.BUFFER_APPENDED, function(event, data) {
 
 counter = 0
  log('Buffer appended',"BUFFER");
  
  
  

});



let bufferEmpty = true;
const bufferEmptyTimeout = setTimeout(() => {
  if (bufferEmpty) {
    console.log('El reproductor está en bucle debido a un problema con el buffer de video.');
  }
}, 20000);

hls.on(Hls.Events.BUFFER_APPENDED, (event, data) => {
  if (video.buffered.length === 0) {
    bufferEmpty = true;
  } else {
    bufferEmpty = false;
  }
});









if(interval) { clearInterval(interval) ; interval = false ;}

if(!interval) {

// Crea un intervalo que se ejecute cada segundo
interval = setInterval(function() {
  // Obtén la tasa de datos del buffer del reproductor
  // const rate = video.buffered.length;
 
 
 if(video.buffered.length>0){
 
 
 
  var rate = (video.buffered.end(0) - bufferSize) ;
  // Actualizar el tamaño del buffer y el tiempo transcurrido
  bufferSize = video.buffered.end(0);
  elapsedTime = 1;

  // Si no hay datos en el buffer, aumenta el contador
  if (rate <= 0) {
    counter++;
    log("RATE:"+rate,"RATE")
      } else {
    
    log("RATE:"+rate,"RATE")
    // Si hay datos en el buffer, reinicia el contador
    counter = 0;
  }

  // Si no hay datos en el buffer durante 20 segundos, lanza una excepción
  if ((counter) >  ( 2 *  (retry_time / 1.5 ))) {
  
 
    log("Xtime","RATE");
  counter = 0 ;

//location.reload()

 hls.startLoad();



 //xplayer(videoSrc)


//  location.reload();
//  hls.loadSource(videoSrc);
// video.refreshManifest();
  } else if(( counter) >  3.5 * (retry_time / 1.2)) {log("Retry:"+counter+":"+retry_time,"RETRY") ; /*hls.startLoad();*/ }
 } else {log("X-Retry:"+counter,"RETRY") ;}
}, 10000);


}



 
let isMuted = false;

let timerId;

controlsContainer.addEventListener("mouseenter", function() {
  controlsContainer.style.display = "block";
/*  volumeBarContainer.style.display = "inline-block";*/
  clearTimeout(timerId);
});

controlsContainer.addEventListener("mouseleave", function() {
  timerId = setTimeout(function() {
    controlsContainer.style.display = "none";
/*    volumeBarContainer.style.display = "none";*/
  }, 1000);
});


video.addEventListener("mouseout", function(event) {

  controlsContainer.style.display = "none";
  /*  volumeBarContainer.style.display = "none";*/

});

video.addEventListener("mousemove", function(event) {
  const videoRect = video.getBoundingClientRect();
  if (event.clientX >= videoRect.left && event.clientX <= videoRect.right &&
      event.clientY >= videoRect.top && event.clientY <= videoRect.bottom) {
    controlsContainer.style.display = "block";
 /*   volumeBarContainer.style.display = "inline-block";*/
    clearTimeout(timerId);
  } else {
    timerId = setTimeout(function() {
      controlsContainer.style.display = "none";
      /*volumeBarContainer.style.display = "none";*/
    }, 1000);
  }
});






// Play/pause video on click
playPauseButton.addEventListener("click", function() {
  if (video.paused) {
    video.play();
    playPauseButton.innerHTML = ''+b_pause+'';
  } else {
    video.pause();
    playPauseButton.innerHTML = ''+b_play+'';
  }
});

// Mute/unmute video on click
muteUnmuteButton.addEventListener("click", function() {
  if (isMuted) {
    video.muted = false;
    isMuted = false;
    muteUnmuteButton.innerHTML = ''+mut+'';
  } else {
    video.muted = true;
    isMuted = true;
    muteUnmuteButton.innerHTML = ''+vol+'';
  }
});





// Check if volume is not blocked and set muted accordingly
video.addEventListener("loadedmetadata", function() {
  if (video.muted) {
    isMuted = true;
    muteUnmuteButton.innerHTML = ''+vol+'';
  } else {
    video.muted = false;
    isMuted = false;
    muteUnmuteButton.innerHTML = ''+mut+'';
  }
});



    function updateProgress(n) {
  const progressElement = document.getElementById("progress_c");
  progressElement.style.width = n * 4.97 + "%";
  progressElement.style.overflow = "hidden";
  return  counter
}






// Format time in mm:ss format
function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return minutes + ":" + (remainingSeconds < 10 ? "0" : "") + remainingSeconds;
}



// Cambiar el botón de play/pause automáticamente
video.addEventListener("play", function() {
  playPauseButton.innerHTML = ''+b_pause+'';
});

video.addEventListener("pause", function() {
  playPauseButton.innerHTML = ''+b_play+'';
});
   
   
   
   
   
   // vinculamos la barra de volumen con el elemento de video
video.addEventListener("volumechange", () => {
  const currentVolume = Math.round(video.volume * 100);
  volumeBar.style.width = currentVolume + "%";
  volumeBar.setAttribute("data-volume", currentVolume);
});

// hacemos que la barra de volumen inferior sea clickeable y cambie el volumen
volumeBarContainer.addEventListener("mousedown", (event) => {
  const volumeBarWidth = volumeBarContainer.clientWidth;
  const clickPositionX = event.offsetX;
  const newVolume = Math.round((clickPositionX / volumeBarWidth) * 100);
  video.volume = newVolume / 100;
  volumeBar.style.width = newVolume + "%";
  volumeBar.setAttribute("data-volume", newVolume);
});

// hacemos que la barra de volumen superior sea movible y cambie el volumen
let isDragging = false;
let startPositionX = 0;
let startVolume = 0;
document.addEventListener("mousedown", (event) => {
  if (event.target === volumeBarContainer) {
    isDragging = true;
    startPositionX = event.clientX;
    startVolume = Math.round(video.volume * 100);
  }
});



document.addEventListener("mouseup", () => {
  isDragging = false;
});
   
   
   
   
video.controls = false ; 
   
   video.volume = 0.25
   
      
     const volumeLevel = (video.volume * 100).toFixed(0);
  volumeBar.style.width = volumeLevel + '%';
  volumeBar.setAttribute('data-volume', volumeLevel);
        
            
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
            video.src = videoSrc;
            video.addEventListener('canplay', function () {
            
                video.play();
                log("Actualizar la interfaz de usuario cp")
                hls.loadSource();
                
            });
        }


}










      // Función que se ejecuta cuando el tiempo de reproducción es igual al tiempo del buffer






function checkBuffer(video) {
  let buffered = video.buffered;
  let duration = video.duration;

counter = 0;

  for (let i = 0; i < buffered.length; i++) {
    log(`Buffered: ${buffered.start(i)} - ${buffered.end(i)}`,"REALBUFFER");
  }

return

}









function autoQuality(video) {
  var hls = video.hls;
  var levels = hls.levels;
  var currentLevel = 0;
  var lastSeekTime = Date.now();
  hls.currentLevel = currentLevel;
  
  video.addEventListener('timeupdate', function() {
    var currentTime = Date.now();
    var delta = currentTime - lastSeekTime;
    var bufferTime = video.buffered.end(0) - video.currentTime;

    if (delta < 1000) {
      return;
    }

    if (bufferTime < 2) {
      currentLevel = Math.max(currentLevel - 1, 0);
    } else if (bufferTime > 5) {
      currentLevel = Math.min(currentLevel + 1, levels.length - 1);
    }

    hls.currentLevel = currentLevel;
    lastSeekTime = currentTime;
  });
}





async function playVideo(video) {
  try {
    video.muted = false
   
    await video.play();
console.log("!PLAY!!")

  } catch(err) {
  
  video.muted = false
  video.play()
  
  console.log("!CGS!")
//    video.className = "";
  }
  
  video.play()
}



/* HLS CONFIG  */  


const hlsConfig = {
  fragLoadingTimeOut: 30000, // Incrementar el tiempo de espera para la carga de fragmentos
  fragLoadingMaxRetry: 10, // Incrementar el número de intentos de carga de fragmentos
  fragLoadingRetryDelay: 1000, // Tiempo de espera entre reintentos de carga de fragmentos
  manifestLoadingTimeOut: 20000, // Incrementar el tiempo de espera para la carga del manifiesto HLS
  manifestLoadingMaxRetry: 10, // Incrementar el número de intentos de carga del manifiesto HLS
  manifestLoadingRetryDelay: 500, // Tiempo de espera entre reintentos de carga del manifiesto HLS
  enableWorker: true, // Habilita el uso de Web Workers para mejorar el rendimiento
  enableSoftwareAES: true, // Habilita el descifrado de AES en software
  maxBufferLength: 120, // Aumentar la longitud máxima del buffer en segundos
  maxMaxBufferLength: 300, // Aumentar la longitud máxima del buffer en casos extremos
  maxBufferSize: 100 * 1024 * 1024, // Aumentar el tamaño máximo del buffer en bytes
  levelLoadingMaxRetry: 6, // Número máximo de intentos de carga de niveles
  levelLoadingRetryDelay: 1000, // Tiempo de espera entre reintentos de carga de niveles
  startLevel: -1, // Nivel de inicio (auto-selección)
  defaultAudioCodec: undefined, // Codec de audio predeterminado (auto-selección)
  enableCEA708Captions: true, // Habilita subtítulos CEA-708
  enableWebVTT: true, // Habilita subtítulos WebVTT
  enableMP2TSDT: true, // Habilita la tabla de descripciones de flujo MPEG-TS
  enableLowLatency: true, // Habilitar latencia baja si es necesario
  capLevelToPlayerSize: true, // Ajusta el nivel al tamaño del reproductor
  smoothSwitching: true, // Permite cambios de nivel suaves
  abrEwmaFastLive: 5.0, // Ajustes para la estimación de ancho de banda rápido en live
  abrEwmaSlowLive: 9.0, // Ajustes para la estimación de ancho de banda lento en live
  abrEwmaFastVoD: 3.0, // Ajustes para la estimación de ancho de banda rápido en VoD
  abrEwmaSlowVoD: 9.0, // Ajustes para la estimación de ancho de banda lento en VoD
  abrEwmaDefaultEstimate: 500000, // Estimación de ancho de banda predeterminada
  abrBandWidthFactor: 0.8, // Factor de ancho de banda para ABR
  abrBandWidthUpFactor: 0.7, // Factor de incremento de ancho de banda para ABR
  abrMaxWithRealBitrate: true, // Utiliza la tasa de bits real para la estimación de ABR
  abrAveragingForBwEstimate: 5000, // Promedio para la estimación de ancho de banda en ABR
  abrScaledToRealBitrate: true, // Escala a la tasa de bits real
  enableSoftwareCC: true, // Habilita la decodificación de subtítulos en software
  widevineLicenseUrl: undefined, // URL de licencia Widevine (si se utiliza)
  requestMediaKeySystemAccessFunc: undefined, // Función para solicitar acceso a MediaKeySystem (si se utiliza)
  debug: false, // Deshabilita el modo de depuración
  xhrSetup: undefined // Función de configuración de XHR (si se necesita)
};


//Player Start

xplayer(videoSrc)


</script>

















</body></html>
