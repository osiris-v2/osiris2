/* index js */



moveTag(MainPanel,Body)



moveTag(IntroApp,MainPanel)




moveTag(Splash, MainPanel)







moveTag(SplashContainer,MainPanel)



moveTag(CloseSplash, SplashContent)


moveTag(SplashContent,SplashContainer)









onload = function(){

  function makeResizable(elementId) {
    const container = document.getElementById(elementId + "-container");
    const content = document.getElementById(elementId);

    // Estilos iniciales
    container.style.width = "40vw";
    container.style.position = "absolute";
    container.style.padding = "10px";
    container.style.boxSizing = "border-box";
    container.style.visibility = "hidden"; 
    container.style.height = "40vh";
    container.style.fontSize = "18px";
    container.style.fontWeight = "bold";
    container.style.overflow = "hidden"; // Evita que el contenido sobresalga
    container.style.resize = "both"; 
    container.style.background = "rgba(125,125,125,.35)"


	content.style.resize = "both";
    content.style.width = "98%";
    content.style.height = "calc(100% - 20px)"; 
    content.style.fontSize = "22px";
    content.style.color = "#feedde";
    content.style.background = "rgba(122, 2, 255, 0.7)";
    content.style.padding = "1%";
    content.style.boxSizing = "border-box";



  }




function randnick(){
randnick  = "Web3" + "_" + Math.floor(Math.random() * 9999999);
return randnick
}

randnick = randnick()

//urlc = "https://chathispano.com/webchat/?theme=embeb&style=orange&title=Osiris-Irc-Chat&autojoin=true&autoload=true&nick=osiris_"+randnick+"&chan=#OsirisWeb3&logo=https://cdn.chathispano.com/news/esquina.jpg"

urlc="https://kiwiirc.hybridirc.com/?nick=Osiris"+randnick+"&theme=Dark#osirisWeb3,#help"
urlcr = "https://osiris000.duckdns.org/app/widgets/webirc.html"

//alert(urlc)

IntroApp.innerHTML = `
<div id="webirc-container" style="z-index:3">

<div>
 
  <b style="background:rgba(120,180,195,.4);padding:2px;"> IRC - CHAT </b> 
<!--reload chat-->
   <button type="button" class='mbuton' onclick="document.getElementById('ifchat').src='`+urlcr+`'"> RELOAD </button>
<!--ocultar chat-->
   <a href="javascript:void(0);" onclick="document.getElementById('webirc-container').style.visibility='hidden';" style="background:rgba(3,3,3,.5);float:right;cursor:pointer;color:#c4edea;font-weight:bold;"> [ocultar] </a>  
</div>

<div id='webirc'> 
<iframe id="ifchat" 
allow="camera; microphone; display-capture; fullscreen"
frameborder="0" src="`+urlc+`"  style="width: 100%;height:100%;overflow:auto;"></iframe>
</div>

</div>

`
makeResizable("webirc");
IntroApp.innerHTML += `
<iframe id='iftvx2' class="rumble" layout="responsive" style="width:100vw;height:100vh;display:block" src="https://osiris000.duckdns.org/app/widgets/hlstv.html" frameborder="0" allowfullscreen></iframe>
`

/*

final de carga

*/


}
