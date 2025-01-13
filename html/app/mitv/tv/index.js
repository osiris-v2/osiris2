



  var video = getId('Player');


 function xvd(videoSrc,ct,p,t,d){


video.preload = "metadata"
video.type = ct
video.poster = p

if (video.canPlayType(ct)) {
  video.src = videoSrc;

  } else if (Hls.isSupported()) {
  var hls = new Hls();
  hls.loadSource(videoSrc);
  hls.on(Hls.Events.MANIFEST_PARSED, function (event, data) {
     console.log('Manifest loaded, found ' + data.levels.length + ' quality level');
    });
   
      hls.attachMedia(video);
}  
   
   
video.preload = true ;
video.play();
video.volume=0.3
video.controls = true;

}
    





	// dinamics onload


//END APP



