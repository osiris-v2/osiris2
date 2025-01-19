<?

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
