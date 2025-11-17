<?php
session_start();
set_time_limit(3000);

#echo "IAMODEL";

if(!isset($_SESSION["CONTEXT_ID"])):
$_SESSION["CONTEXT_ID"] = md5(rand(100,10000000000).date("DmYhis"));
endif;


//# echo "alert(`".$_SESSION["CONTEXT_ID"]."`);";

$context_id = $_SESSION["CONTEXT_ID"];
#echo $context_id;

#ini_set('memory_limit', '-1');

$NContext = "TEMPCONTEXT";

$ask = rawurldecode(($_POST["question"]));

$noExec = false;

if(!$ask):
	exit();
endif;



if($ask):

$raddr = $_SERVER["REMOTE_ADDR"] ;
$xdata .=<<<ID_CONTEXT

El ip Cliente es: {$raddr}
Tu Id de contexto es: {$context_id}

ID_CONTEXT;


$contextmode="TRUE";


switch ($_POST["smodel"]):
case "image":
$selectModel = "--b64imagecreate";
break;
case "text":
$selectModel = "--b64prompt";
break;
case "video":
$url = "";
$url = explode(" ",trim($ask));
$curl = $url[0];
$durl = filter_var($curl,FILTER_VALIDATE_URL);
unset($url[0]);
$ask = implode(" ",$url);
if(!$durl){$noExec=true;$response  = "ERROR : El primer argumento debe ser un enlace válido ";} else { $xdata = $durl ; }
$selectModel = "--b64prompt-video";
break;
default:
$selectModel = "--b64prompt";
endswitch;


#echo $selectModel;

$xdata = base64_encode($xdata);
#$ask = addcslashes($ask,"\\\$");
$ask = base64_encode($ask);


if(!$noExec){
$response = shell_exec("../../bin/com/web/iask2.sh  \"$selectModel\" ". $ask ." ".$NContext." ".$raddr." CXID-".$context_id." ".$xdata." ".$context_mode);
}



if($response):
$response = addcslashes($response, "`\$\\");
#$response = htmlspecialchars($response, ENT_QUOTES, 'UTF-8');
#$response = htmlentities($response);
#$response = nl2br($response);
$ask_dec = htmlentities(base64_decode($ask));

if(isset($_POST["rewid"])){
$rewid = $_POST["rewid"];
echo<<<JS
mktparse(getId(`responsediv_$rewid`),`$response`);
JS;
} else {
echo<<<JS
constmenu(iardiv.id);
mktparse(rsdiv,`$response`);
JS;
}

endif;
else:
echo<<<JS
iardiv.innerHTML = "No se ha recibido una respuesta correctamente";
iardiv.style = "background:#fdfffe;padding:10px;font-size:16px;font-family:arial;";
JS;
endif;




?>
