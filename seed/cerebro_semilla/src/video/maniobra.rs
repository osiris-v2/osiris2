// PROYECTO OSIRIS - MANIFIESTO DE INGENIERIA (DUREZA 256)
// SINTAXIS FGN - ASCII PURO - SIN ACENTOS

pub struct GestorManiobra {
    pub bitrate: u32,
    pub filtros_activos: Vec<usize>,
    pub historial: Vec<usize>,
    pub catalogo: Vec<(&'static str, &'static str)>,
}

impl GestorManiobra {
    pub fn new() -> Self {
        Self {
            bitrate: 3000,
            filtros_activos: Vec::new(),
            historial: Vec::new(),
/* cerebro/src/video/maniobra.rs */

// ... (dentro de impl GestorManiobra::new)
catalogo: vec![

    ("BASE", "format=yuv420p"),
    ("BORDES", "edgedetect=low=0.1:high=0.4,format=yuv420p"),
    ("NOCHE", "hue=s=0,curves=all='0/0 0.5/0.8 1/1',format=yuv420p"),
    ("XRAY", "negate,curves=color_negative,format=yuv420p"),
    ("MOSAICO", "split=4[a][b][c][d];[b]edgedetect[b];[c]negate[c];[d]hue=s=0[d];[a][b][c][d]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0,scale=iw:ih,format=yuv420p"),

    // --- VISION TACTICA (Optimización GBRP) ---
    ("THERMAL", "format=gbrp,lutrgb=r=maxval:g=0:b=0,colorlevels=rimin=0.05:gimin=0.05:bimin=0.05,colormatrix=bt709:fcc,format=yuv420p"),
    ("CYBER", "hue=h=90:s=2,chromashift=cbh=20:crv=20,unsharp=5:5:1.0:5:5:0.0,format=yuv420p"),
    ("VAPOR", "curves=vintage,drawbox=y=ih/2:w=iw:h=1:t=1:c=black@0.5,tinterlace=mode=interleave_top,format=yuv420p"),
    ("GLITCH", "noise=alls=100:allf=t+u,hue=h=20:s=3,format=yuv420p"), // Eliminado frei0r si no es necesario
    ("SOBEL", "format=gray,sobel,negate,format=yuv420p"),
    ("MATRIX", "format=gray,lutrgb=g=val*2:r=0:b=0,curves=all='0/0 0.5/0.2 1/1',format=yuv420p"),

    // --- EFECTOS DE MOVIMIENTO Y ESTELA ---
    ("GHOST", "split[a][b];[a]format=yuva420p,lutalpha=val=128[a_trans];[b]lagfun=decay=0.9[b_slow];[b_slow][a_trans]overlay,format=yuv420p"),
    ("INFRA", "format=gbrp,extractplanes=r+g+b[r][g][b];[r]negate[rn];[rn][g][b]merge=gbrp,hue=s=0.5:h=180,format=yuv420p"),
    ("SCANLINE", "split[a][b];[b]noise=alls=20:allf=t+u,hue=s=0[noise];[a][noise]blend=all_mode='overlay':all_opacity=0.3,drawgrid=w=iw:h=2:t=1:c=black@0.5,format=yuv420p"),
    ("CRT", "lenscorrection=k1=0.1:k2=0.1,chromashift=cbh=10:crv=10,vignette=angle=0.5,format=yuv420p"),
    ("NEON", "split[orig][edges];[edges]edgedetect=low=0.1:high=0.2,negate,hue=h=200:s=2[neon];[orig][neon]blend=all_mode='lighten',format=yuv420p"),
    ("CORRUPT", "split[a][b];[b]crop=iw:ih/4:0:ih/2,scale=iw:ih/4:flags=neighbor,hue=h=120[block];[a][block]overlay=0:ih/3:shortest=1,format=yuv420p"),
    ("RADAR", "format=gray,lutrgb=g=val*1.5:r=0:b=0,drawbox=y=ih/2:w=iw:h=2:t=1:c=green@0.8,format=yuv420p"),

    // --- FASE 2: DINAMICA AVANZADA ---
    ("PREDATOR", "split[a][b];[a]format=gbrp,lutrgb=r=val*2:g=val/2:b=0[thermal];[b]edgedetect=low=0.1:high=0.2,negate[edges];[thermal][edges]blend=all_mode='screen',format=yuv420p"),
    ("CHRONOS", "split=4[a][b][c][d];[b]tblend=all_mode=average,tpade=start_frame=1[b1];[c]tblend=all_mode=average,tpade=start_frame=2[c1];[d]tblend=all_mode=average,tpade=start_frame=3[d1];[a][b1][c1][d1]vstack=inputs=4,scale=iw:ih,format=yuv420p"),
    ("AMBER", "format=gray,lutrgb=r=val:g=val*0.6:b=0,noise=alls=15:allf=t,curves=all='0/0 0.5/0.4 1/1',format=yuv420p"),
    ("KALEIDO", "split=4[a][b][c][d];[b]hflip[b1];[c]vflip[c1];[d]hflip,vflip[d1];[a][b1][c1][d1]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0,scale=iw:ih,format=yuv420p"),
    ("ACID", "chromashift=cbh=20:cbv=20:crh=-20:crv=-20,hue=h=150:s=1.5,curves=all='0/0 0.3/0.6 1/1',format=yuv420p"),
    ("SOLAR", "curves=all='0/0 0.25/0.5 0.5/1 0.75/0.5 1/0',hue=s=0.2,format=yuv420p"),
    ("CRUSHER", "format=rgb24,colorlevels=rimin=0.1:gimin=0.1:bimin=0.1,format=pal8,scale=iw:ih:flags=neighbor,format=yuv420p"),
    ("NEBULA", "split[a][b];[b]boxblur=20:1,hue=h=300:s=4[blur];[a][blur]blend=all_mode='lighten':all_opacity=0.7,format=yuv420p"),
    ("SINCITY", "format=gbrp,split[a][b];[a]format=gray[gray];[b]colorkey=color=red:similarity=0.3:blend=0.2[mask];[gray][mask]overlay,format=yuv420p"),
    ("NEURO", "drawgrid=w=20:h=20:t=1:c=cyan@0.3,curves=all='0/0 0.5/0.7 1/1',format=gbrp,negate,hue=h=180:s=0.5,negate,format=yuv420p"),

    // --- VANGUARDIA DIGITAL (Optimización de GEQ a LUT/COLOR) ---
    ("STARDUST", "split[a][b];[b]format=gbrp,noise=alls=100:allf=t,gblur=sigma=20[noise];[a][noise]blend=all_mode='dodge',hue=h=45:s=2,format=yuv420p"),
    ("CUBISMO", "colorlevels=rimin=0.1:gimin=0.1:bimin=0.1,format=pal8,spp=6:4,scale=iw:ih:flags=neighbor,format=yuv420p"),
    ("REDACT", "format=gray,threshold=level=0.5,negate,noise=alls=50:allf=p,format=yuv420p"),
    ("PINTURA", "anlmdn=s=7:p=3:r=15,unsharp=5:5:1.5:5:5:0.0,format=yuv420p"),
    ("SUPER8", "curves=vintage,noise=alls=20:allf=t,vignette,format=yuv420p"),
    ("FRACTAL", "split[a][b];[b]lutrgb=r=negval:g=negval:b=negval,rotate=PI*t/10:c=black@0:ow=iw:oh=ih[rotated];[a][rotated]blend=all_mode='difference',format=yuv420p"),
    ("MONET", "atadenoise=0.1:0.1:0.1,smartblur=lr=5:ls=-1:lt=1,hue=s=1.5,format=yuv420p"),
    ("NOIR", "format=gray,curves=all='0/0 0.4/0.1 0.6/0.9 1/1',vignette=angle=0.3,noise=alls=30:allf=t,format=yuv420p"),
    ("PLASMA", "format=gbrp,colorchannelmixer=rr=1.5:gg=1.2:bb=2.0,hue=h='t*10',format=yuv420p"), // GEQ reemplazado por mixer dinamico (mas rapido)
    ("SHELL", "split[a][b];[a]hue=s=0[gray];[b]edgedetect=low=0.1:high=0.2,negate,split[c][d];[c]hue=h=180:s=2[cyan];[d]hue=h=300:s=2[mag];[cyan][mag]blend=all_mode='screen'[edges];[gray][edges]overlay,format=yuv420p"),

    // --- OPTICA & DINAMICA ---
    ("MIRROR", "split[a][b];[b]scale=iw/1.5:ih/1.5,pad=iw:ih:(ow-iw)/2:(oh-ih)/2:black@0[inner];[a][inner]overlay=format=yuv420,format=yuv420p"),
    ("ZOOMBLUR", "split[a][b];[b]vignette=angle=0.5,boxblur=10:1[v];[a][v]blend=all_mode='lighten',format=yuv420p"),
    ("VERTIGO", "split[a][b];[b]rotate=1*PI/180:c=black@0,format=yuva420p,lutalpha=val=150[r];[a][r]overlay,lagfun=decay=0.95,format=yuv420p"),
    ("PIXELSMOOTH", "spp=6:5,scale=128:72:flags=neighbor,scale=iw:ih:flags=neighbor,format=yuv420p"),
    ("PRISMA", "format=gbrp,split=3[r][g][b];[r]lutrgb=g=0:b=0,rotate=2*PI/180:c=black@0[r1];[g]lutrgb=r=0:b=0[g1];[b]lutrgb=r=0:g=0,rotate=-2*PI/180:c=black@0[b1];[r1][g1][b1]merge=3,format=yuv420p"),
    ("GSHIFT", "format=gbrp,displace=edge=mirror[a][b];[a]split[a1][a2];[a2]negate[mask];[a1][mask]overlay,format=yuv420p"),
    ("GASOLINA", "format=gbrp,geq=r='r(X,Y)*sin(T)':g='g(X,Y)*cos(T)':b='b(X,Y)*tan(T/10)',format=yuv420p"),

//    ("GASOLINA", "format=gbrp,colorchannelmixer=rr='sin(t)':gg='cos(t)':bb='tan(t/10)',format=yuv420p"), // GEQ optimizado
    ("DOPPEL", "split[a][b];[b]negate,format=yuva420p,lutalpha=val=60,setpts=2.0*PTS[slow];[a][slow]overlay=shortest=1,format=yuv420p"),
    ("INK", "edgedetect=low=0.1:high=0.3,negate,format=gray,curves=all='0/0 0.2/0 0.8/1 1/1',smartblur=lr=5:ls=-1,format=yuv420p"),
    ("KINETIC", "format=gray,tblend=all_mode=difference,threshold=level=0.1,negate,format=yuv420p"),


/*
    ("BASE", "format=yuv420p"),
    ("BORDES", "edgedetect=low=0.1:high=0.4"),
    ("NOCHE", "hue=s=0,curves=all='0/0 0.5/0.8 1/1'"),
    ("XRAY", "negate,curves=color_negative"),
    ("MOSAICO", "split=4[a][b][c][d];[b]edgedetect[b];[c]negate[c];[d]hue=s=0[d];[a][b][c][d]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0"),
    
    // --- NUEVA BATERIA DE FILTROS OSIRIS ---
    
    // 5. THERMAL: Simula vision termica con gradiente de color (Amarillo/Rojo/Azul)
    ("THERMAL", "format=gbrp,lutrgb=r=maxval:g=0:b=0,colorlevels=rimin=0.05:gimin=0.05:bimin=0.05,colormatrix=bt709:fcc"),
    
    // 6. CYBERPUNK: Saturacion de magentas y cianos con aberracion cromatica leve
    ("CYBER", "hue=h=90:s=2,chromashift=cbh=20:crv=20,unsharp=5:5:1.0:5:5:0.0"),
    
    // 7. VAPORWAVE: Efecto de scanlines de TV vieja y color pastel
    ("VAPOR", "curves=vintage,drawbox=y=ih/2:w=iw:h=1:t=1:c=black@0.5,tinterlace=mode=interleave_top"),
    
    // 8. GLITCH: Desincronizacion de bits forzada (Simula fallo de IA)
    ("GLITCH", "noise=alls=100:allf=t+u,hue=h=20:s=3,frei0r=filter_name=glitch0r"),
    
    // 9. SOBEL: Deteccion de profundidad estilo dibujo tecnico pesado
    ("SOBEL", "format=gray,sobel,negate"),
    
    // 10. MATRIX: El clasico verde digital con realce de contraste
    ("MATRIX", "format=gray,lutrgb=g=val*2:r=0:b=0,curves=all='0/0 0.5/0.2 1/1'"),

// 11. GHOST_ECHO (Efecto Estela): Mezcla el frame actual con el anterior al 50%
    // Ideal para detectar movimiento residual.
    ("GHOST", "split[a][b];[a]format=yuva420p,lutalpha=val=128[a_trans];[b]lagfun=decay=0.9[b_slow];[b_slow][a_trans]overlay"),

    // 12. INFRARED (Falso Infrarrojo): Invierte canales y resalta el rojo sobre el azul
    ("INFRA", "format=gbrp,extractplanes=r+g+b[r][g][b];[r]negate[rn];[rn][g][b]merge=gbrp,hue=s=0.5:h=180"),

    // 13. SCANLINE_PRO (Interferencia de Seguridad): Mezcla ruido con lineas horizontales
    ("SCANLINE", "split[a][b];[b]noise=alls=20:allf=t+u,hue=s=0[noise];[a][noise]blend=all_mode='overlay':all_opacity=0.3,drawgrid=w=iw:h=2:t=1:c=black@0.5"),

    // 14. CRT_WARP (Efecto Monitor Viejo): Curvatura de lente y aberracion cromatica
    ("CRT", "lenscorrection=k1=0.1:k2=0.1,chromashift=cbh=10:crv=10,vignette=angle=0.5"),

    // 15. NEON_DREAMS (Mixto): Bordes brillantes sobre fondo oscuro saturado
    // Usa split para detectar bordes y luego los ilumina en modo 'addition'
    ("NEON", "split[orig][edges];[edges]edgedetect=low=0.1:high=0.2,negate,hue=h=200:s=2[neon];[orig][neon]blend=all_mode='lighten'"),

    // 16. DATA_CORRUPTION (Simulacion de fallo critico): 
    // Desplaza bloques de color y aplica pixelado aleatorio
    ("CORRUPT", "split[a][b];[b]crop=iw:ih/4:0:ih/2,scale=iw:ih/4:flags=neighbor,hue=h=120[block];[a][block]overlay=0:ih/3:shortest=1,frei0r=filter_name=pixeliz0r"),

    // 17. RADAR (Tactico): Circulo de escaneo verde sobre mapa de grises
    ("RADAR", "format=gray,lutrgb=g=val*1.5:r=0:b=0,drawbox=y=ih/2:w=iw:h=2:t=1:c=green@0.8"),

    // --- EXPANSION CRITICA: PROTOCOLO OSIRIS FASE 2 ---

// 18. PREDATOR: Mapa de calor dinámico con realce de siluetas blancas
("PREDATOR", "split[a][b];[a]format=gbrp,lutrgb=r=val*2:g=val/2:b=0[thermal];[b]edgedetect=low=0.1:high=0.2,negate[edges];[thermal][edges]blend=all_mode='screen'"),

// 19. CHRONOS: Mezcla el frame actual con tres frames anteriores (estela de tiempo real)
("CHRONOS", "split=4[a][b][c][d];[b]tblend=all_mode=average,tpade=start_frame=1[b1];[c]tblend=all_mode=average,tpade=start_frame=2[c1];[d]tblend=all_mode=average,tpade=start_frame=3[d1];[a][b1][c1][d1]vstack=inputs=4,scale=iw:ih"),

// 20. AMBER_ALERT: Monocromo ámbar industrial con ruido de grano de película de 16mm
("AMBER", "format=gray,lutrgb=r=val:g=val*0.6:b=0,noise=alls=15:allf=t,curves=all='0/0 0.5/0.4 1/1'"),

// 21. KALEIDO: Espejo cuádruple con rotación de fase (Efecto caleidoscópico táctico)
("KALEIDO", "split=4[a][b][c][d];[b]hflip[b1];[c]vflip[c1];[d]hflip,vflip[d1];[a][b1][c1][d1]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0,scale=iw:ih"),

// 22. ACID_RAIN: Desplazamiento de canales R y B en cascada (efecto lluvia ácida)
("ACID", "chromashift=cbh=20:cbv=20:crh=-20:crv=-20,hue=h=150:s=1.5,curves=all='0/0 0.3/0.6 1/1'"),

// 23. SOLARIZE: Inversión de curvas de luminancia media (Efecto Sabatier digital)
("SOLAR", "curves=all='0/0 0.25/0.5 0.5/1 0.75/0.5 1/0',hue=s=0.2"),

// 24. BIT_CRUSHER: Reducción drástica de la paleta de colores y posterización agresiva
("CRUSHER", "format=rgb24,colorlevels=rimin=0.1:gimin=0.1:bimin=0.1,format=pal8,scale=iw:ih:flags=neighbor"),

// 25. NEBULA: Mezcla de desenfoque radial con saturación extrema de púrpuras
("NEBULA", "split[a][b];[b]boxblur=20:1,hue=h=300:s=4[blur];[a][blur]blend=all_mode='lighten':all_opacity=0.7"),

// 26. SIN_CITY: Todo en blanco y negro excepto los rojos intensos (aislamiento de canal)
("SINCITY", "format=gbrp,split[a][b];[a]format=gray[gray];[b]colorkey=color=red:similarity=0.3:blend=0.2[mask];[gray][mask]overlay"),

// 27. NEURO_LINK: Superposición de rejilla hexagonal con pulsación de brillo
("NEURO", "drawgrid=w=20:h=20:t=1:c=cyan@0.3,curves=all='0/0 0.5/0.7 1/1',format=gbrp,negate,hue=h=180:s=0.5,negate"),

// --- COLECCION MASTER: VANGUARDIA DIGITAL OSIRIS ---

// 28. LIQUID_STARDUST: Partículas de luz que se funden con un desenfoque de movimiento direccional
("STARDUST", "split[a][b];[b]format=gbrp,noise=alls=100:allf=t,gblur=sigma=20[noise];[a][noise]blend=all_mode='dodge',hue=h=45:s=2"),

// 29. CUBISMO_VIRTUAL: Divide la imagen en bloques de color sólido que bailan según la luminancia
("CUBISMO", "colorlevels=rimin=0.1:gimin=0.1:bimin=0.1,format=pal8,spp=6:4,scale=iw:ih:flags=neighbor"),

// 30. DEEP_REDACTION: Convierte la imagen en un negativo de alto contraste con ruido de bits "perdidos"
("REDACT", "format=gray,threshold=level=0.5,negate,noise=alls=50:allf=p"),

// 31. OIL_CANVAS: Simula una pintura al óleo mediante la reducción de ruido por anisotropía
("PINTURA", "anlmdn=s=7:p=3:r=15,unsharp=5:5:1.5:5:5:0.0"),

// 32. SUPER_8_NOSTALGIA: Grano de película de 8mm, quemaduras de celuloide y virado a sepia orgánico
("SUPER8", "curves=vintage,noise=alls=20:allf=t,drawbox=x=iw*random(1):w=2:h=ih:c=white@0.2:t=fill,vignette"),

// 33. PSYCHO_FRACTAL: Multiplica la imagen y la rota en fases de color opuestas (desorientación total)
("FRACTAL", "split[a][b];[b]lutrgb=r=negval:g=negval:b=negval,rotate=PI*t/10:c=black@0:ow=iw:oh=ih[rotated];[a][rotated]blend=all_mode='difference'"),

// 34. MONET_DATAMOSH: Aplica un desenfoque selectivo que solo afecta a las zonas de bajo contraste
("MONET", "atadenoise=0.1:0.1:0.1,smartblur=lr=5:ls=-1:lt=1,hue=s=1.5"),

// 35. NOIR_DETECTIVE: Blanco y negro extremo con un haz de luz central y grano pesado
("NOIR", "format=gray,curves=all='0/0 0.4/0.1 0.6/0.9 1/1',vignette=angle=0.3,noise=alls=30:allf=t"),

// 36. PLASMA_WAVE: Distorsión de onda senoidal sobre el mapa de colores (efecto psicodélico líquido)
("PLASMA", "format=gbrp,geq=r='128+127*sin(hypot(X-W/2,Y-H/2)/10-T)':g='128+127*sin(hypot(X-W/2,Y-H/2)/15+T)':b='128+127*sin(hypot(X-W/2,Y-H/2)/20)'"),

// 37. GHOST_IN_THE_SHELL: Bordes de cian y magenta que parpadean sobre un fondo desaturado
("SHELL", "split[a][b];[a]hue=s=0[gray];[b]edgedetect=low=0.1:high=0.2,negate,split[c][d];[c]hue=h=180:s=2[cyan];[d]hue=h=300:s=2[mag];[cyan][mag]blend=all_mode='screen'[edges];[gray][edges]overlay"),

// --- LIBRERIA OSIRIS: OPTICA & DINAMICA ESPACIAL ---

// 38. INFINITY_MIRROR: Crea un tunel de espejos infinito hacia el centro
("MIRROR", "split[a][b];[b]scale=iw/1.5:ih/1.5,pad=iw:ih:(ow-iw)/2:(oh-ih)/2:black@0[inner];[a][inner]overlay=format=rgb"),

// 39. RADIAL_BLUR: Desenfoque de zoom que simula velocidad hiperespacial
("ZOOMBLUR", "split[a][b];[b]vignette=angle=0.5,boxblur=10:1[v];[a][v]blend=all_mode='lighten',zoompan=z='min(zoom+0.001,1.1)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"),

// 40. VERTIGO: Combina el movimiento con una rotacion leve y eco temporal
("VERTIGO", "split[a][b];[b]rotate=1*PI/180:c=black@0,format=yuva420p,lutalpha=val=150[r];[a][r]overlay,lagfun=decay=0.95"),

// 41. MOSAIC_SMOOTH: Pixelado de alta definicion que se suaviza con el movimiento
("PIXELSMOOTH", "spp=6:5,scale=128:72:flags=neighbor,scale=iw:ih:flags=neighbor"),

// 42. PRISMA: Separa la luz en los tres colores primarios con un desfase angular
("PRISMA", "format=gbrp,split=3[r][g][b];[r]lutrgb=g=0:b=0,rotate=2*PI/180:c=black@0[r1];[g]lutrgb=r=0:b=0[g1];[b]lutrgb=r=0:g=0,rotate=-2*PI/180:c=black@0[b1];[r1][g1][b1]merge=3"),

// 43. GHOST_SHIFT: Los bordes de la imagen se desplazan lateralmente segun el brillo
("GSHIFT", "format=gbrp,displace=edge=mirror[a][b];[a]split[a1][a2];[a2]negate[mask];[a1][mask]overlay"),

// 44. OIL_SPILL: Colores que fluyen como gasolina en el agua (Interferencia de pelicula delgada)
("GASOLINA", "format=gbrp,geq=r='r(X,Y)*sin(T)':g='g(X,Y)*cos(T)':b='b(X,Y)*tan(T/10)'"),

// 45. DOUBLE_EXPOSURE: Superpone una version en negativo muy lenta sobre el video real
("DOPPEL", "split[a][b];[b]negate,format=yuva420p,lutalpha=val=60,setpts=2.0*PTS[slow];[a][slow]overlay=shortest=1"),

// 46. SCANNER_DARKLY: Estilo rotoscopia pesada con contornos de tinta china
("INK", "edgedetect=low=0.1:high=0.3,negate,format=gray,curves=all='0/0 0.2/0 0.8/1 1/1',smartblur=lr=5:ls=-1"),

// 47. KINETIC_ENERGY: Resalta UNICAMENTE lo que se esta moviendo, el resto queda en negro
("KINETIC", "format=gray,tblend=all_mode=difference,threshold=level=0.1,negate"),
*/
],



        }
    }

    pub fn obtener_vf(&self) -> String {
        if self.filtros_activos.is_empty() {
            return self.catalogo[0].1.to_string();
        }

        // Blindaje contra IDs inexistentes (Previene panics)
        self.filtros_activos.iter()
            .filter(|&&id| id < self.catalogo.len()) 
            .map(|&id| self.catalogo[id].1)
            .collect::<Vec<_>>()
            .join(",")
    }

    pub fn backup(&mut self) { 
        self.historial = self.filtros_activos.clone(); 
    }

    pub fn rollback(&mut self) { 
        self.filtros_activos = self.historial.clone(); 
    }
}