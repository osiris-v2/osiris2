<?php
session_start();
?>
<script src="../../lib/js/wfcore3.js"></script>

<script>
lnk = parent.parent

function setSrc(param,type){

rs = false
n = lnk.document.getElementsByClassName("controles_input")

for(k in n){

if(!rs) rs = false
if(n[k].title==type) {


rs=true;l=lnk.getId(n[k].id);l.value=param

if(type=="style.backgroundImage") {
rs=true;l=lnk.getId(n[k].id);l.value= `url("`+param+`")`

eval('lnk.ad['+n[k].alt+'].'+type+'=`url("'+param+'")`')
d = eval('lnk.ad['+n[k].alt+'].style.background')

if(!d || d == 'none') eval('lnk.ad['+n[k].alt+'].style.background=`url("'+param+'")`')

} else {
rs=true;l=lnk.getId(n[k].id);l.value=param
eval('lnk.ad['+n[k].alt+'].'+type+'=`'+param+'`')
}

lnk.clickId('#edit_'+lnk.editing)

}

}
/*DEBUG if(rs) alert("set")
else alert("noexists")
*/

if(!rs) alert("no existe el atributo "+type+"\n para el objeto id "+lnk.editing+" seleccionado")
}


</script>
<style>
.visor{
clear:both;
border:solid 0px red;
display:none;
visibility:hidden;
padding:10px;
font-size:18px;
font-family:'gill sans';
overflow:hidden;
}
.amenuv{
padding:8px;
text-decoration:none;
color:#222313;
font-weight:bold;

font-size:13px;
}
.amenuv2{
float:left;
background:#dedefe;

border:outset 1px #cfcfcf;
}


.lsdir{

font-size:16px;
font-family:arial;
}

</style>
<div style="width:100%;max-width:100%;min-height:100%;margin:0 auto 0 auto;">
<?php
$fconf = "../../conf2/freedirectory.conf";
include('../../lib/php/aconf.php');
include '../../lib/php/lib.php';

//print_r($_SPECIALCONF);

if(!isset($_SESSION['bdir'])) $_SESSION['bdir'] = "./";
if(!isset($_SESSION['path'])) {$_SESSION['path'] = "./";}
if(!isset($_REQUEST['mkdir'])) $mkdir = '';
else $mkdir = $_REQUEST["mkdir"];
if(!isset($_REQUEST["chdir"])) $chdir= ".";
else $chdir = $_REQUEST["chdir"];


if(preg_match("@( (\.\.)| (\.\./) |(/\.\.)|(\.\./))@si",$chdir) || preg_match("@^file:///@si",trim($chdir)) || preg_match("@^/@si",trim($chdir)) || !is_dir($chdir)){

echo "<h1>dir error  
<a href='?chdir=".$_SESSION["path"]."'>Volver</a>
</h1>";
exit;
}


if($mkdir){
@mkdir($mkdir,0777) ? $_SESSION["path"] = $mkdir."/" : die("ERROR creando directorio<br><a href='?chdir=".$_SESSION["path"]."'>Volver</a>");

}
elseif($chdir) {
$_SESSION["path"] = $chdir."/";

}



$barra = explode("/",$_SESSION["path"]); 

if(($len=count($barra))>1){

$relay = 0;
$enlace[0] = "<a href='?chdir=.'>Inicio</a>";

for($i=1;$i<$len-1;$i++){
if($barra[$i]=="") continue;
$barra_l[$i] = $barra[$i];
$sl = implode("/",$barra_l);
if($i==$len-2) {$enlace[$i] = "<b>{$barra[$i]}</b>";}
else {$enlace[$i] = "<a href='?chdir=./".$sl."'>{$barra[$i]}</a>";}
$relay++;
} 

$barra = implode("/",$enlace);

} else echo "INICIO";


$lists = fdext($_SESSION["path"]);
//print_r($lists);exit
?>


<script>var mxurl = 0;z=new Array()</script>

<div style="text-align:right;">
<select id="select">
<option value="url">url</option>
<option value="ydl">VideoUrl</option>
</select>
<input type="text" id="ajxurl" placeholder="Introducir URL" style="width:240px;">
<input type="button" value="importar"

onclick='

  z[mxurl] = document.createElement("div") ;
  z[mxurl].id = "d_"+mxurl ;
  z[mxurl].innerHTML = `<b>Importing:<br>`+document.getElementById("ajxurl").value+`<br><img src="/img/cargando.gif" height=20>`;
  document.getElementById("ajxres").prepend(z[mxurl]) ;
  ajax({
  	datas:"url="+encodeURIComponent(document.getElementById("ajxurl").value)+"&option="+document.getElementById("select").value,
  	id:z[mxurl].id,
  	location:"import.php",
  	method:"GET",
  	eval:false
  	}) ; 

mxurl++;

'>

<div id="ajxres"  style='max-height:20%;overflow:auto;'></div>



<a href="javascript:void(0);" onclick='
if(d = prompt("CREAR DIRECTORIO NUEVO\nEs necesario tener permisos para crear el directorio nuevo.","")){
location.href="?mkdir=<?=$_SESSION["path"]?>"+d

} else{alert("Operación Cancelada")}
'>Nuevo Directorio</a>

 
<a href="javascript:void(0);" onclick='
location.reload()
'>Actualizar</a>

</div><div id='barra' style='padding:3px;'><?=$barra?></div>
<div style="overflow:hidden;float:left;width:15%;paddind:4px;height:auto;background:#ecfcdf;" id="lsdir">

<?php
if(isset($lists["DIR"])>0){
foreach($lists["DIR"] as $key => $value){
?>

<span class='lsdir'><a href="?chdir=<?=$_SESSION["path"]?><?=$value[0]?>" title="<?=$value[1]?>"><?=$value[1]?></a></span><br> 

<?php
}} else echo "0 DIR";
?>
</div>


<div style="float:left;overflow:hidden;text-align:left;width:85%;height:auto" id="lsfile">

<?php
if($lists["EXT"]){
$ext = explode("\/",$lists["EXT"]);
$menu = "";
$visor = "";
foreach($ext as $extvalue){

$menu .= "
<div class='amenuv2'>
<a class='amenuv' href='javascript:void(0)' onclick=\"dmenu('$extvalue','visor')\">$extvalue</a>
</div>
";


$visor .=  "<div class='visor' id='$extvalue'>";
if(isset($lists["FILE"])){


asort($lists["FILE"]);


$visor .= extoption($extvalue);




$ids = 0;
foreach($lists["FILE"] as $key => $value){
$ids++;
if($value[2] == $extvalue){
$innerDiv = "";
$idsN = "id_".$extvalue."_".$ids;

$setSrc = "<a href=\"javascript:setSrc('../freedirectory/".$_SESSION["path"].rawurlencode($value[0])."','src')\">Aplicar Src</a>";

$setPoster = "<a href=\"javascript:setSrc('https://".$_SERVER['SERVER_NAME'].'/jsa/media/'.$_SESSION["path"].rawurlencode($value[0])."','poster')\">Aplicar Poster</a>";


$setBGIMG = "<a href=\"javascript:setSrc('https://".$_SERVER['SERVER_NAME'].'/jsa/media/'.$_SESSION["path"].rawurlencode($value[0])."','style.backgroundImage')\">Aplicar backgroundImage</a>";

switch(strtolower($extvalue)){

case 'jpg':
case 'png':
case 'jpeg':
case 'bmp':
case 'ico':


$innerDiv = $setSrc." ".$setPoster." ".$setBGIMG."<div><img src=\"".$_SESSION["path"].$value[0]."\" style=\"height:50vh;width:auto;\"></div>
";

break;

case 'gif':
case 'svg':
case 'webp':

$innerDiv = $setSrc." ".$setPoster." ".$setBGIMG."<div style=\"background:url('".$_SESSION["path"].$value[0]."') center/cover;width:70%;height:70%\">Previev Img</div>";



break;


case 'ttf':
case 'otf':

$innerDiv = $setSrc." ".$setPoster." ".$setBGIMG."<div style=\"font:url('".$_SESSION["path"].$value[0]."')\">

qwertyuiopñlkjhgfdsazxcvbnm<br>
QWERTYUIOPÑLKJHGFDSAZXCVBNM<br>
123456789 
<br>


</div>";



break;


case 'php':
$innerDiv = "<p>".$setSrc."</p>" ;
break;


case 'html':
case 'htm':
case 'txt':
case 'json':
case 'description':

$innerDiv = $setSrc."<iframe src=\"".$_SESSION["path"].$value[0]."\" style=\"border:0;resize:both;width:100%;height:80%;display:inline\" >Previev</iframe>";

break;


case 'mp4':
case 'webm':
case 'ogv':
case 'ogm':
case 'ogg':

$innerDiv = $setSrc."<video src=\"".$_SESSION["path"].rawurlencode($value[0])."\" type=\"video/".$extvalue."\" style=\"border:0;resize:both;width:100%;height:80%;\" autoplay controls loop volume=\"0.5\"></video>";

break;

case 'wav':
case 'mp3':

$innerDiv = $setSrc."<audio src=\"".$_SESSION["path"].rawurlencode($value[0])."\" type=\"audio/".$extvalue."\" style=\"border:0;resize:both;width:100%;\" autoplay controls loop volume=\"0.5\"></audio>";

break;

case 'pdf':
$innerDiv = $setSrc."<iframe src=\"".$_SESSION["path"].rawurlencode($value[0])."\" style=\"border:0;resize:both;width:100%;height:80%;\" type=\"application/".$extvalue."\">Previev</iframe>";

break;


default:
$innerDiv = "Advanced Open";
break;
}

$view = "<a name=\"xn_$idsN\"><a href='#xn_$idsN' onclick='x = display2(\"$idsN\",\"displays\");if(x==`none`) {document.getElementById(\"$idsN\").innerHTML = decodeURIComponent(`".rawurlencode($innerDiv)."`)} else {clearHTML(\"$idsN\")}'>view</a>";

$divsplays = "<div id='".$idsN."' style='display:none;' class='displays'></div>";

$visor .= "<div><a href='".$_SESSION["path"].$value[0]."' target='_blank' title='".

$value[1]."'>open</a> ".$view." ".fileoption($value[2],$value[0])."&nbsp;<span>".ucwords(strtolower($value[1]))."</span> $divsplays </div>";



}
}}
$visor .= "</div>";
}
echo "".$menu."<br>".$visor;
} else echo "0 FILES";

?>
</div>

</div>

<?php

function fileoption($ext,$file){
global $cd__MiTV;
switch(strtolower($ext)){
case 'ts';
$base1 = "file '{$_SERVER["DOCUMENT_ROOT"]}/{$_SESSION["path"]}";
$base2 = "'\n";
$file = base64_encode($base1.$file.$base2);


$TS=<<<TS


<input type="checkbox" class="check_$ext" value="$file">

TS;

return $TS;

break;
default:
return;
break;
}}


function extoption($ext){


switch(strtolower($ext)){
case 'ts';

$TS=<<<TS
 
<input type="button" value="Crear Lista TS" onclick="creaLista(document.getElementsByClassName('check_$ext'),'op_$ext')">

<span id='op_$ext'></span>

<br>
<script type="text/javascript">

function creaLista(tag,vret){


mklist = ""
openlist = ""
namelist = ""
intolist = ""
closelist = ""

n = 0;
for(i=0;i<tag.length;i++){
if(tag[i].checked == true) {
intolist += "*"+tag[i].value;n++;
}
}

if(n<1){
alert("Ningun archivo seleccionado");
return false;
}

if(namelist = prompt("CREAR LISTA TS Nombrar","lista")){

lista = mklist+openlist+intolist+closelist


ajax("namelist="+namelist+"&files="+lista+"&div="+vret,vret,'mklist.php','GET')

} else{ alert("cancelado")}
}

</script>
TS;

return $TS;

break;
default:
return;
break;
}

}

?>
