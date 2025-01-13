<?php
session_start();

//sleep(2);

$_REQUEST["x"] ? $x = $_REQUEST["x"] : $x = false ;


if(!$_SESSION["REGUSER"]):


if($_REQUEST["divid"]){

	$divid = $_REQUEST["divid"];
}  else {
	$divid="panelDerecha";
}

die("

<div style='width:93.7%;padding:3%;
background:#4d4d4d;border:solid 2px #a77a7a;font-size:3vw;
color:#fcecfd;text-align:center;' align=center>

Se necesita estar registrado para entrar.<br>

<button onclick='

ajax({
datas:`nodatas`,
method:`POST`,
location:`/engines/rusr.php`,
id:`$divid`,
handler:`UNIKE1`,
block:true	
})

'>Entrar</button>

</div>

	");

endif;


if($x=="intro"):
echo<<<INTRO
<div style="background:#caeb86;width:50%;">
<h2 align=center>Resumen de actividades y usuario</h2>

</div>
INTRO;
elseif($x=="introEcono"):
echo<<<INTRO
<div style="margin:0 auto 0 auto;background:#caeb86;width:50%;">
<h1>EconoApp</h1>
<h2 align=center>Resumen de actividades y usuario</h2>
</div>
INTRO;
elseif($x=="frecuencias"):
echo<<<FRC
 <iframe src="/lib/xdev/frecuencias.html" style="width:50vw;height:50vw" frameborder=0></iframe>
FRC;
elseif($x=="tv"):
echo<<<FRC
 <iframe src="/tv.php" style="width:75vw;height:100vh" frameborder=0></iframe>
FRC;
elseif($x=="jsa"):
echo<<<FRC
 <iframe src="https://vtwitt.com/jsa" style="width:75vw;height:100vh" frameborder=0></iframe>
FRC;
elseif($x=="videos"):
echo<<<FRC
 <iframe src="/likes/index.php" style="width:75vw;height:100vh" frameborder=0></iframe>
FRC;
elseif($x=="GuestEditor"):
echo<<<FRC
 <iframe src="/economa.html" style="width:75vw;height:100vh" frameborder=0></iframe>
FRC;
endif;
?>