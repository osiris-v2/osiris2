
function addTask(menubar="Menubar parametro1",text="Escribe tu Texto",src="https://127.0.0.1/www/php/paneljs.php",tag="iframe",id="auto",cclass="defclass",insert="body",style="width:auto;height:auto"){

create = document.createElement(tag)
create.id = id
create.className = cclass
create.style = style
parsesrc(create,src,tag)
layerdisplay = create
  
create = document.createElement()
  
  
  
  
return create
  
}


function parsesrc(thisid,src,tag){
  

  
  
if(src.match(/^http+s?:\/\/.+$/si) && tag == "iframe")
{
return thisid.src = src
}  
  else
    {
      
      return thisid.innerHTML = src
      
    }
}


addTask()

