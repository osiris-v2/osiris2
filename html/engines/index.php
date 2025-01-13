<?php
session_start();


if($_SESSION["REGUSER"]):

echo<<<ENG
div2.innerHTML = `
<div style="background:#222425;padding:20px;">
<a href="/public.html" style="font-size:29px;font-weight:bold;font-family:ubuntu;text-decoration:underline;color:#bcaaef">PUBLICAR</a></h1>
</div>
`;
ENG;

else:
echo<<<JS
ajax({
datas:"nodata",
method:"POST",
location:"/engines/rusr.php",
id:"div2",
eval:false,
handler:"UNIKH",
block:false
});
JS;
endif;	













?>