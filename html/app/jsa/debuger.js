/*Hace uso de wfcore.js*/

write(`\
<div style='position:relative'>\
<img style='position:absolute' src='loading.gif' height=15 width=420>\
<div style='position:fixed;background:rgba(255,255,255,0.4);' id='bgimg'><b style='background:rgba:(17,10,12,0.3'>Loading...<b></div>\
</div>\
`)


/*
f=0

loadingText = ['.','..','...','....','.....','......','.......','........','..........','............','Estamos cargando','el contenido','de la página', 'por favor', 'espere a que termine','si se prolonga la espera','llame a su abogado']

hand = temp(`if(f==loadingText.length) f=0;bgimg.innerHTML = "<b style='padding:0px 10px 0px 15px'>"+loadingText[f]+"</b>";f++`,`interval`,1500)

$hand = temp(`temp.clear(hand);bgimg.innerHTML = "<b>Fin Temporizador</b>"`,`timeout`,55000)
*/

const objectLength = function(object){

return Object.entries(object).length

}

const loading = function(object){

this.loading = object

defId = document.body
defTimeIn = 350
defTimeOut = 14279
defEndText = "EndTemporizador"
defRollText = "Text , por defecto"

defRollOn = {'rollText':"Cargando....,,.....espere,finalizará en "+defTimeOut / 1000+" segundos",endText:""+defEndText+"",timeIn:""+defTimeIn+"",timeOut:""+defTimeOut+""}

if(objectLength(this.loading)<1 || this.loading.length > 0){

this.loading = defRollOn

}

if(objKeyExists(this.loading,'rollText')) {

if(this.loading.rollText.length > 0){

} else {

	this.loading.rollText = defRollText


	}

 } 

 if(objKeyExists(this.loading,'timeIn')){
/*
TIME IN
*/
} this.loading.timeIn = defTimeIn

if(objKeyExists(this.loading,'timeOut')){
/*timeout ok*/

} else this.loading.timeOut = defTimeOut 

if(objKeyExists(this.loading,'endText')){

//endtext ok

} else this.loading.endText = defEndText

if(objKeyExists(this.loading,'id')){
if(!this.loading.id) this.loading.id = defId
else this.loading.id = getId(this.loading.id)
} else this.loading.id = defId



const setx = function(time){

this.loading.timeIn = time
}

loadingText = this.loading.rollText.split(',')

f=0
hand = temp(`\
if(f==loadingText.length) f=0;\
this.loading.id.innerHTML = loadingText[f];\
f++\
`,`interval`,this.loading.timeIn)

$hand = temp(`temp.clear(hand);this.loading.id.innerHTML = this.loading.endText`,`timeout`,this.loading.timeOut)

}



carga = {id:'bgimg','rollText':"Cargando....,  ,  espere por favor , , espere por favor, ,G,Gr,Gra,Grac,Graci,Gracia,Gracias,Gracias :),Gracias ;),Gracias ;),Gracias :), espere por favor, , espere por favor ",endText:"End ROLL",timeIn:"290",timeOut:"30000"}

loading(carga)



setTimeout(`f=0;loadingText = new Array('Cambiando',' texto sobre',' la marcha','',' nupcial','');`,5000)

























