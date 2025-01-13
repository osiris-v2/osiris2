<?php
session_start();
//session_unset();exit;
#$_SESSION["REGUSER"] = 1;
#$_SESSION["REGUSER_PERM"] = 1 ;
#$_SESSION["REGUSER_EMAIL"] = $_SERVER["REMOTE_ADDR"] ;

$_S_N = "/engines" ;

$ano = date("Y");
echo<<<JS
XX = addPanel({innerHTML:"<div style='color:#118dca;border: outset 2.3px #da029d;background-color:#9ffe11;height:auto;font-weight:bold;font-size:18px;'>&copy; {$ano} "+Version+"</div>"});
moveTag(XX,footer);
div000.style.width = "100%";
div000.style.textAlign = "right";
setInterval(
function(){
div000.innerHTML = new Date();
r = getRand(120,255);
g = getRand(120,255); 
b = getRand(120,255);
div000.style.color = "rgba("+r+","+g+","+b+",1)";
div000.style.backgroundColor = "rgba(0,0,0,1)";
}
,1000);
JS;

echo<<<JS
ajax({
datas:"divid=div2&x=introEcono",
method:"POST",
location:"{$_S_N}/jxp.php",
id:"div2",
handler:false,
block:false
});
JS;

if($_SESSION["REGUSER"]):

echo<<<MENUJS
addStyle(`
.menu_reg{
	display:inline-block;
	color:gold;
}

.menu_link{
	color:blue;
	padding:5px;	
	cursor:pointer;
	font-size:16px;
	font-weight:bold;
	display:inline-block;
	border:solid 1px #336ef6;
	background:#fefafe;
}
`,"style_feqdsde_23231");
MENU = addPanel({className:"menu_reg"}) ;
moveTag(MENU,divMenu);

EDITAR = addPanel({TAG:"span",className:"menu_link"}) ;
EDITAR.innerHTML = "Publicar" ;
EDITAR.onclick = function(){
ajax({
datas:"edit=article",
id:false,
eval:true,
location:"{$_S_N}/jcore.php",
block:true,
handler:"BCKxS",
method:"POST"
});
} ;

moveTag(EDITAR,MENU)

MENUJS;

endif;


?>








