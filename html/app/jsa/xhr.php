<?php

$RET = false ;

$_REQUEST["opt"] ? $recv = $_REQUEST["opt"] : $recv = false ;

switch($recv){

case 'how':


$RET=<<<RET
<div style="font-family:arial;font-size:18px;line-height:22px;letter-spacing:1.8px:">
<h5><b><u>C&oacute;mo funciona</u></b></h5>
<p>Abre una pesta&ntilde;as en el bot&oacute;n[+] para iniciar la edición.
Arrastra los elementos (tags html) 
del men&uacute; gr&aacute;fico (izquierda) a la pestaña activa y graba animaciones haciendo transiciones en cada objeto.</p>
<p>Una transici&oacute;n es el paso de un objeto de un estado a otro (cambio de valores de propiedades y/o estilos).</p>
<p>Una animaci&oacuten es un conjunto de transiciones.</p>
<p>Para grabar una transici&oacute;n pulsar bot&oacute;n rojo (grabar) despu&eacute;s de definirla. Las transiciones se definen cambiando sus valores, autom&aacute;ticamente estos quedan registrados, cuando sean del agrado, pulsar bot&oacute;n rojo para grabar. As&iacute; con todos los objetos.</p>

<p>
Cuando se abre una pestaña, automáticamente se edita el cuerpo del documento "body".
 No es necesario que exista grabación de ningún tag en concreto para realizar animaciones
  de objetos conjuntas.
  Un animación de objetos conjunta, es la animación de más de un objeto a la vez en una misma ventana.
</p><p>
  Los objetos se pueden animar conjuntamente o en solitario y obtener el código HTML/CSS/JAVASCRIPT y guardar las animaciones en el servidor como archivos nombredado.html
 </p> <p>

 Al arrastrar un elemento del menú gráfico a una pestaña, este se edita automáticamente (más adelante podrá cambiarse en opciones)

</p><p>

Al grabar una transición quedan registrados los estilos CSS disponibles, excepto los del grupo animation , que son globales a toda la animación y no es necesario grabarlos, la animación obtiene los últimos valores asignados a sus campos para su id concreto.

</p><p>

Para editar elementos, se hace pinchando en el botón "editar" de cada elemento.

</p><p>

Los últimos valores de cada id editado son guardados sin tener que grabarlos, de modo que si se hacen cambios en un objeto en concreto y se edita otro, al volver a editar el primero no se han perdido los valores que hayan sido modificados, por lo tanto se puede saltar de la edición de un tag (id) a otro (id) sin perder los cambios hechos sin necesidad de grabar una transición.
<br>
<br>
Al cambiar un valor de estilos, este se aplica automáticamante (onkeypress) al tag en cuestión en la pestaña de edición correspondiente y a la velocidad establecidad en "transition" para ese id concreto, de momento transition sirve para sólo eso, más adelante tomará más protagonismo, como por ejemplo, ajustar la animación a las velocidades dadas en "transition".

</p><p>

Para los valores de propiedades (src, innerHTML, title, etc..) sucede lo mismo, se obtienen los últimos valores establecidos para aplicárselos al elemento html que le corresponda.

(más adelante se podrán cambiar esos valores por medio de temporizadores y otras opciones de grabación)
<br>
Los cambios realizados en las propiedades se aplican al objeto en cuestión en su pestaña de edición correspondiente, a diferencia de los estilos, se hace "onchange" es decir que una vez se cambie un valor hay que pulsar enter o sacar el foco del cursor de la entrada correspondiente para hacer el cambio efectivo.

</p>
<p>
De momento no es posible editar las transiciones pero si eliminar las no deseadas haciendo click sobre ellas<br>

La animación "standard" funciona así:
<br><br>
Siendo la primera transición la posición inicial (0%) y la última el final (100%)
de forma que si hay más de dos transiciones grabadas, cada transición tiene la misma duración
 en relación al número de transiciones de ese id en concreto, si por ejemplo se graban cuatro transiciones...<br>
la primera es el 0% la segunda el 33,333% , tercera 66,667% la última el 100%
 , lo que quiere decir que un una animación de 10 segundos la velocidad de cambio entre transiciones sería de 3,3 segundos. Podría decirse que es una animación lineal.
<br>
Más adelante podrán editarse los porcentajes y otras propiedades desde los paneles gráficos
</p>
<p>
<figure style="width:65%">
<figcaption>1- La forma más sencilla de probarlo es abriendo una pestaña desde el botón [+] y grabar una transición del "body" </figcaption>
<img src="https://vtwitt.com/jsa/media/im.php?ratio=340&img=image/jsa/rec1.png">
</figure>

<figure  style="width:65%">
<figcaption>2- Cambiar el color de fondo, grabar y probar la animación animando el elemento desde "animar" o la pestaña desde "animar pestaña"</figcaption>
<img src="https://vtwitt.com/jsa/media/im.php?ratio=340&img=image/jsa/rec3.png">
</figure>

Animar el elemento muestra la animación del elemento independientemente del resto<br>
Animar pestaña anima todos los elementos de una pestaña<br>
Se pueden abrir todas las pestañas que se deseen. Más adelante se darán opciones para hacer combinaciones.<br>
El botón desagrupar permite editar en grupos de iframes "pestañas" y "animación", aunque no está aún muy desarrollado. en Chrome son resizables, en firefox no siempre.

Para que un elemento quede estático grabar sólo la transición de inicio de ese elemento<br>
</p>
<p>
Para obtener el código fuente de las animaciones usar el enlace "source" que se muestra al realizar una animación.<br>
Para Guardarla como .html en el servidor usar el botón "guardar como HTML" que se muestra al "animar pestaña"
</p>

<p>
<b><u>Controles Avanzados</u></b><br>

Los controles avanzados están en fase de desarrollo y se irán decumentando a medida que se vayan implementando. Estos se muestran al hacer click sobre el nombre de una propiedad o estilo.<br><br>
<br>
<br>
Hay dos categorías de controles avanzados,
los gráficos y los plugins.<br>

Los gráficos estás más orientados a los estilos y
 los plugins son utilidades para obtener recursos de red principalmente.<br><br>
 
 Un plugin que ya existe es la utilidad youtube-dl del atributo src de los elementos que lo admitan,
  este se despliega haciendo click sbre el texto del atributo "src" del control input del elemento, en "propiedades".<br><br>



Se pueden usar videos de twitter, youtube y otros sitios directamente
 desde el atributo src del video usando este enlace: <br><br>
 https://vtwitt.com/ydld.php?url=  ...url del video<br><br>
   Por ejemplo, https://vtwitt.com/ydld.php?url=https://twitter.com/i/status/1567403701114966016

<br><br>

También se pueden aplicar directamente los archivos del directorio de archivos desde el menu "archivo"<br><br>


</p>

Menús<br>

Archivo: Directorio con archivos clasificados por extensión listos para aplicar en algunas propiedades, por ejemplo, background-image , al previsualizar la imagen se puede aplicar su "src" al atributo css background-image del tag (id) editado, o al atributo src del tag, haciendo un click. Pero su interfaz es aún algo primaria aunque funcional<br> <br>

Conectividad: Objeto xhr ( funcion ajax() ) ciclo browser->xhr->http->server->SO->server->http->xhr->browser<br><br>
sirve para ejecutar aplicaciones como youtube-dl , ffmpeg, etc... haciendo pipes y circulando el flujo de datos de xhr a xhr<br><br>

Ver consola de pruebas  <a href="javascript:void(0)" onclick="cx = open('','cx','width=640,height=420,0,0,0');cx.location.replace(`https://vtwitt.com/ydld.php?url=https://twitter.com/i/status/1567176008167456769`)" target="CN">en este vídeo</a>

<p style="text-indent:33%"><a href="mailto:diariocompostela21@gmail.com">contacto</a></p>



</div>

RET;

break;


default:

$RET = "echo switch 1 default value - XHR Http 200 ok" ;

break;
}


if($RET) echo $RET;

