

internalsgen = 0; // auto incrementable en controls
internals = 0 ; // similar a internalsgen, variables autoincrementables de ambito global sin importancia numérica



var injectx // (animall.js) contiene el código de la última animación de una pestaña
var editing // contiene el id último en edición

/*
ad contiene los tags arrastrados a pestanas ad[n].id = n ...
ad[n] == 'erased' , significa que el tag ha sido eliminado
el primero se marca como eliminado ad[0].id = 0 no existe porque ad[0] siempre = 'erased'
esto se hace para evitar un valor de retorno 0 que se podría dar como false sin serlo
el id de cada tag arrastado a las pestañas es un número, debido a que css no interpreta números
 , no sirve #1 , en la animación css los tags pasan a ser div_1 video_3 siendo el texto el nombre
del tag ad[n].tag y _ que se une al id numérico.
*/

ad = new Array('erased') 


var mas1 = 0 //inicializa un variable ++ para funcion addControl










msg = new Object( { 'win': {


0: "Active una pestaña para arrastrar elementos"

}
}
)



