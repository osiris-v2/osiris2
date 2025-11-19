
const sitiosDeseados = {
  youtube: "https://www.youtube.com/watch?v=",
  vimeo: "https://www.vimeo.com",
  vimeo1: "https://vimeo.com",
  vimeo2: "https://player.vimeo.com",
  dailymotion: "https://www.dailymotion.com/video/",
  dailymotion: "https://www.dailymotion.com/embed/",
  osiris: "https://osiris000.duckdns.org/img/tmp/"
};

function mktparse(id, txt) {
  id.innerHTML = "";
  let html = marked.parse(txt);
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');
  const enlaces = doc.querySelectorAll('a[href]');
  let enlacesEncontrados = 0;

    enlaces.forEach(enlace => {
      enlace.setAttribute('target', '_blank'); // Añadido target="_blank" a todos los enlaces

      const href = enlace.getAttribute('href');
      let esEnlaceDeseado = false;
        for (const sitio in sitiosDeseados) {
            if (href && href.startsWith(sitiosDeseados[sitio])) {
                esEnlaceDeseado = true;
                 enlacesEncontrados++;
                break;
            }
        }

        if (esEnlaceDeseado) {
             procesarEnlaceVideo(enlace,true);
        }
    });

  if (enlacesEncontrados > 0) {
    id.innerHTML += ``;
  }
  id.appendChild(doc.body);
}


function procesarEnlaceVideo(enlace, modoVideoActivado) {
  if (modoVideoActivado) {
    const enlaceId = `enlace-video-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    const videoContainerId = `video-container-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    const iframeId = `iframe-video-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
    enlace.id = enlaceId;

    const botonDesplegar = document.createElement('button');
    botonDesplegar.textContent = 'Desplegar Video';
    botonDesplegar.classList.add('boton-desplegar-video');

      const contenedorVideo = document.createElement('div');
    contenedorVideo.id = videoContainerId;
      contenedorVideo.classList.add('video-container');
      contenedorVideo.style.display = "none"

    const urlVideo = enlace.getAttribute('href');
    const urlVideoMapeada = mapearUrlAEmbed(urlVideo);

     const br = document.createElement('br'); // Crear elemento br
    enlace.parentNode.insertBefore(br, enlace); // Insertar br antes del botón
     enlace.parentNode.insertBefore(botonDesplegar, enlace);


        botonDesplegar.addEventListener('click', () => {
          if (contenedorVideo.innerHTML === "") {
               if (urlVideoMapeada) {
                contenedorVideo.innerHTML = `<iframe id="${iframeId}" src="${urlVideoMapeada}" width="80%" height="315" allowfullscreen></iframe>`
                botonDesplegar.textContent = 'Cerrar Video';
                contenedorVideo.style.display = "block"
            }else{
              contenedorVideo.innerHTML = '<p>No se pudo obtener el video asociado a este enlace.</p>';
              }
          } else {
              contenedorVideo.innerHTML = "";
              contenedorVideo.style.display = "none"
              botonDesplegar.textContent = 'Desplegar Video';
          }

    });


      enlace.parentNode.insertBefore(contenedorVideo, enlace.nextSibling);
  }
}


function mapearUrlAEmbed(url) {
  if (url.includes('youtube.com')) {
    const urlParams = new URLSearchParams(url.split('?')[1]);
    const videoId = urlParams.get('v');
    if (videoId) {
      return `https://www.youtube.com/embed/${videoId}`;
    }
  }

  if (url.includes('vimeo.com')) {
    const videoId = url.split('/').pop();
    return `https://player.vimeo.com/video/${videoId}`;
  }

  if (url.includes('dailymotion.com')) {
    const videoId = url.split('/').pop();
    return `https://dailymotion.com/embed/video/${videoId}`;
  }

  if (url.includes('osiris000.duckdns.org')) {
    const videoId = url.split('/').pop();
    return url
  }

  return null;
}
