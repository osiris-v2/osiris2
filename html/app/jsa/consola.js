
this.LOCATION = "consolaif"


defsrc="debuger.js"


document.write("<div id='consola'  onclick='display(\""+LOCATION+"\")'><a target='"+LOCATION+"' onclick='xload(`"+defsrc+"`)' href='javascript:void(0);'><b>debuger</b></a></div>")

document.write("<div id='"+LOCATION+"' style='display:none;visibility:visible'><iframe name='"+LOCATION+"' style='width:100%;height:150px;border:0;'></iframe></div>")

document.write(LOCATION)




const xload = function(param=defsrc){

this.src = param

LOCATION = open(this.src,LOCATION)

LOCATION.document.write('<html><head><script src=wfcore.js></script><script src="'+this.src+'"></script>')

LOCATION.close()
}


//document.write("<script>LOCATION.src = 'inframe.js';alert('hola')</script>")







objects ={ navigator:'THIS',location:"href=location,target=blank,style='width:100%'",window:"browser wininfo",ERROR:'0'     }

object = {create:'6J2022'}


//document.write('WRITE')


const recursive = function (object=object){






nn = 0

for (const [key, value] of Object.entries(object)) {


//const nap = function (object){


nn++
VALOR = "VALUE"+nn

//eval(''+key+'.'+value+' = "'+VALOR+'"')

document.write(''+key+'.'+value+' = `'+VALOR+'`'  )
document.write('<br>')

//}

//eval(  ''+object+'.'+value+'' )


//if(object.is(key,key)) 

//document.write(evalInstance(object,key,value))

}


//nap(object)

for (const [key, value] of Object.entries(object)) {

//recursive(object);
document.write(key+":"+value+"<hr>")
}



}


recursive(objects)


document.write('end')

