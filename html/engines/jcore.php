<?php
session_start();
$permiso_publico_1 = 10;
#session_unset();



if (!$_SESSION["ARTICLE_ID"]):

$_SESSION["ARTICLE_ID"] = md5($_SESSION["REGUSER_EMAIL"]);

endif;

$fconf = '../conf2/jcores.conf';
include('../lib/php/aconf.php');
include('../lib/php/lib.php');
/*  jcore para econo */

/* editar articulo */


//requiere method post

if(!$_POST["divid"]):
	$divid = "div2";
else:
	$divid = $_POST["divid"];
endif;





if($_POST["edit"] == "article"):


if(!isset($_SESSION["REGUSER"]) || !$_SESSION['REGUSER']) {
	die("

{$divid}.innerHTML = `
<div style='margin:0 auto 0 auto;width:100%;'>
<h1 align=center style='padding:20px; background:white;'>Inicie sesión para Acceder</h1>
</div>
`


");
}


$_SESSION["SECURE_JSON"] = $_SERVER["DOCUMENT_ROOT"]."/textos/".md5($_SESSION["REGUSER_EMAIL"])."_article_secure.json";
$feb = $_SERVER["DOCUMENT_ROOT"]."/textos/".md5($_SESSION["REGUSER_EMAIL"])."_article.json";
$chfed = $_SERVER["DOCUMENT_ROOT"]."/textos/".md5($_SESSION["REGUSER_EMAIL"])."_article_pending.json";





if($_POST["action"]=="revisar"):

if(rename($feb,$chfed)){
/*was renamed*/
};

elseif($_POST["action"]=="revoke"):
if(rename($chfed,$feb)){
/* was renamed */
};

endif;





if(file_exists($chfed)) {$_SESSION["fileditbin"]  = $chfed;}
else { $_SESSION["fileditbin"] = $feb;}




echo<<<ARTICLE


addStyle(`


.article_main{


    background:#d3e0f9;
	width:860px;
	max-width:100%;
	margin:0 auto 0 auto;
	text-align:center;
	padding:10px;
}


.article_container{

    background:#031009;
	width:100%;
	max-width:100%;
	margin:0 auto 0 auto;
	text-align:center;
	padding:0px;
}

#edit_article_description {
	
	width:100%; max-width:100%;height:60px;
	resize:vertical;
}

#edit_article_01 {
	
	outline:none;
	text-align:justify;
	width:100%; max-width:100%;height:380px;
   background:white;
   border:solid 1px #234587;
   color:#090a0b;
  font-weight:bold;
  font-size:16px;
  font-family:ubuntu;
  resize:vertical;
}



#edit_a2 {

	background:#c0c0c0;
	text-align:left;
	width:100%;
	max-width:100%;
	height:auto;	
}

#edit_article_text {
	

	width:100%; max-width:100%;

}

#container_editor{
	
	padding:0;margin:0;
	width:100%;
	background:#032020;
}

.boton10x10 { 
background:#eae93d;
	border:solid 1px #A3127F ;
	margin:0;
	width:15px;height:15px;
padding:2.39px;
}

`,"idX_scxse34");



ARTICLE_MAIN = addPanel({className:"article_main"});

ARTICLE_EDIT = addPanel({className:"article_container"});
ARTICLE_EDIT.id = "article_edit_X";

TEXT_TITLE = addPanel({TAG:"input",type:"text",placeholder:"Text Title"});
TEXT_TITLE.id = "edit_article_text"
BUTTON_A1 = addPanel({TAG:"button",innerHTML:"Load<b style='color:red;font-family:impact;font-size:15px'>↑</b>",style:""});
TEXTAREA_A1 = addPanel({TAG:"textarea"});
TEXTAREA_A1.id = "edit_article_description" ;
CONTAINER_EDITOR = addPanel({})
CONTAINER_EDITOR.id = "container_editor"
EDIT_A2 = addPanel({TAG:"div",contentEditable:"false"});
EDIT_A2.id = "edit_a2" ;
TEXTAREA_A2 = addPanel({TAG:"iframe",src:"/engines/wys.php"});
TEXTAREA_A2.id = "edit_article_01" ;


SHOW_JSON = addPanel({style:"background:white;"}) ;

BOTON_GUARDAR = addPanel({
	TAG:"button",
	innerHTML:"Guardar",
	style:"margin:0 0 0 auto;right:0;"
	});


/*
OBRAS = addPanel({
	TAG:"img",
	src:"https://vtwitt.com/obras.jpg",
	style:"width:70px;height:70px;right:0;top:0;position:absolute;"
	});

moveTag(OBRAS,main);
*/


moveTag(TEXT_TITLE,ARTICLE_EDIT);
moveTag(br3 = addPanel({TAG:"br"}),ARTICLE_EDIT);
moveTag(TEXTAREA_A1,ARTICLE_EDIT);
moveTag(br2 = addPanel({TAG:"br"}),ARTICLE_EDIT);
moveTag(EDIT_A2,CONTAINER_EDITOR);
moveTag(TEXTAREA_A2,CONTAINER_EDITOR);
moveTag(CONTAINER_EDITOR,ARTICLE_EDIT);


moveTag(BOTTOM_FORM = addPanel({
	style:"width:100%;text-align:right;background:#fdeffa;"
	}),ARTICLE_EDIT);


moveTag(BOTON_GUARDAR,BOTTOM_FORM);
moveTag(BUTTON_A1,BOTTOM_FORM);





{$divid}.innerHTML = ""; 
moveTag(ARTICLE_MAIN,{$divid});



moveTag(RESPONSE_FORM = addPanel({
	style:"width:100%;height:auto;background:white;"
	}),ARTICLE_EDIT);

RESPONSE_FORM.id = "response_form";





moveTag(ARTICLE_EDIT,ARTICLE_MAIN);

moveTag(SHOW_JSON,ARTICLE_MAIN);
SHOW_JSON.id = "showjson";


ctrlg = false ;

BOTON_GUARDAR.onclick = function(){
if(!ctrlg) {
	ctrlg = confirm("Guardar el archivo lo modificará al contenido del editor");
} 
if(ctrlg){
ajax({
	datas:"edit=save&title="+edit_article_text.value+"&description="+edit_article_description.value+"&article="+escape(encodeURIComponent(edit_article_01.contentWindow.document.body.innerHTML)),
	location:"/engines/jcore.php",
	id:false,
	method:"POST",
	block:false,
	handler:false,
	eval:true
	});	
ctrlg = true;
};

};


BUTTON_A1.onclick = function(){
getId('edit_article_text').value = getId('jart_title').innerHTML;
getId('edit_article_description').value = getId('jart_description').innerHTML;
edit_article_01.contentWindow.document.body.innerHTML = getId('jart_article').innerHTML;
ctrlg = true;
};



moveTag(edit_bold = addPanel({TAG:"img",className:"boton10x10"}),EDIT_A2);
edit_bold.src= "/img/editor/bold-25x25.png";

edit_bold.onclick = function(){ 

edit_article_01.contentWindow.document.execCommand("bold", null);


  }


moveTag(edit_italic = addPanel({TAG:"img",className:"boton10x10"}),EDIT_A2);
edit_italic.src= "/img/editor/italic-50x50.png";


edit_italic.onclick = function(){ 

edit_article_01.contentWindow.document.execCommand("italic", null);


  }



moveTag(edit_underline = addPanel({TAG:"img",className:"boton10x10"}),EDIT_A2);
edit_underline.src= "/img/editor/underline-50x50.png";


edit_underline.onclick = function(){ 

edit_article_01.contentWindow.document.execCommand("underline", null);


  }



moveTag(edit_link = addPanel({TAG:"img",className:"boton10x10"}),EDIT_A2);
edit_link.src= "/img/editor/enlace-50x50.png";
edit_link.onclick = function(){ 


sel = edit_article_01.contentWindow.document.getSelection();

xlink =  prompt("Introduzca dirección del enlace","https://...");

if(!xlink) return;
else edit_article_01.contentWindow.document.execCommand("insertHTML", false,`<a href="`+xlink+`" target="_blank" rel="noopener noreferrer">`+sel+`</a>`);
  };




moveTag(add_img = addPanel({TAG:"img",className:"boton10x10"}),EDIT_A2);
add_img.src= "/img/editor/image.png";
add_img.onclick = function(){ 


xlink =  prompt("Introduzca la url de la imagen","https://...");

if(!xlink) return;
else edit_article_01.contentWindow.document.execCommand("insertHTML", false,`<img src="`+xlink+`" style="max-width:100%;max-height:100%;">`);
  };



moveTag(add_video = addPanel({TAG:"img",className:"boton10x10"}),EDIT_A2);
add_video.src= "/img/editor/video.png";
add_video.onclick = function(){ 


xlink =  prompt("Introduzca la url del video","https://...");

if(!xlink) return;
else edit_article_01.contentWindow.document.execCommand("insertHTML", false,`

<video src="`+xlink+`" controls style="width:auto;height:auto;max-width:100%;"></video>

`);
  };






utiljs = "/engines/utileditor.js?v=0.20";

if(!document.querySelector('script[src="'+utiljs+'"]')){
script = document.createElement("script");
script.src = utiljs;
script.type = "text/javascript";
script.charset = "utf-8";
document.head.append(script);

}


ARTICLE;



if(file_exists($chfed)):
echo<<<JS
article_edit_X.innerHTML = `
<h1 style="background:#101016;color:#eddaaf;padding:10px;margin:10px;">
Pendiente de revisión
<br>
<a href="javascript:void(0)" onclick='
ajax({
	datas:"edit=article&action=revoke",
	location:"/engines/jcore.php",
	id:false,
	method:"POST",
	block:false,
	handler:false,
	eval:true
	});	
' style='color:#edef2a;'>REVOCAR PETICIÓN</a>
</h1>
`;
ajax({
	datas:"edit=showjson&nohead=true",
	location:"/engines/jcore.php",
	id:"showjson",
	method:"POST",
	block:false,
	handler:false,
	eval:false
	});	
JS;
exit;
endif;



elseif($_POST["edit"] == "save"):


if(!$_SESSION["REGUSER"]) {
	die("

{$divid}.innerHTML = `
<div style='margin:0 auto 0 auto;width:100%;'>
<h1 align=center style='padding:20px; background:white;'>Se ha cerrado la sesión</h1>
</div>
`;


");
}


//$fileditbin = md5($_SESSION["REGUSER_EMAIL"]);
$sfa = $_SESSION["fileditbin"];


$title = urldecode(strip_tags($_REQUEST["title"]));

if(!$title) $title = "Título" ;

$article = addcslashes(trim(rawurldecode($_REQUEST["article"])),"\"\n");

if(!$article) $article = "Artículo";

$description = addcslashes(urldecode(strip_tags(trim($_REQUEST["description"]))),"\n");


if(!$description) $description = "Descripción";


$time = time();

$JSON=<<<Json
{
"id":"{$_SESSION["ARTICLE_ID"]}",
"time":"{$time}",
"title":"{$title}",
"description":"{$description}",
"article":"{$article}"
}
Json;

@file_put_contents($sfa,$JSON);
@file_put_contents($_SESSION["SECURE_JSON"],$JSON);
echo "response_form.innerHTML = 'Guardado en: {$time}';";



elseif($_POST["edit"]=="showjson"):


$user2 = "";

if($_SESSION["REGUSER_PERM"] >= $permiso_publico_1)
	{
$jsfile = basename($_SESSION["fileditbin"]);
$user2=<<<HTML
<button onclick='ajax({
datas:"action=publicar&file={$jsfile}",
location:"/engines/jcore2.php",
method:"POST",
eval:true,
	})'>
<b>Publicar</b>
</button>

HTML;
} elseif($_SESSION["REGUSER_PERM"] < $permiso_publico_1)
	{

		$user2 = '<a href="javascript:void(0);" onclick="solicitar_revision(`¡param`)">Enviar a Revisión</a>';

}

$sfa = $_SESSION["fileditbin"];
$jsonurl = "/textos/".basename($_SESSION["fileditbin"]);
$sfae=<<<ARTC
<hr>
<a href='{$jsonurl}' target='_blank'><b>ver JSON</b></a>
-
{$user2}

<hr>
ARTC;


if($_POST["nohead"]==true) $sfae = "" ;


if(file_exists($sfa)){

$rjson = file_get_contents($sfa);

$data = json_decode($rjson,true);

echo<<<rjson
$sfae
<div style="padding:2%;width:96%;text-align:left;">
<div id="jart_title" style="font-size:32px;">{$data["title"]}</div>
<div id="jart_description" style="padding:20px;">{$data["description"]}</div>
<div id="jart_article">{$data["article"]}</div>
</div>

rjson;


} else echo "Grabe para iniciar ".basename($sfa);

exit;
endif;



if($_POST["edit"]):
echo<<<AJAX
ajax({
	datas:"edit=showjson",
	location:"/engines/jcore.php",
	id:"showjson",
	method:"POST",
	block:false,
	handler:false,
	eval:false
	});	
AJAX;
endif;


