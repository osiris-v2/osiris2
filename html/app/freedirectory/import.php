<?php
session_start();
set_time_limit(0);


//if(!$_SESSION["REGUSER"]) die("<h5 style='background:white;'><!--*/ alert('Se ha cerrado la sesión'); /*--> Inicia Sesión Para usar herramientas</h5>");

include $_SERVER["DOCUMENT_ROOT"]."/lib/php/lib.php";

$_REQUEST["url"] ? $url = $_REQUEST["url"] : die("Not Url") ; 
$_SESSION["path"] ? $path = $_SESSION["path"] : die("Path Error") ; 
$_REQUEST["option"] ? $option = $_REQUEST["option"] : die("Option fail") ;

$ext = pathinfo($url)["extension"] ;
$fname = pathinfo($url)["filename"] ; 

$path = filter_var($path, FILTER_CALLBACK, array('options' => 'escapeshellcmd'));


switch($ext){

/*extensions disabled*/

case 'php':
case 'py':
case 'perl':
case 'cgi':

die("<h3>Protect Discover</h3>");

break;


default:
break;
} 
 
 
switch($option){

case 'ydl':

    $cd = "cd $path && " ;
//    $uid = md5($url);
    #$exec = " --exec 'php postp.php' " ;
   // echo $cd;
   
       $url = filter_var($url, FILTER_VALIDATE_URL);
    $url = filter_var($url, FILTER_CALLBACK, array('options' => 'escapeshellarg'));
   
   $com = "$cd yt-dlp -f best  --write-description --write-info-json --restrict-filenames --write-thumbnail $exec $url";
  
  $out  = md5($url).".mp4";
  
  
#echo $com;

$cd =  dirname(__FILE__)."/".sanitizePath($_SESSION["path"]);

$o = shell_exec("bash ../../../bin/com/web/download.sh $cd $url $out");


echo "".$o ; 

 // echo $com;  


/*
    $id = popen($com,"r") ;
    while($fr = fread($id,255)){
   echo $fr."<br>"; 
   echo str_pad('',4096)."\n";  
    }

  
  pclose($id);
*/

//  echo "EXIT import";
 exit;

break;

default:
break;
}


switch($ext){

case 'gif':
case 'jpg':
case 'jpeg':
case 'mp4':
case 'webm':
case 'mp3':
case 'png':
case 'jpeg':
case 'webp':
case 'svg':
case 'pdf':
case 'txt':
case 'html':


$fname = format_title_for_url(rawurldecode($fname));

$fname = $path.$fname.".".$ext;

//$fname = @str_replace('../',"",$fname);

$x = file_get_contents($url);

echo $fname;
//exit;

if($x) {


$id = fopen($fname,"w") or die("writeError");
fwrite($id,$x);
fclose($id);


echo "<a href='".$fname."' target='_blank'>".$fname."</a>";
} else echo "Not FGC";
break;

default:

echo "ERROR: $fname  :   $ext extensión no permitida para enlace directo";

break;

}

//echo $_REQUEST["path"];

//print_r($data);

?>
