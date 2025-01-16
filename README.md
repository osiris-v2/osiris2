
<h3>OSIRIS V2</h3>

**Osiris:** Una Plataforma Modular para IA y Más Allá

**Descripción General:**

Osiris2 es una plataforma versátil y modular diseñada para la integración de inteligencia artificial (IA) y otras funcionalidades avanzadas. A diferencia de soluciones monolíticas, Osiris2 se construye sobre una arquitectura flexible que permite a los usuarios adaptar y expandir sus capacidades según sus necesidades específicas. Esta versión, `osiris2`, introduce una serie de mejoras y nuevos módulos, consolidando su posición como una herramienta potente y adaptable.

**Características Principales:**

*   **Independencia del Modelo de IA:** Osiris2 no está atado a un modelo de IA específico. Si bien puede integrar fácilmente modelos de proveedores como Google (Gemini) a través de la API, su arquitectura permite la integración de modelos de Hugging Face, modelos propios y otros servicios de IA, garantizando la flexibilidad y evitando el 'vendor lock-in'.
*   **Arquitectura Modular:** La base de Osiris2 es su diseño modular. Los componentes se pueden activar, desactivar o intercambiar fácilmente, lo que permite a los usuarios construir soluciones personalizadas y eficientes. Esta modularidad facilita el mantenimiento, la expansión y la adaptación a diferentes casos de uso.
*   **Interfaz de Consola Mejorada:** Osiris2 ofrece herramientas y ventanas de ayuda para interactuar con la consola de forma más intuitiva y eficaz. Esto facilita el manejo de la plataforma, la depuración y la configuración de los módulos.
*   **Streaming Multimedia Avanzado:** La plataforma incluye módulos para el manejo de streaming multimedia a través de `ffmpeg`, `HLS`, web y formatos HTML. Esto abre un abanico de posibilidades para la creación de aplicaciones que procesen, transmitan y presenten contenido multimedia en tiempo real.
*   **Cliente/Servidor en Rust:**  Los módulos cliente y servidor de Osiris2 están desarrollados en Rust, lo que proporciona rendimiento y seguridad de nivel superior. Esta elección tecnológica permite el desarrollo de aplicaciones de alto rendimiento con capacidades robustas de concurrencia y seguridad.
*   **Potencial para Blockchain:** Se está explorando la integración con tecnologías blockchain, lo que podría habilitar futuras funcionalidades para la gestión segura de datos, identidades digitales y transacciones dentro de la plataforma.
*   **Facilidad de Expansión:** La arquitectura modular de Osiris2 está diseñada para la fácil incorporación de nuevos módulos y funcionalidades, lo que garantiza la longevidad y adaptabilidad de la plataforma a las nuevas necesidades del mercado.

**Capacidades:**

*   **Procesamiento de Lenguaje Natural (PLN):** Análisis de texto, generación de contenido, traducción, chatbots, etc. (dependiendo del modelo de IA integrado).
*   **Visión por Computadora:** Reconocimiento de objetos, análisis de imágenes, generación de imágenes (dependiendo del modelo de IA integrado).
*   **Streaming Multimedia:** Transmisión de vídeo y audio en tiempo real, conversión de formatos, procesamiento multimedia, etc.
*   **Desarrollo Web:** Integración con interfaces web, generación de contenido dinámico, etc.
*   **Desarrollo de Aplicaciones:** Construcción de aplicaciones personalizadas con diferentes módulos y funcionalidades.
*   **Automatización:** Automatización de tareas repetitivas, gestión de flujos de trabajo, etc.

**Expectativas:**

*   **Flexibilidad:** Ofrecer una plataforma adaptable a una amplia gama de casos de uso, evitando el 'vendor lock-in' y permitiendo a los usuarios elegir las mejores herramientas para sus necesidades.
*   **Rendimiento:** Proporcionar un rendimiento excepcional gracias al uso de Rust y una arquitectura modular optimizada.
*   **Escalabilidad:** Permitir el crecimiento y la expansión de las funcionalidades según las necesidades del usuario.
*   **Comunidad:** Fomentar la participación de la comunidad en el desarrollo de módulos y la mejora continua de la plataforma.

**Próximos Pasos:**

*   Continuar desarrollando nuevos módulos y funcionalidades.
*   Explorar la integración de otras tecnologías emergentes.
*   Fortalecer la comunidad de usuarios y desarrolladores.

**En Resumen:**

Osiris2 es más que una simple herramienta de IA. Es una plataforma versátil y modular que permite a los usuarios construir soluciones personalizadas y adaptadas a sus necesidades específicas. Su flexibilidad, rendimiento y capacidad de expansión la convierten en una opción ideal para aquellos que buscan una solución robusta y adaptable a largo plazo.

**INSTALACION:** 

* Instalar Osiris es fácil usando el **Instalador General**. En la carpeta [DEBIAN](DEBIAN/) de este repositorio tienes un archivo .deb, al momento de escribir este manual es **[osiris2.deb](/DEBIAN/osiris2.deb)** si bien podrá haber otros más adelante. Sólo tienes que descargarlo para empezar la instalación. 

* **Instálalo** Desde el directorio que lo descargaste ejecutando:

Suponiendo que el archivo sea osiris2.deb haga:

*    **sudo dpkg -i osiris2.deb**

 El instalador actúa instalando los archivos en el directorio /var  
 El instalador provee de un nombre base para instalar el programa /var/VERSION por defecto.  
 El instalador pide al inicio un nombre base por si se quiere crear una nueva base o actualizar una existente.  
 Si existe la base proporcionada el instalador puede actuar de distintas formas (Actualizar, Reinstalar,...) en función a sus estados de instalación anteriores.  
 Si no existe esa base simplemente la instala nueva e independiente de otras.   
 Por lo tanto se pueden tener distintas versiones, algo así como /var/osiris2 /var/osiris21 /var/osirisXXX  

Al finalizar la descarga de archivos podrás completar la instalación instalando los programas y dependencias necesarias para que osiris funcione correctamente desde el **instalador interno**.  

No es un requisito hacerlo desde el **instalador general** ya que una vez descargados los archivos necesarios se puede hacer en cualquier momento.  

Para hacerlo manualmente sitúese sobre el directorio **/var/VERSION**  
y ejecute para acceder al **Instalador Interno** **./osiris**  o directamente  **./install.sh**  


**Se añadió una nueva política de instalación.** Los pasos anteriores están enfocados a una instación enfocada al desarrollo (menos estricta).  

* Para instalar una versión más estable y estrica use el instalador [RELEASE](/osiris2release.deb)  

La instalación release sólo usará los archivos listados en [Gitup-Release](/bin/gitup-release.txt)  
Ese archivo contiene los archivos que ya han sido probados y testados suficientemente para pasarlos a producción.  

La instalación en modo desarrollo puede contener archivos que se encuentren en distintas fases de implementación y podría no ser óptimo para un sistema en producción. Además su instalador en distintos momentos podría no estar enfocado a la seguridad absoluta.  

En el futuro habrá distintas orientaciones y opciones de instalación y actualización basándose en archivos de listados. Podrá usar instaladores dedicados o seleccionarlas en el previsto instalador general.  

**Herramientas**

* **GIT**

El instalador .deb de **osiris** usa GIT para descargar, instalar y actualizar el programa. 
Además Osiris contiene herramientas para facilitar la gestión si quieres a partir de osiris crear distintas versiones personalizadas y publicarlas en tus sitios de Github.  

Osiris incorpora todas las herramientas necesarias para su implementación.  
Osiris está diseñado con un enfoque  **autobuilding**  

* **DOCKER**

Docker permite ejecutar distintas aplicaciones en contenedores aislados, esto es útil cuando se quieren aislar del resto del sistema y asignarle recursos limitados. Esta funcionalidad es útil para mejorar la estabilidad y rendimiento del sistema en determinadas ocasiones. Esta característica será uno de los ejes principales del desarrollo de **osiris2**  

* **FFMPEG**

Osiris proporciona herramientas para descargar diferentes versiones de ffmpeg y compilarlas automáticamente para cada versión instalada de osiris independientes unas de otras ya que las compila en el directorio /var/VERSION/bin/com/osiris_env/ffmpeg.  
Sin embargo se puede generar un alias para usarlas globalmente de forma independiente, por ejemplo o2ffmpeg, ffmpeg-osiris, etc...  

* **APACHE2**

Osiris hace una una instalación global del servidor **Apache** para todo el sistema.  
Las distintas versiones instaladas pueden hacer uso de el y tener configurados sus propios host virtuales compartidos.  
Normalmente se usa una versión como host principal por defecto sin embargo esto es flexibe y se puede alternar fácilmente

* **PHP-FPM**  

FastCGI Process Manager. Esta versión de PHP logra por un lado reforzar la seguridad y por otro mejorar el rendimiento de aplicaciones Php. Se trata de separar cada aplicación la una de la otra asignándole un Pool de PhP diferente.

* **NGINX**  

Nginx es la herramienta ideal para trabajar con flujos de streaming HLS debido a su forma de manejar las conexiones, además de otras importantes características, es por ello que compartirá funciones HTTP con el servidor Apache dentro de Osiris, por ejemplo,
 usando un puerto distinto al 80 para manejar transmisiones HLS corriendo tanto Nginx como Ffmpeg en contenedores Docker.

* **CERTBOT**  

Permite crear certificados SSL para tus dominios web (host y hosts virtuales) (HTTPS) **Let's Encrypt**  
Osiris proporciona herramientas específicas para facilitar y automatizar esa tarea.   

* **MARIADB**  

Maria-DB es el gestor de bases de datos Libre derivado de MYSQL. Es un servidor de bases de datos  potente, flexible y de alto rendimiento.  

* **TMUX**  

Osiris dispone de herramientas para descargar y actualizar **tmux**  
Tmux es un multiplexor de terminal que permite utilizar varias aplicaciones de forma simultánea.  
Además de las composiciones predeterminadas, Osiris permite hacer diferentes composiciones diseñadas por el usuario según sus necesidades, usando las herramientes que osiris proporciona para ello.  

* **TERMINATOR**  

Terminator es un emulador de terminal vitaminizado que te permite potenciar la clásica terminal con muchísimas opciones. Terminator nos permitirá sacarle más jugo a nuestra terminal linux y facilitarnos algunas tareas.  

Terminator integrado con tmux ofrece una amplia gama de posibilidades  

* **PYTHON**

Python es ideal para aplicaciones cuyo rendimiento no es crítico y aplicaciones gráficas asistentes, y provee de una gran cantidad de librerías que facilitan sus implementaciones.  

Los comando de la consola osiris son implementaciones en este lenguaje principalmente.  

Revise la guía sobre como crear comandos y sus requisitos [En Esta Guía](/DOCS/com.create.md)   

Osiris dispone de un entorno virtual independiente al resto del sistema.  

Si tiene más de un proyecto osiris en el sistema, cada uno de ellos provee de su entorno virtual independiente de manera automática.  

* **RUST**  

Osiris proporciona una herramienta que descarga e instala la útima versión del lenguaje **rust** en el sistema, el compilador **rustc** y el asistente de proyectos **cargo**, además de las propias herramientas que osiris dispone para compilar/re-compilar/ejecutar las fuentes rust que osiris usa, fundamentalmente para herramientas como servidores y clientes.   

* **NODEJS** 

Puede usar NodeJs para algunos de sus proyectos si lo desea, osiris provee de heramientas para su instalación y uso.  



<h3><u> Este README está en proceso de construcción y no está aún completo </u></h3>  




### Modo tmux

 Inicie osiris en múltiples consolas [DOC OSIRIS2TMUX](/DOCS/osiris2tmux.md)

![Osiris2Tmux1](/bin/com/tmp/zj91enedg3.png)


* **Este sistema ha sido probado con éxito en gnu/linux debian 12**  


<h4> Todas las aplicaciones, especificaciones y funcionalidades descritas forman parte de osiris o la formarán en un futuro.  </h4>  




**Modelo dashboard**  
!["Imagen Osiris Final"](https://www.compostela21.com/videojs/elementos/_0_NIM/9yjEUNRxHE.png)

**--**  **osiris.osscom@gmail.com**  






