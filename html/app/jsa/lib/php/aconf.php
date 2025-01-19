<?php
$__x_DEBUG = "";
$__x_LISTA_VARIABLES = "";
function pecho($data,$reten="0"){
if($reten>0){echo "<p>".htmlentities($data)."</p>";}else{return "<p>".htmlentities($data)."</p>";}
}
if(!isset($fconf)) {$fconf ="conf.conf";}
if(file_exists($fconf)){$__x_DEBUG .= pecho("Existe fileconf $fconf");/*existe fileconf*/}else{
/*no existe fileconf la creamos*/
$time = time();
$autoconf=<<<CNF
#archivo de configuracion creado automáticamente
AUTOCONF = true
AUTOCONF_TIME = {$time}
AUTOCONF_INFO = include path /var/www/share/php
_SYS_DEBUG = 1
_SYS_VARS = 1
#continue
CNF;
$_SPECIALCONF = Array();
if(file_put_contents($fconf,$autoconf)){$__x_DEBUG .= pecho("Creado fileconf automático como: ".$fconf);}}
$read = file_get_contents($fconf,"r");
$filelines = explode("\n",$read);
$nlines = count($filelines);
$lineas = pecho("Filas en fileconf: ".$nlines);
if($read){ 
$__x_DEBUG .= pecho("Leido fileconf");
$__x_DEBUG .= $lineas;
$__x_DEBUG .= "<pre>".pecho("Contenido fileconf:\n\n".$read)."</pre>";
}else {
$__x_DEBUG .= pecho("NO SE HA PODIDO LEER fileconf: ".$fileconf);
$__x_DEBUG .= $lineas;
} /* Se interpreta archivo de configuracion */
$__x_DEBUG .= pecho ("interpretación de configuración , lectura línea a línea");
$LCONF = "";
$_CONF = Array();
for($i=0;$i<$nlines;$i++){
$linea = $filelines[$i];    
if(preg_match("/^#/", $linea)){    
/*línea $i es un comentario*/
$__x_DEBUG .= pecho("Línea $i ES UN COMENTARIO: ".$linea); 

} elseif(preg_match("/([a-z0-9_\[\]]+)+ {0,}= {0,}(.+)/si",$linea,$match,PREG_OFFSET_CAPTURE)){
/*linea $i es una variable correctamente configurada*/

$__x_DEBUG .= pecho("Línea $i ES VARIABLE OK: ".$linea);
$_CONF[] = Array("var"=>trim($match[1][0]),"value"=>trim($match[2][0]),"line"=>trim($match[0][0]));
}else{

/*error al declarar variable*/
if(trim($linea!="")){
$control[$i] = "error";
$__x_DEBUG .= pecho ("<li>Línea $i ES ERROR: ".$linea);
}
}
unset($linea);unset($match);
}
$nvars = count($_CONF);
$__x_DEBUG .= pecho("Se han detectado $nvars variables correctas");
for($i=0;$i<$nvars;$i++){
$n=$i+1;



$_ASX_varname=$_CONF[$i]["var"];
$_ASX_value=$_CONF[$i]["value"];
$_ASX_var= "$".$_CONF[$i]["var"];
$namevar = $_CONF[$i]["var"];




if(preg_match("/^[@](.+)$/si",$_ASX_value,$match_exec_php)) {

eval('$_ASX_value='.$match_exec_php[1].';');



$parse=<<<PRS
$namevar=$_ASX_value
PRS;
parse_str($parse);

if(is_resource($_ASX_value)){

    // aquí se intenta dar a una variable el valor
    // de una función php, como fopen que devuelve un resource
    // sin embargo no es válido hacerlo por eval
    // sería hacer , $id =  $_ASX_value que es igual ej, fopen();
    
    
$line = ($n+$i)-1;

$namevar = $_ASX_value;

}

$_SPECIALCONF[$_ASX_var] = $_ASX_value;

} else{




$parse=<<<PRS
$namevar="$_ASX_value";
PRS;

parse_str($parse,$array);





foreach($array as $var => $value){

 eval('$$var='.$value.';');

$_SPECIALCONF[$var] = $_ASX_value;

} 



} 

$_ASX_valuentities=@htmlentities(@stripslashes($_ASX_value));
$_ASX_line=$_ASX_varname."=".$_ASX_valuentities;
$__x_LISTA_VARIABLES.=<<<VARS
<hr>Variable {$n}:<br>
      Nombre: {$_ASX_varname}<br>
       Valor: {$_ASX_valuentities}<br>
       Linea: {$_ASX_line}
VARS;
}
unset($_ASX_VAR_X);unset($_ASX_var);unset($_ASX_line);unset($_ASX_value);unset($_ASX_valuentities);unset($_ASX_varname);
if($_SYS_DEBUG){echo "<hr>".$__x_DEBUG."";}
if($_SYS_VARS){echo $__x_LISTA_VARIABLES."<hr>";}
unset($__x_DEBUG);unset($__x_LISTA_VARIABLES);
#END
