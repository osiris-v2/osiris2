<?

if(!$_REQUEST["name"]) $_REQUEST["name"] = "default";

$save = "SAVED:".$_REQUEST["name"]."\n<hr>".$_REQUEST["com"];
$com = $_REQUEST["com"];
$filename = $_REQUEST["name"];
if(!ISSET($_REQUEST["rewrite"])) $rewrite = 0;
else $rewrite= $_REQUEST["rewrite"];



if(file_exists($_SERVER["DOCUMENT_ROOT"]."/php/datas/".$_REQUEST["name"].".com") && !$rewrite){

echo<<<JS

<input type='button' 
onclick='
ajaxReturn("rewrite=1&save=1&com="+getId("cdx")+"&name=$filename","avisos","saver.php","POST");
emulaClick("#hrefId_listacom")
' 
value='sobreescribir: $filename'>

JS;

echo "ERROR SAVE EN SAVER.php";

} else {
file_put_contents($_SERVER["DOCUMENT_ROOT"]."/php/datas/".$_REQUEST["name"].".com",$_REQUEST["com"]);
file_put_contents("".$_REQUEST["name"]."",$_REQUEST["com"]);

}
echo $save;
