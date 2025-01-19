






document.write("<div id='PRUEBA'>Response on DIV</div></body></html>")

//ajax("data=UNO&data=dos",'PRUEBA','xhr.php','POST','alert("Ajax 1 Modo escritura Div = ")',"=")


ajax("data=UNO&data=dos",'PRUEBA','xhr.php','POST','/*JS*/',"+='<br>RESPONSE<br>'+")

//ajax("data=UNO&data=dos",0,'xhr.php','POST','alert("Ajax 3 Eval Response")')
