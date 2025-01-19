<?php

$dir = '../freedirectory/records';

if(!is_dir($dir)) mkdir($dir);

trim($_REQUEST['code']) ? $code = $_REQUEST['code'] : die('Err 1');


trim($_REQUEST['savename']) ? $namefile = $_REQUEST['savename'] : $namefile = rand(0,100000000);

$namefile = preg_replace("/[-]{2,}/","-",preg_replace("/[^a-z0-9ñáéíúó]/si","-",$namefile)).".html";

if(file_exists($dir."/".$namefile)) die("EXISTS FILE");
else file_put_contents($dir."/".$namefile,$code);

echo<<<FG
<div style="z-index:999999999;background:white;float:right;"> Guardado: <a href="$dir/$namefile" target="_blank">Abrir</a></div>
FG;


