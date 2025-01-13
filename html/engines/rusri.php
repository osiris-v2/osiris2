<?php
session_start();
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_STRICT);

$action = filter_input(INPUT_POST,"action",FILTER_DEFAULT);
$usr = filter_input(INPUT_POST, "usr", FILTER_CALLBACK, array("options" => "f_usr"));
$pswd = filter_input(INPUT_POST, "pswd", FILTER_CALLBACK, array("options" => "f_pswd"));
$repswd = filter_input(INPUT_POST,"repswd",FILTER_CALLBACK, array("options" => "f_pswd"));
$email = filter_input(INPUT_POST,"email",FILTER_VALIDATE_EMAIL);



function f_pswd($param) {

    if (strlen($param) >= 6 && strlen($param) <= 64) {
        $return = preg_match("/^([a-z0-9_!\$%\+&\*\-#@])+$/si", htmlspecialchars_decode($param));
        if ($return) {
            $ar[0] = 1;
            $ar[1] = $param;
            $ar[2] = strtoupper(hash("sha256", $param, false));
            return $ar;
        } else {
            return 2;
        }
    } else {
        return 3;
    }
}

function f_usr($param) {

    if (strlen($param) >= 4 && strlen($param) <= 64) {
        $return = preg_match("/^([a-z0-9_])+$/si", htmlspecialchars_decode($param));
        if ($return) {
            $ar[0] = 1;
            $ar[1] = $param;
            return $ar;
        
        } else {
           $f_email = filter_var($param,FILTER_VALIDATE_EMAIL);
           if($f_email) {
               $ar[0] = 2;
               $ar[1] = $f_email;
               return $ar;
               
           }else {
               return 2;
               
           }
        }
    } else {
        return 3;
    }
}




function valida_usr($usr){


switch($usr):
    
    case is_array($usr) && $usr[0] == 1:
        $usr = $usr[1];
        $return[0]=1;
        $return[1] = $usr;
return $return;       

case is_array($usr) && $usr[0] == 2:
        $usr = $usr[1];
        $return[0]=2;
        $return[1] = $usr;
return $return;       

    case 2:
         $return[0]=0;
        $return[1] = "<p>El formato del nombre: sólo puede contener letras, números y guión bajo o dirección de correo válida</p>";
return $return;

    case 3:
         $return[0]=0;
        $return[1] = "<p>El nombre de usuario debe tener entre ocho y sesentaycuatro caracteres de longitud</p>"; 
return $return;  




    default:
       $return[0]=0;
        $return[1] = "Error desconocido";
return $return;        

            
endswitch;

  $return[0]=0;
        $return[1] = "USR EN BLANCO";
        return $return;

}



function valida_pswd($pswd,$repswd="///"){

    if($repswd=="///"){
       /* continue;*/
  
    } else{
        
        if($pswd[2] != $repswd[2]){
          
               $return[0]=0;
        $return[1] = "Contraseña y Repetición deben ser iguales";
        return $return;
        
    }
    }
    
    
switch($pswd):
    
    case is_array($pswd) && $pswd[0] == 1:
        $pswd_hash = $pswd[2];
        $pswd = $pswd[1];
        $return[0]=1;
        $return[1] = $pswd;
        $return[2] = $pswd_hash;
        return $return;
  
    case 2:
        $return[0]=0;
        $return[1] =  "<p>El formato de la contraseña : Puede contener letras, números y los caracteres que aparecen encerrados entre paréntesis y en negrita(<b> @ _ # ! \$ % + & * - </b>)</p>";
        return $return;
 
    case 3:
        $return[0]=0;
        $return[1] =  "<p>La contraseña debe ser mayor o igual a ocho caracteres de longitud y menor o igual de sesentaycuatro</p>"; 
        return $return;
     
    default:
        $return[0]=0;
        $return[1] =  "Error desconocido";
        return $return;

            
endswitch;

$return[0]=0;
$return[1] =  "Campo password en blanco no sirve";
return $return;

}


function valida_email($email){

switch($email):
    
    case "":
       
        $return[0]=0;
        $return[1] = "<p>Email inválido</p>";
          return $return;
         
    default:
        $return[0]=1;
        $return[1] = $email;
        return $return;

    
    
endswitch;

 $return[0]=0;
        $return[1] = "<p>Email inválido-vacío</p>";
          return $return;

}






switch($action):

    
    case 'registro':
if($usr && $pswd && $email && $repswd){
    
    $ret_usr = valida_usr($usr);
    $ret_pswd = valida_pswd($pswd,$repswd);
    $ret_email = valida_email($email);
    
    
    if($ret_pswd[0]===1 && $ret_usr[0]===1 && $ret_email[0]===1){
     $x = new registro();
        $x->registra($ret_usr,$ret_pswd,$ret_email);

    } else {
          echo "<p>EL REGISTRO CONTIENE ERRORES</p>";
     }
    
} else {
    
    $ret_usr = valida_usr($usr);
    $ret_pswd = valida_pswd($pswd,$repswd);
    $ret_email = valida_email($email);

       echo "<p>EL REGISTRO CONTIENE ERRORES</p>";

    
}

break;

    case 'acceso':

if($usr && $pswd){
    
         $ret_usr = valida_usr($usr);
     $ret_pswd = valida_pswd($pswd,"///");
      if($ret_pswd[0]===1 && $ret_usr[0]===1){
  
                   $x = new registro();
                  $x->acceso($ret_usr,$ret_pswd);
       
       
    } elseif($ret_pswd[0]===1 && $ret_usr[0]===2){

                    $x = new registro();
                  $x->acceso($ret_usr,$ret_pswd);
        
    }else {
   
       echo "<p>USUARIO O EMAIL INCORRECTO</p>";
     }
  
    
} else {
    
      echo "<p>Faltan entradas por rellenar</p>";
    echo "<p>stop por errores</p>";
    
}
        

break;

    default:
        echo "<h2>ERROR void action</h2>";
break;

endswitch;







class registro{

    public $mysqli_rsc;
    private $host = "localhost";
    private $usr = "root";
    private $psd = "osiris";
    private $bd = "osiris_web";
    private $table = "users";

    
public function __construct() {
  $this->mysqli_rsc = new mysqli($this->host, $this->usr, $this->psd, $this->bd);
  
 
}
    

public function registra($user,$password,$email){
    $query = "select count(usr) as DUPLI from ". $this->table." where usr='$user[1]'";
    if($result=$this->mysqli_rsc->query($query)){
        $obj=$result->fetch_object();
        
        if($obj->DUPLI>0){
           
            echo "<p>ERROR USUARIO EXISTIA YA</p>";
            
        }else{
   
            $query = "select count(email) as DUPLI from ". $this->table." where email='$email[1]'";
            
        if($result= $this->mysqli_rsc->query($query)){
            
            $obj=$result->fetch_object();
        
        if($obj->DUPLI>0){
            
            echo "Ya existe una cuenta con ese EMAIL";
        } else {
    
          $query = "insert into ".$this->table."(usr,pswd,email) values('$user[1]','$password[2]','$email[1]');"; 
   
   if($this->mysqli_rsc->query($query)){
       echo "<p>SE HA EFECTUADO EL ALTA DE USUARIO</p>";   
    } else {
        echo "<p>ERROR AL CREAR USUARIO NUEVO<br> Compruebe que no exista usuario para <b>$email[1]</b><br>";
        echo "<a href=\"javascript:alert('servicioi recuperacion de cuenta');\">recordar contraseña</a></p>";
        }}} else{  echo "<p>Error query de comprobacion email</p>"; }
        }
    } else {
        echo "<p>Error query de comprobacion usr</p>". mysqli_error($this->mysqli_rsc);
    }
}



public function acceso($user,$password){ 
    if($user[0]===1) {$acceso="usr";}
    elseif($user[0]===2) {$acceso = "email";}
  $query ="select * from ".$this->table." where $acceso='".$user[1]."' ";
    if($result=$this->mysqli_rsc->query($query)){
       $obj = $result->fetch_object(); 
        if($obj){
            if($obj->pswd == $password[2]){
               /**
                * $_SESSION["REGUSER"] controla la session activa a true
                * **/
               $_SESSION["REGUSER"] = true;  
               $_SESSION["REGUSER_ID"] = $obj->id ;
               $_SESSION["REGUSER_PERM"] = $obj->perm ;     
                $_SESSION["REGUSER_EMAIL"] = $obj->email ;         
echo "<p>Acabas de validarte en el sistema <a href=\"javascript:location.reload()\">ACTUALIZAR</a>
    <!-- DISABLED
    <br> o se redireccionará en 3 segundos <meta http-equiv=\"refresh\" content=\"3; url=https://www.compostela21.com?component=usuarios\" /> 
    -->
    </p>";
                
            } else {
                
                echo "<p>CONTRASEÑA INVÁLIDA</p>";
            }
        } else{
            echo "<p>USUARIO O EMAIL INCORRECTO</p>";
        }
  } else {
        echo "<p>No se he ejecutado el query</p>"; 
    }
    
}



public function __destruct() {
  $this->mysqli_rsc->close();
}

}
