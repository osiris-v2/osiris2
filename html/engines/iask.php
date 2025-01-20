<?php
session_start();
set_time_limit(300);
if(!isset($_SESSION["CONTEXT_ID"])):
$_SESSION["CONTEXT_ID"] = md5(rand(100,10000000000).date("DmYhis"));
endif;

//# echo "alert(`".$_SESSION["CONTEXT_ID"]."`);";

$context_id = $_SESSION["CONTEXT_ID"];


#ini_set('memory_limit', '-1');

$NContext = "TEMPCONTEXT";

$ask = rawurldecode(($_POST["question"]));


if(!$ask):
	exit();
endif;



if($ask):

$raddr = $_SERVER["REMOTE_ADDR"] ;
$xdata .=<<<ID_CONTEXT

El ip Cliente es: {$raddr}
Tu Id de contexto es: {$context_id}

ID_CONTEXT;


$xdata = base64_encode($xdata);
#$ask = addcslashes($ask,"\\\$");
$ask = base64_encode($ask);
$contextmode="TRUE";


switch ($_POST["smodel"]):
case "image":
$selectModel = "--b64imagecreate";
break;
case "text":
$selectModel = "--b64prompt";
default:
$selectModel = "--b64prompt";
endswitch;

$response = shell_exec("/var/osiris2/bin/com/web/iask.sh  \"$selectModel\" ". $ask ." ".$NContext." ".$raddr." ".$context_id." ".$xdata." ".$context_mode);




if($response):
$response = addcslashes($response, "`\$\\");
#$response = htmlspecialchars($response, ENT_QUOTES, 'UTF-8');
#$response = htmlentities($response);
#$response = nl2br($response);
$ask_dec = htmlentities(base64_decode($ask));
echo<<<JS
constmenu(iardiv.id);
mktparse(rsdiv,`$response`);
iardiv.style = `overflow:auto;margin:5px;margin-top:10px;border-radius:10px;font-weight:500;border:solid 2px;background:#fdffde;padding:15px;font-size:15.2px;line-height:19.5px;word-spacing:1.5px;letter-spacing:1.00px;font-family:Roboto;`
JS;
endif;


else:
echo<<<JS
iardiv.innerHTML = "No se ha recibido una respuesta correctamente";
iardiv.style = "background:#fdfffe;padding:10px;font-size:16px;font-family:arial;";
JS;
endif;




?>
