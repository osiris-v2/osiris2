<script src="http://<?=$_SERVER['SERVER_NAME']?>/lib/ajax/hls.js/dist/hls.js" type="text/javascript"></script>
<script src="http://<?=$_SERVER['SERVER_NAME']?>/lib/ajax/hxr.js"></script>
<style>
.comt,.com{
width:100%;
}
.comt{
height:240px;
}
</style>

<div id='companel'>
<textarea id="com1" class='comt'>
<?=trim(file_Get_contents($_SERVER["DOCUMENT_ROOT"].'/php/datas/default.com'));?>
</textarea>
<input type="button" onclick='if(confirm("CLEAR TEXTAREA??")){
gId("com1").value = ""
gId("namecom").value = ""
}
' value='Nuevo'><input type='button' onclick='
ajaxReturn("save=1&rewrite=1&com="+getId("com1")+"&name="+getId("namecom"),"avisos","saver.php","POST","flush")
clickId("#hrefId_listacom")'
 value='Guardar'><input type="text" value='default' id='namecom' paceholder='guardar comando como'>
<span id='listacom'><input type="button" onclick="
jxp('action=listacom','listacom');
" id='hrefId_listacom' 
value="lista comandos">


</span>

<br>


<input type="button" value="KILL" onclick="alert('matar proceso');return false">
<input type="button" value="UnBucle" onclick="unbucle=1">
<input type="button" value="flush data" onclick="if(flushdata) {ret='activar';flushdata=0;} else {ret='desactivar';flushdata='noempty';document.getElementById('div1').innerHTML=''} this.value = 'FlushData: '+ret">
<input type="button" value="EXEC" onclick="scom('>'+getId('com1'))">
<input type="button" value="EXIT_AJAX" onclick='EXIT_AJAX=true'>
<input type="button" value="ADD_VIDEO" onclick='if(src=prompt("AD VIDEO URL","http://<?=$_SERVER["SERVER_NAME"]?>/www/play.m3u8")){addVideo("MASTER",src);}'>
<br>
<input type="button" value="Browser" onclick='r=display("browserfile");this.value="Browser "+r'>
<input type="button" value="Sub-Editor" onclick='r=display("comdata");this.value="comdata "+r'>
<input type="button" value="avisos" onclick='r=display("avisos");this.value="avisos "+r'>
<input type="button" value="div1" onclick='r=display("div1");this.value="div1 "+r'>
<input type="button" value="idx" onclick='r=display("idx");this.value="idx "+r'>
<input type="button" value="Video" onclick='r=display("mg");this.value="mg "+r'>
<input type="button" value="CLEAR EXEC" onclick='clearHTML("div1")'>
</div>
<iframe id='browserfile' src="index.html" style="display:none;width:100%;height:320px;" frameborder=0></iframe>
<div id="comdata"></div>
<div id="avisos"></div>
<div id='div1'>RETURN PJXML EXEC JS</div>
<code id='idx' style=''>RETURN PJXML EXEC JS</code>
<div id='mg'></div>

<script>

unbucle=0

function progres1(data){
document.getElementById('idx').innerHTML = data
console.log(data)
}

document.getElementById('idx').style.maxHeight = "160px"
document.getElementById('idx').style.overflow = "auto"
document.getElementById('idx').style.display = "block"


document.getElementById('div1').style.maxHeight = "140px"

document.getElementById('div1').style.overflow = "auto"

document.getElementById('idx').innerHTML = ""
document.getElementById('div1').innerHTML = ""


flushdata="";

function addVideo(s,src='in.mp4',mimetype="application/x-mpegURL"){

video = document.createElement("video")
video.id = s
video.style="width:100%;height:280px;"+
"border:solid 3px #239476;"
video.controls = true;


xplayer(s,src,mimetype)

document.getElementById('mg').innerHTML = ""
document.getElementById('mg').appendChild(video)

}


function scom(a){
action = a
if(unbucle) filejhp = '/php/execajax.php'
else filejhp = '/php/execajax-while.php'
ajaxReturn("VAR="+action+"&flushdata="+flushdata,'',filejhp,'GET','function');


}


function jxp(action,put){
ajaxReturn(action,put,'/php/jxp.php','GET')
}


</script>


