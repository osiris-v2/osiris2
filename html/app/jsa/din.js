function dmenu(divid,classname){
    var dcls=document.getElementsByClassName(classname);
    for(i=0;i<dcls.length;i++){
    if(dcls[i].id!==divid){
    dcls[i].style.visibility="hidden";
    dcls[i].style.display="none";
    }else{
    dcls[i].style.visibility="visible";
    dcls[i].style.display="block";
     }
   }
 }
 


function display(id){
if(!id) return "Undefined";
id = document.getElementById(id)
dsplay = id.style.display
if(dsplay=='block') id.style.display = "none"
else id.style.display = "block"
return dsplay
}


function getId(id){
return document.getElementById(id)
}

function clearHTML(id){
if(!id) return "Undefined";
id = document.getElementById(id)
id.innerHTML = "";
}


 function clickId(emulado){
var y = document.querySelector(emulado);
y.click();
return;
}


function display2(divid,classname){

rt = getId(divid).style.display
    var dcls=document.getElementsByClassName(classname);
    for(i=0;i<dcls.length;i++){
    if(dcls[i].id!==divid){
    disp = "none"
    dcls[i].style.display=disp
    cl = getId(dcls[i].id)
    cl.innerHTML = ""
    }else{
    disp = "block"
    dcls[i].style.display=disp
     }
   }

return rt
 }

