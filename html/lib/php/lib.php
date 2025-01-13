<?php



class ffmpeg{


function get_capture($input){


$COM=<<<COM

ffmpeg -i $input

 -ss 00:01:55 -t 00:00:01 '.$newIm ;



COM;
}



}






function cadena_a_binario(string $cadena): string {
  $binario = '';
  for ($i = 0; $i < strlen($cadena); $i++) {
    $ascii = ord($cadena[$i]);
    $binario .= decbin($ascii);
  }
  return $binario;
}





function text_inline($text){

     return preg_replace("/\n+/", "\n", $text);

}



function format_title_for_url($title, $encoding = "utf-8") {
  // Convertimos el título a minúsculas.
  $title = strtolower($title);

  // Reemplazamos los espacios por guiones bajos.
  $title = str_replace(" ", "-", $title);

  // Convertimos el título al formato UTF-8.
  $title = mb_convert_encoding($title, "UTF-8", $encoding);

  // Reemplazamos los caracteres especiales por guiones bajos.
  $title = preg_replace("/[^a-z0-9.,áéíóúñÑü\n\t]/", "", $title);

  // Eliminamos los guiones consecutivos.
  $title = preg_replace("/-+/", "-", $title);

  // Convertimos el título de nuevo al formato ISO.
  $title = mb_convert_encoding($title, $encoding, "UTF-8");

  return $title;
}



function b64e($toEncode,$encode="rb64e",$function="base64_encode"){

return $encode.":".$function($toEncode);

}



function get_texto_url($url, $expresion_regular, $valor_predeterminado) {
  if (preg_match($expresion_regular, $url)) {
    return preg_match($expresion_regular, $url);
  } else {
    return $valor_predeterminado;
  }
}



function AutoLinkUrls($str,$popup = FALSE,$param=""){
    if (preg_match_all("#(^|\s|\()((http(s?)://)|(www\.))(\w+[^\s\)\<]+)#i", $str, $matches)){
        $pop = ($popup == TRUE) ? " target=\"_blank\" " : "";
        for ($i = 0; $i < count($matches['0']); $i++){
            $period = '';
            if (preg_match("|\.$|", $matches['6'][$i])){
                $period = '.';
                $matches['6'][$i] = substr($matches['6'][$i], 0, -1);
            }
            $str = str_replace($matches['0'][$i],
                    $matches['1'][$i].'<a href="http'.
                    $matches['4'][$i].'://'.
                    $matches['5'][$i].
                    $matches['6'][$i].'"'.$pop.' '.$param.'>http'.
                    $matches['4'][$i].'://'.
                    $matches['5'][$i].
                    $matches['6'][$i].'</a>'.
                    $period, $str);
        }//end for
    }//end if
    return $str;
}//end AutoLinkUrls




function keywords($param){
    
    $d = explode(" ",$param);
    
    foreach($d as $value){
        
        if(strlen($value)<4) {continue;}
        else {$palabro[] = $value;}
        
    }

    $frase = implode(",",$palabro);
  return $frase;
    
}



function articulos_relaccionados($gID,$relSrch,$tabla,$excludes="array",$limit="15"){

GLOBAL $host, $usr, $psd, $base_datos;

if(!$relSrch || !$gID){return false;}

$lenLimit = 2;
$join = " || ";
$modejoin = " || ";
$modejoinoption = " ||  ";
$limitResult = " Limit 0,$limit ";
$defrag = explode(" ",$relSrch);

$z = count($defrag);
$y = $z;

if(is_array($excludes)) {$isArray = true;}
else {$isArray=false;}

for($x=$z-1;$x>=0;$x--){


if($isArray){
if(in_array(strtolower($defrag[$x]),$excludes)){ 
continue;
}
}



if(strlen($defrag[$x])>$lenLimit){

$psar[] = " (sem like  '%".$defrag[$x]."%' $modejoinoption expo like '%".$defrag[$x]."' $modejoinoption  subtitulo like '%".$defrag[$x]."') ";
$pstr[] = implode($modejoin,$psar);

	}
$y--;

}

$constsql = implode($join,array_reverse($pstr));

$sql = "select id,sem,expo,subtitulo,foto from $tabla where ((".$constsql.") && (id !='$gID')) order by time_update desc $limitResult";



$mysqli = new mysqli($host, $usr, $psd, $base_datos);

if ($resultado = $mysqli->query($sql)) {
	if($afr = $mysqli->affected_rows){
$narray = 0;
while($res = $resultado->fetch_row()){
$reLink[$narray]["ID"] = $res[0];
$reLink[$narray]["TITLE"] = $res[1];
$reLink[$narray]["SUBTITLE"] = $res[3];
$reLink[$narray]["DESCRIPTION"] = $res[2];
$reLink[$narray]["IMAGE"] = $res[4];
$narray++;
}
	} else { return Array();  }
} else { return Array(); }
return $reLink;
$mysqli->close();
}

// FIN FUNCION ARTÍCULOS RELACCIONA2



// rawurlencodefixed
function xencode($url) {
    // Divide la URL en componentes
    $url_components = explode("/", $url);
    // Obtiene el último componente de la URL
    $last_component = end($url_components);
    // Codifica el último componente usando urlencode
    $encoded_last_component = rawurlencode($last_component);
    // Reemplaza el último componente de la URL con el codificado
    array_pop($url_components);
    array_push($url_components, $encoded_last_component);
    // Reconstruye la URL
    $encoded_url = implode("/", $url_components);
    // Devuelve la URL codificada
    return $encoded_url;
}








/*   Archivos y directorios */



function dext($_a,$_1=""){
$match = preg_match("@^(.+)?\.(.+)$@si",$_a,$matches);
if($match) {$matches[1] = basename($matches[1]);}
else {$matches[0] = $_a; $matches[1] = basename($_a);$matches[2]=false;$matches[3] = false;}
if($_1){if(file_exists($_a)){
if(is_dir($_a)){$matches[2]=false;$matches[1]=basename($_a);}
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$matches[3] = finfo_file($finfo, $_a);
finfo_close($finfo);
} else {$matches[3] = false;}}
return $matches;
}




function ext($file,$preg=""){
$file = str_replace(".","",strrchr($file,"."));
if($preg) return preg_match($preg,$file);
else return $file;
}

function cdext($file,$value,$preg){
if($value == '*') {$RD[0] = "*";$RD[1] = ext($file,$preg);$RD[2] = $file;return $RD;} 
else{
$dext = explode(",",$value);
if(count($dext)<1) {return false;}
foreach($dext as $avalue){
$ext = ext($file,$preg);
if(strtolower($ext) == strtolower($avalue)){ $RD[1] = $ext;$RD[2]=$file;$RD[0]=true;return $RD;}
else {continue;}
}
}
return false;
} 



function txtln($exec){
 return preg_replace("/\n/is"," ",trim($exec));
}



function filesdir($dir,$rtype='0'){
$files = Array();
$handle = opendir($dir);
while($read = readdir($handle)){
if(is_file($dir."/".$read) && $read!="." && $read!=".."){
if($rtype>1) $read = $dir."/".$read;
$files[] = $read;
}
}
return $files;
}



function fdir($dir="."){
$ret = Array();;
$files = Array();
$subdirectorios = Array();
$handle = @opendir($dir); 
if(!$handle) return false;
while ($file = readdir($handle)) {
if(is_dir($dir."/".$file) || $file=="." || $file=="..") {
    if($file!="." && $file!=".."){
    $subdirectorios[] = $file;
    continue; 
    }
} else  {$files[] = $file;}
}
closedir($handle);
$ret[0] = $subdirectorios;
$ret[1] = $files;
return $ret;
}


function fdext($dir,$dext=''){
$ret = Array();
$ext = Array();
$arr = fdir($dir);
if(count($arr[0])>0){
foreach($arr[0] as $key => $value){
$ret["DIR"][] = dext($value,$dext);
}}
if(count($arr[1])>0){
$i=0;
foreach($arr[1] as $key => $value){
$ret["FILE"][$i] = dext($value,$dext);
if($ret["FILE"][$i][2]) $ext[$ret["FILE"][$i][2]] = $ret["FILE"][$i][2];
$i++;
}}
$ret["EXT"] = implode("\/",$ext);
return $ret;

}





































function formatear_enlace($cadena){
		
		//Reemplazamos la A y a
		$cadena = str_replace(
		array('Á', 'À', 'Â', 'Ä', 'á', 'à', 'ä', 'â', 'ª'),
		array('A', 'A', 'A', 'A', 'a', 'a', 'a', 'a', 'a'),
		$cadena
		);
 
		//Reemplazamos la E y e
		$cadena = str_replace(
		array('É', 'È', 'Ê', 'Ë', 'é', 'è', 'ë', 'ê'),
		array('E', 'E', 'E', 'E', 'e', 'e', 'e', 'e'),
		$cadena );
 
		//Reemplazamos la I y i
		$cadena = str_replace(
		array('Í', 'Ì', 'Ï', 'Î', 'í', 'ì', 'ï', 'î'),
		array('I', 'I', 'I', 'I', 'i', 'i', 'i', 'i'),
		$cadena );
 
		//Reemplazamos la O y o
		$cadena = str_replace(
		array('Ó', 'Ò', 'Ö', 'Ô', 'ó', 'ò', 'ö', 'ô'),
		array('O', 'O', 'O', 'O', 'o', 'o', 'o', 'o'),
		$cadena );
 
		//Reemplazamos la U y u
		$cadena = str_replace(
		array('Ú', 'Ù', 'Û', 'Ü', 'ú', 'ù', 'ü', 'û'),
		array('U', 'U', 'U', 'U', 'u', 'u', 'u', 'u'),
		$cadena );
 
		//Reemplazamos la N, n, C y c
		$cadena = str_replace(
		array('Ñ', 'ñ', 'Ç', 'ç'),
		array('N', 'n', 'C', 'c'),
		$cadena
		);
$cadena = preg_replace("@[^a-z0-9áéíóú (&#.+;)]@is","", trim($cadena));
$cadena = str_replace(" ","_",strtolower($cadena));

		return $cadena;
	}




function formatArticle($title, $description, $article) {
  // Create the formatted article string
  $formattedArticle = "";

  // Headline (use $title or customize logic)
  $formattedArticle .= "<h2>" . $title . "</h2>";

  // Lead paragraph (summarize from $description)

$offset = 150;
$leadParagraph = ($position !== false) ? substr($description, 0, $position) : substr($description, 0, min($offset, strlen($description)));


#  $leadParagraph = substr($description, 0, strpos($description, '.', 150)); // Limit to 150 chars with first sentence
  $formattedArticle .= "<p class='lead'>" . $leadParagraph . "</p>";

  // Body paragraphs (extract from $article)
  $paragraphs = explode("\n", $article); // Split into paragraphs
  foreach ($paragraphs as $paragraph) {
    $formattedArticle .= "<p>" . trim($paragraph) . "</p>"; // Trim whitespace and add paragraph tag
  }

  return $formattedArticle;
}
