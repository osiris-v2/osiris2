<?php



#  Sirve para averiguar la extension de un archivo dada en su nombre ej(archivo.mp4)
#  Devuelve cuatro valores en un array
# 0-> nombre del archivo completo
# 1-> nombre del archivo sin la extension
# 2-> la extension del archivo
# 3-> optativo INT 0 | 1 comprueba que el archivo existe y el mimetype
# con el segundo parámetro en 1 comprueba el mime/type del archivo
# esto es útil para nombres de archivo no fiables
# devuelve entonces un cuarto parametro
# 3-> mime/type
# si es un directorio devuelve
# 0 -> nombre del directorio completo
# 1 -> nombre del directorio
# 2 -> vacio
# 3 -> directory
# si se le pasa una cadena nombre.archivo.ext con la comprobacion mime a 1
# pero el archivo no existe devuelve el cuarto parámetro con el valor 0
# si el nombre pasao es un archivo sin extension en el nombre

//< CODE

#  function dext(\$string,int) 
 
#
#
#
#
function strTo1($xp="",$p="",$r="",$n="2"){
if(!$xp) return "ERROR_1" ; //isset void
if(!$p) return "ERROR_2" ; //isset void
if(!$r) $r = $p;
return @preg_replace("@[$p]{{$n}}@si",$r,$xp);
}

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
$files = Array();
$subdirectorios = Array();
$handle = opendir($dir);
while ($file = readdir($handle)) {
if(is_dir($dir."/".$file) || $file=="." || $file=="..") {
    if($file!="." && $file!=".."){
    $subdirectorios[] = $dir."/".$file;
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









