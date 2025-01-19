<?php


$idv = filter_input(INPUT_GET,"v",FILTER_VALIDATE_INT);

$mysqli = new mysqli('compostela21.com', 'root', 'c21comdbpsw', 'varias2');
#include('paginator2.php');    

if($_GET["v"]){
    $sql ="select id,image,title,url,description,fuente from videos where id=".$idv;
} 
$result = $mysqli->query($sql);






while ($row = mysqli_fetch_object($result)) {
$url = $row->url;
$poster = $row->image;
$id = $row->id;
$fuente = $row->fuente;
$title = $row->title;
}


?>



<?php

/*

$F = $quality="best";


switch($fuente){
    case 'dailymotion':

    $F = "http-480-1";

        break;
        
      case 'youtube':

    $F = "18";

        break;
    
        case 'facebook':

    $F = "best";

        break;
    
    
case 'vimeo':

$F = "http-360p";
break;

case 'abcnews:video':
        case 'abcnews':
            $F ='PDL_MED';
       
            break;
}

if($url){
$cmd = "youtube-dl -s -q -f $F --get-url $url";
  
//$cmd = "youtube-dl -s -q --get-url -f $quality $url";

$link =  shell_exec($cmd);

$link=trim($link);
       $link = preg_replace("@^(https|http)(.+)$@is","https$2",$link);
} else{
    
    echo "<h1>err:1</h1>";
    exit;
}
//$xl = base64_encode("link=".trim(urlencode($link))); 



$mdata = stream_get_meta_data(fopen($link,"r")); 



if(!$mdata){

$puente = 0;

$link = "https://www.compostela21.com/img/er404.mp4";

} else {

if(preg_match("/^http.+dailymotion.com.+$/is",$link)) {

$puente=1;;

} else {


//print_r($mdata["wrapper_data"]);exit; 

 foreach($mdata["wrapper_data"] as $k => $value){
    

    
    if(preg_match("/^(Content\-Type\:) ?(audio|video)\/(.+)$/si",$value,$resdata)){
        
        $content_type=$resdata[1]." ".$resdata[2]."/".$resdata[3];
        $title  = $title.".".$resdata[3]; 
      unset($puente);
      break;
       
    } else {$puente=1;}
    
    } 

}

}
//echo $content_type.$puente;


//exit;


//if($puente==1) $link="/ytbdwn.php?ein=".base64_encode("link=".urlencode($link));      

*/
?>





<figure style="background:#fcfeff;">

<?php 
if($_REQUEST["link"]!="none"){
?>
<div style='text-align:right;'><b><i><a href="<?=$url?>" target="_blank"><?=$fuente?></a></i></b></div>
<?php
}
?>

<?php

if($_REQUEST["title"]!="none") {print('<figcaption style="padding:5px;">'.$title.'</figcaption>');}

if(!$_REQUEST["preload"]) $_preload = "none";
else $_preload = $_REQUEST["preload"];

?><video id="video_w_<?=$id?>" poster="<?=$poster?>" style="width:100%;min-height:320px;max-width:100%;max-height:640px;background:#000;" 

src="https://vtwitt.com/ydld.php?url=<?=$url?>"

<?php
$_REQUEST["attrs"] ? $echo = $_REQUEST["attrs"] : $echo = " controls" ;
?><?=$echo?>

></video></figure>
   







<?php
$mysqli->close();
?>



























