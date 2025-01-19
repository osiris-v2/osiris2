$ajax = new Array()


function ajax(datas,ih,loc,method="GET",js,mode="=",masajax=$ajax.length){



$ajax[masajax] =  new XMLHttpRequest()


if(method.toUpperCase()=="GET"){
loc = loc+"?"+datas;    
}

$ajax[masajax].open(method,loc)


$ajax[masajax].onreadystatechange = function(){





if($ajax[masajax].readyState===4){

if(ih){

eval(`document.getElementById('`+ih+`').innerHTML` + eval(`mode`) + `$ajax[masajax].responseText`)


} if(js) eval(js); $ajax[masajax] = "END 4:"+masajax  } else {

	if($ajax[masajax].readyState==3){
	if(!ih) eval($ajax[masajax].responseText)
		}
        //readyState < 4
	}
//end function
}



if(method.toUpperCase()=="POST"){
	
	$ajax[masajax].setRequestHeader('Content-Type','application/x-www-form-urlencoded');
	$ajax[masajax].send(datas)
	
} else if(method.toUpperCase()==="GET"){
	$ajax[masajax].send()
}

}











