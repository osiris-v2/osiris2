<?php
session_start();
#session_unset();
$fconf = '../conf2/jcores.conf';
include('../lib/php/aconf.php');
include('../lib/php/lib.php');


/*
if (!$_SESSION["ARTICLE_ID"]):

echo<<<EXIT
alert(`

Session Error. Se ha podido cerrar.

`);
EXIT;

exit;

endif;

*/

if(!isset($_SESSION["REGUSER"]) || !$_SESSION['REGUSER']) die("<center><h1 style='color:#abc922;background:black;'>Inicia Sesión Para Publicar</h1>
<center><img src='/img/oluz.png' style='width:auto;height:auto;;max-height:80vh'>
<img src='/img/oluz2.png' style='width:auto;height:auto;;max-height:80vh'>
</center>
  ");
$mysqli = new mysqli($mysql_host, $mysql_usr, $mysql_psd, $mysql_bd);



#echo "alert('".$_SESSION["PERM"] ."');"; 
if($_SESSION["REGUSER_PERM"] >= $USR_PERM_PUBLIC && isset($USR_PERM_PUBLIC)):


if($_POST["action"]=="publicar"):


$JSON_FILE = $PATH_PUBLIC_TXT."/".$_POST["file"];

$data = file_get_contents($JSON_FILE);

if( ! $data) die("alert('nodata_err');");

$data = json_decode($data,true);


if($_SESSION["ARTICLE_ID"]==""):

echo<<<JS
alert(`
Article_id Error
`);
JS;
exit;
endif;


$sql = "select id from edit_files where user_id='".$_SESSION["REGUSER_ID"]."' && file_id='".$_SESSION["ARTICLE_ID"]."'";
$rquery = $mysqli->query($sql);
$article_exists =  $rquery->num_rows;



//echo "alert('$article_exists');";


if($article_exists === 0): //no existe articulo en la bd


$sql = "insert into edit_files(user_id,file_id,filecode,format,title,description,article,time)
 values('".$_SESSION["REGUSER_ID"]."','".$_SESSION["ARTICLE_ID"]."','".$_POST["file"]."','json','".$data["title"]."','".$data["description"]."','".$data["article"]."',".$data["time"].");";


echo "alert(`Registro nuevo: 

{$_SESSION['ARTICLE_ID']}

`);";

elseif($article_exists==1):

$sql = "update edit_files set title='".addcslashes($data["title"],"'")."',description='".addcslashes($data["description"],"'")."',article='".addcslashes($data["article"],"'")."'  where user_id='".$_SESSION["REGUSER_ID"]."' && file_id='".$_SESSION["ARTICLE_ID"]."'";

#echo "alert(`{$sql}`);";


echo "alert(`Registro update: 

{$_SESSION['ARTICLE_ID']}

`);";




else:
	/*error var*/
endif;

if($mysqli->query($sql)){


echo "response_form.innerHTML= `Artículo Publicado: ".time()."`;";

	} else{ die("
	alert(`
	{$mysqli->error} 
	ERRRO`);
	");
  }

//$str = join($rquery);
/*
echo<<<JS
alert(`{$str}

{\$_SESSION["ARTICLE_ID"]}
{\$data["time"]}

`);
JS;
*/

endif;



#fin post action=publicar
endif;







if ($_POST["action"] == "resumen"):

if($_SESSION["REGUSER_PERM"] >= $USR_PERM_PUBLIC && isset($USR_PERM_PUBLIC)):


$sql = "SELECT title, description, article FROM edit_files";



$result = $mysqli->query($sql);

if ($result->num_rows > 0) {
  // Loop through each article row
  while($row = $result->fetch_assoc()) {
    $title = $row["title"];
    $description = $row["description"];
    $article = $row["article"];

    // Format the article using the function
    $formattedArticle = formatArticle($title, $description, $article);

    // Output the formatted article (replace with your display logic)
    echo "<div style='background:white;padding:3vw;'>$formattedArticle</div>";
    echo "<hr>"; // Add a separator between articles
  }
} else {
  echo "No articles found.";
}


else:
echo "<h1 style='background:white;'> Debe estar registrado para ver este contenido </h1>";
exit;
endif;


endif;
