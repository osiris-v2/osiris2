<?php
session_start();
//session_unset();session_destroy();
if(isset($_POST["action"]) && $_POST["action"]=="closesession"):
session_unset();

elseif(isset($_SESSION["REGUSER"]) && $_SESSION['REGUSER']!=""):

//print_r($_SESSION);
echo<<<LOGED

<div style="padding:50px">
 <h3>ARE LOGED</h3>

<button onclick='ajax({
  location:"/engines/rusr.php",
  method:"POST",
  datas:"action=closesession",
  eval:false,
  id:"regInf"
  });top.location.reload()'> Cerrar Sesión </button>

</div>

LOGED;

/*  está logueado se sale   */

exit;

elseif(isset($_POST["action"]) && $_POST["action"]!=""):
echo<<<REG
action reg<!-- Action REg -->
REG;

include 'rusri.php';

exit;


#else:

#echo "<!--REGISTRO acceso-->";

endif;






?>


<style>
/* Estilos generales */

.container {
  max-width: 800px;
  margin: 20px auto;
  padding: 20px;
  background-color: #fff;
  border-radius: 10px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

/* Estilos para el título */
h2 {
  text-align: center;
  font-size: 24px;
  color: #333;
  margin-bottom: 20px;
}

/* Estilos para los enlaces de registro */
.lreg {
  text-align: center;
  margin-bottom: 20px;
}

.lreg a {
  text-decoration: none;
  color: #007bff;
  font-size: 18px;
  margin: 0 10px;
  cursor: pointer;
  transition: color 0.3s;
}

.lreg a:hover {
  color: #0057b7;
}

/* Estilos para los formularios */
.regmenus {
  display: none;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
}

.regmenus.active {
  display: block;
}

.regmenus input[type="text"],
.regmenus input[type="password"],
.regmenus button {
  width: 100%;
  padding: 10px;
  margin-bottom: 10px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.regmenus button {
  border: none;
  background-color: #007bff;
  color: #fff;
  cursor: pointer;
  transition: background-color 0.3s;
}

.regmenus button:hover {
  background-color: #0057b7;
}

/* Efectos hover dinámicos */
.regmenus:hover {
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.2);
}
</style>


<div class="container">
  <h2>Usuarios</h2>
  <div class="lreg">
    <a class="areg" href="javascript:void(0);" onclick="dmenu('registro','regmenus')">Registro</a>
    <span> / </span>
    <a class="areg" href="javascript:void(0);" onclick="dmenu('acceso','regmenus')">Acceso</a>
  </div>
  
  <div id="registro" class="regmenus">
    <div>
      <p>Para registrarte como usuario tan solo has de rellenar correctamente el formulario. Se necesita un nombre de usuario, una contraseña y una dirección de Email. Una vez registrado, puedes acceder a tu cuenta de manera inmediata. Sin embargo, para obtener todas las funcionalidades es preciso confirmarla.</p>
    </div>
    <input type="text" id="usr" placeholder="Usuario"><br>
    <input type="text" id="email" placeholder="Email"><br>
    <input type="password" id="pswd" placeholder="Contraseña"><br>
    <input type="password" id="re_pswd" placeholder="Confirmar Contraseña"><br>
    <button onclick="ajaxPost('action=registro&usr='+getIdValue('usr')+'&repswd='+getIdValue('re_pswd')+'&pswd='+getIdValue('pswd')+'&email='+getIdValue('email'),'reginfo','/engines/rusr.php','POST')">Registrar</button>
  </div>
  
  <div id="acceso" class="regmenus">
    <div>
      <p>Para acceder, si eres usuario, introduce tu nombre de usuario o email y tu contraseña. ¡Ya puedes acceder!</p>
    </div>
    <input type="text" id="usr_a" placeholder="Usuario"><br>
    <input type="password" id="pswd_a" placeholder="Contraseña"><br>
    <button onclick="ajaxPost('action=acceso&usr='+getIdValue('usr_a')+'&pswd='+getIdValue('pswd_a'),'reginfo','/engines/rusr.php','POST')">Entrar</button>
  </div>
  
  <div id="reginfo"></div>
</div>
