<!DOCTYPE html>
<html><head><title>editor</title>
<script type="text/javascript">



function eliminarHtml(html) {
  // Expresión regular para eliminar etiquetas HTML
  const regex = /(<([^>]+)>)/gi;

  // Eliminar etiquetas HTML del contenido
  const textoPlano = html.replace(regex, '');

  // Devolver el texto plano
  return textoPlano;
}






onload = function(){

document.body.addEventListener('paste', function(event) {

  event.preventDefault();
  const contenidoPegado = event.clipboardData.getData('text/html');
  const textoPlano = eliminarHtml(contenidoPegado);
  document.execCommand("insertHTML",false,textoPlano);
  console.log('paste Texto plano:', textoPlano);


});


document.body.addEventListener('drop', function(event) {

  event.preventDefault();
  const contenidoPegado = event.dataTransfer.getData('text/html');
  const textoPlano = eliminarHtml(contenidoPegado);
  document.execCommand("insertHTML",false,textoPlano);
  console.log('drop Texto plano:', textoPlano);


});


}
</script>

</head><body style="overflow:auto;position:absolute;width:100%;height:100%;margin:0;" contentEditable="true"></body></html>
