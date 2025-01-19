

write(`\
<div style='position:relative'>\
<img style='position:absolute' src='loading.gif' height=18 width=510>\
<div style='position:fixed;background:rgba(255,255,255,0.4)' id='bgimg'></div>\
</div>\
`)

f=0

chr = ['Estamos cargando','el contenido','de la página', 'por favor', 'espere a que termine','si se prolonga la espera','llame a su abogado']

hand = temp(`if(f==chr.length) f=0;bgimg.innerHTML = "<b>"+chr[f]+"</b>";f++`,`interval`,1500)

$hand = temp(`temp.clear(hand);bgimg.innerHTML = "<b>Fin Temporizador</b>"`,`timeout`,55000)

