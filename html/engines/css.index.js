

xbody.style = `font-family:arial;margin:0;background:#000000;`
a2.className = "lmenu"
a3.className = "lmenu"
//IAR.id = "IAR"


Nav0.style = ` 
background:#000000;
position:fixed;
height:30px;
width:100%;float:right;z-index:665;paggin:0;margin:0;z-index:10;;
`

button0.style = `height:50px;top:0px;z-index:4;
margin:0;padding:0;border:0;width:50px;
`


Container.style = `
background:#000000;
position:fixed;height:95vh;
margin-top:5vh;
z-index:1;
width:100%;
text-align:center;border:solid 1px red;
`

MI.style = `display:block;
background:#000000;
 width:54px;
height:95vh;
`

WEBIRC.style = `
 width: 80%;
  height: 80%;
margin:0% 5% 20% 5% ;
background:#000000;
  display: flex;
  justify-content: center;
  align-items: center;
`



IAI.style = `
display:flex;flex-grow:1;
position:relative;top:0;height:4.5vh;
border:solid 2.3px #05124F;font-size:2vh;font-weight:700;font-family:ubuntu; ;
`

IAVQ.style = `
position:absolute;width:5.6%;top:0;height:5vh;
border:solid 2px #05124F;
margin-left:calc(90vw + 3%);
`


SMODEL.innerHTML += `
    <form id="miFormulario">
        <input type="radio" name="opcion" value="text" id="opcion1" checked  onclick="selectModel()">
        <label for="opcion1">Text</label><br>
        <input type="radio" name="opcion" value="image" id="opcion2"  onclick="selectModel()">
        <label for="opcion2">Image</label><br>     
        <input type="radio" name="opcion" value="video" id="opcion3"  onclick="selectModel()">
        <label for="opcion3">Video</label><br>
        <!--button type="button" onclick="selectModel()"></button-->
    </form>
    <p id="resultado"></p>
`

IAR.style = `
padding:20px 2% 2% 2%;
background:rgba(5,5,2,.4);
position:absolute;z-index:665;
margin-left:13%;
width:80%;
max-height:87vh;
height:auto;
display:none;
overflow:auto;
resize:both;
border:solid 4px rgba(222,220,220,.6); justify-content:center; align-items:center;
`



menuApp.style = `
z-index:666;
display:none;position:fixed;
width:auto;
background:rgba(0,0,0,.85);
color:#efefdc;
height:100%;
top:5vh;
padding:1.4%;
`



regInf.info = `ShadowHost Link`
regInf.style = `background:black;`

