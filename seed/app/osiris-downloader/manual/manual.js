(function(){
  var root=document.documentElement, KEY='osiris-manual-theme';
  try{var s=localStorage.getItem(KEY); if(s) root.setAttribute('data-theme',s);
      else if(matchMedia('(prefers-color-scheme: dark)').matches) root.setAttribute('data-theme','dark');}catch(e){}
  document.addEventListener('DOMContentLoaded',function(){
    // índice automático de la página actual (h2) bajo su enlace del menú
    var cur=document.querySelector('nav.side a.cur'), hs=document.querySelectorAll('main h2');
    if(cur&&hs.length){var box=document.createElement('div');box.className='toc';
      hs.forEach(function(h,i){if(!h.id)h.id='s'+i;var a=document.createElement('a');a.href='#'+h.id;a.textContent=h.textContent;box.appendChild(a);});
      cur.after(box);}
    // botón copiar en bloques de código
    document.querySelectorAll('main pre').forEach(function(pre){
      var b=document.createElement('button');b.textContent='Copiar';
      b.onclick=function(){var t=pre.querySelector('code').innerText;
        (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){b.textContent='¡Copiado!';},function(){
          var r=document.createRange();r.selectNodeContents(pre.querySelector('code'));var sel=getSelection();sel.removeAllRanges();sel.addRange(r);b.textContent='Seleccionado';});
        setTimeout(function(){b.textContent='Copiar';},1500);};
      pre.appendChild(b);});
    // tema claro/oscuro
    var tb=document.getElementById('theme');
    if(tb)tb.onclick=function(){var n=root.getAttribute('data-theme')==='dark'?'light':'dark';root.setAttribute('data-theme',n);try{localStorage.setItem(KEY,n);}catch(e){}};
  });
})();
