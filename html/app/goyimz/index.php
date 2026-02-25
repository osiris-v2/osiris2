<?php
header("location:search");
exit;





function makecard($params = []) {
    $defaults = [
        "title"       => "Mi Sitio Web",
        "description" => "Bienvenido a mi página personal.",
        "image"       => "https://tusitio.com/default-image.jpg",
        "url"         => (isset($_SERVER['HTTPS']) ? "https" : "http") . "://$_SERVER[HTTP_HOST]$_SERVER[REQUEST_URI]",
        "site_name"   => "Mi Marca",
        "twitter_id"  => "@tu_usuario",
        "card_type"   => "summary_large_image"
    ];
    $card = array_merge($defaults, $params);
    $html = "\n";
    $html .= '<meta property="og:type" content="website">' . "\n";
    $html .= '<meta property="og:url" content="' . htmlspecialchars($card['url']) . '">' . "\n";
    $html .= '<meta property="og:title" content="' . htmlspecialchars($card['title']) . '">' . "\n";
    $html .= '<meta property="og:description" content="' . htmlspecialchars($card['description']) . '">' . "\n";
    $html .= '<meta property="og:image" content="' . htmlspecialchars($card['image']) . '">' . "\n";
    $html .= '<meta property="og:site_name" content="' . htmlspecialchars($card['site_name']) . '">' . "\n";
    $html .= '<meta name="twitter:card" content="' . htmlspecialchars($card['card_type']) . '">' . "\n";
    $html .= '<meta name="twitter:title" content="' . htmlspecialchars($card['title']) . '">' . "\n";
    $html .= '<meta name="twitter:description" content="' . htmlspecialchars($card['description']) . '">' . "\n";
    $html .= '<meta name="twitter:image" content="' . htmlspecialchars($card['image']) . '">' . "\n";
    return $html;
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
      <meta charset="UTF-8">
  <meta name="viewport" content="initial-scale=1, maximum-scale=1">
<?php 
echo makecard([
        "title" => "Goyim Nation of Goys",
        "description" => "Goym World United",
        "image" => "https://goyimz.duckdns.org/img/goyimzh.png"
    ]);
?>
<style>
body{
background:#000000;
}
</style>
</head>
<body>
<center>
<img src="img/goys1.png" style="max-width:100%">
<br><br>
<a href="index.goy" style="font-size:36px;color:#eaf9d4;text-decoration:underline">
    Atraviesa la Frontera<br>
Sitio no apto para Judíos
</a>
</center>
</body></html>