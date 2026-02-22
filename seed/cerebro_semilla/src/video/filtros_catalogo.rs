vec![
    // [0] BASE
    ("BASE",       "format=yuv420p"),

    // ── VISIÓN TÁCTICA ────────────────────────────────────────
    ("BORDES",     "edgedetect=low=0.1:high=0.4,format=yuv420p"),
    ("NOCHE",      "hue=s=0,curves=all='0/0 0.5/0.8 1/1',format=yuv420p"),
    ("XRAY",       "negate,curves=all='0/0 0.5/0.5 1/0.9',format=yuv420p"),
    ("THERMAL",    "format=gbrp,lutrgb=r=maxval:g=0:b=0,colorlevels=rimin=0.05:gimin=0.05:bimin=0.05,colormatrix=bt709:fcc,format=yuv420p"),
    ("INFRA",      "format=gbrp,colorchannelmixer=rr=0:gr=1:br=0:rg=0:gg=0:bg=1:rb=0:gb=0:bb=0,hue=s=0.5:h=180,format=yuv420p"),
    ("RADAR",      "format=gray,lutrgb=g=val*1.5:r=0:b=0,drawbox=y=ih/2:w=iw:h=2:t=1:c=green@0.8,format=yuv420p"),
    ("PREDATOR",   "split[a][b];[a]format=gbrp,lutrgb=r=val*2:g=val/2:b=0[thermal];[b]edgedetect=low=0.1:high=0.2,negate[edges];[thermal][edges]blend=all_mode=screen,format=yuv420p"),
    ("SOBEL",      "format=gray,sobel,negate,format=yuv420p"),
    ("EMBOSS",     "format=gray,sobel,curves=all='0/0.5 1/1',format=yuv420p"),
    ("KINETIC",    "format=gray,tblend=all_mode=difference,curves=all='0/0 0.1/0 0.15/1 1/1',negate,format=yuv420p"),

    // ── DIGITAL / GLITCH ──────────────────────────────────────
    ("GLITCH",     "noise=alls=100:allf=t+u,hue=h=20:s=3,format=yuv420p"),
    ("CORRUPT",    "noise=alls=40:allf=t+u,hue=h=120:s=3,chromashift=cbh=30:crv=20,format=yuv420p"),
    ("VHSLINES",   "split[a][b];[b]noise=alls=20:allf=t+u[n];[a][n]blend=all_mode=overlay,drawgrid=w=iw:h=3:t=1:c=black@0.4,format=yuv420p"),
    ("CRT",        "lenscorrection=k1=0.1:k2=0.1,chromashift=cbh=10:crv=10,vignette=angle=0.5,format=yuv420p"),
    ("SCANLINE",   "split[a][b];[b]noise=alls=20:allf=t+u,hue=s=0[noise];[a][noise]blend=all_mode=overlay:all_opacity=0.3,drawgrid=w=iw:h=2:t=1:c=black@0.5,format=yuv420p"),
    ("FLICKER",    "noise=alls=30:allf=t,hue=s=1.5,format=yuv420p"),
    ("MATRIX",     "format=gray,lutrgb=g=val*2:r=0:b=0,curves=all='0/0 0.5/0.2 1/1',format=yuv420p"),
    ("PHOSPHOR",   "format=gray,curves=r='0/0 1/0.2':g='0/0 0.5/0.8 1/1':b='0/0 1/0.1',format=yuv420p"),

    // ── CYBERPUNK / NEÓN ──────────────────────────────────────
    ("CYBER",      "hue=h=90:s=2,chromashift=cbh=20:crv=20,unsharp=5:5:1.0:5:5:0.0,format=yuv420p"),
    ("NEON",       "split[orig][edges];[edges]edgedetect=low=0.1:high=0.2,negate,hue=h=200:s=2[neon];[orig][neon]blend=all_mode=lighten,format=yuv420p"),
    ("RETROWAVE",  "hue=h=270:s=2,chromashift=cbh=10:crv=10,curves=all='0/0 0.5/0.3 1/1',format=yuv420p"),
    ("ACID",       "chromashift=cbh=20:cbv=20:crh=-20:crv=-20,hue=h=150:s=1.5,curves=all='0/0 0.3/0.6 1/1',format=yuv420p"),
    ("SHELL",      "split[a][b];[a]hue=s=0[gray];[b]edgedetect=low=0.1:high=0.2,negate,hue=h=180:s=2[edges];[gray][edges]blend=all_mode=screen,format=yuv420p"),
    ("NEURO",      "drawgrid=w=20:h=20:t=1:c=cyan@0.3,curves=all='0/0 0.5/0.7 1/1',hue=h=180:s=0.5,format=yuv420p"),

    // ── CINEMATOGRÁFICO / GRANO ───────────────────────────────
    ("NOIR",       "format=gray,curves=all='0/0 0.4/0.1 0.6/0.9 1/1',vignette,noise=alls=25:allf=t,format=yuv420p"),
    ("DAGUERRO",   "format=gray,curves=all='0/0 0.3/0.1 0.7/0.9 1/1',vignette,noise=alls=15:allf=t,format=yuv420p"),
    ("SUPER8",     "curves=vintage,noise=alls=20:allf=t,vignette,format=yuv420p"),
    ("VELVIA",     "curves=r='0/0 0.5/0.6 1/1':g='0/0 0.5/0.55 1/0.95':b='0/0 0.5/0.4 1/0.9',hue=s=1.4,format=yuv420p"),
    ("LOMO",       "vignette,curves=all='0/0 0.3/0.2 0.7/0.8 1/1',hue=s=1.3,format=yuv420p"),
    ("POLAROID",   "curves=all='0/0.05 0.5/0.55 1/0.95',hue=s=0.7,vignette,format=yuv420p"),
    ("XPROCESS",   "curves=r='0/0.1 0.5/0.4 1/0.9':g='0/0 0.5/0.6 1/1':b='0/0.2 0.5/0.5 1/0.8',hue=s=1.3,format=yuv420p"),
    ("SEPIA",      "hue=s=0,curves=r='0/0 1/1':g='0/0 1/0.78':b='0/0 1/0.4',format=yuv420p"),
    ("FLARE",      "curves=all='0/0 0.7/0.9 1/1',gblur=2,hue=s=0.8,format=yuv420p"),
    ("HAZE",       "gblur=3,curves=all='0/0.1 1/1',hue=s=0.6,format=yuv420p"),

    // ── COLOR GRADING ─────────────────────────────────────────
    ("TEAL",       "colorchannelmixer=rr=0.7:gg=1.1:bb=1.3,hue=s=1.3,format=yuv420p"),
    ("ORANGE",     "curves=r='0/0.1 1/1':g='0/0 1/0.7':b='0/0 1/0.4',hue=s=1.2,format=yuv420p"),
    ("BLUEPRINT",  "hue=s=0,curves=b='0/0.2 1/1':r='0/0 1/0.3':g='0/0.1 1/0.5',format=yuv420p"),
    ("MILITARY",   "hue=s=0,curves=g='0/0 0.5/0.6 1/1':r='0/0 1/0.8':b='0/0 1/0.3',format=yuv420p"),
    ("COLDWAR",    "hue=s=0,colorchannelmixer=rr=0.8:gg=0.9:bb=1.1,curves=all='0/0.05 1/0.9',format=yuv420p"),
    ("BURN",       "curves=all='0/0 0.3/0.5 1/1',colorchannelmixer=rr=1.2:gg=0.9:bb=0.7,format=yuv420p"),
    ("DUOTONO",    "hue=s=0,curves=r='0/0 1/0.8':b='0/0 1/0.2',format=yuv420p"),
    ("SOLAR",      "curves=all='0/0 0.25/0.5 0.5/0.8 0.75/0.5 1/0',hue=s=0.3,format=yuv420p"),

    // ── ARTÍSTICOS ────────────────────────────────────────────
    ("MONET",      "smartblur=lr=5:ls=-1:lt=1,hue=s=1.5,curves=all='0/0 0.5/0.6 1/1',format=yuv420p"),
    ("OILPAINT",   "smartblur=lr=3:ls=1:lt=0,unsharp=7:7:1.5,format=yuv420p"),
    ("MANGA",      "format=gray,edgedetect=low=0.05:high=0.15,negate,curves=all='0/0 0.5/0 1/1',format=yuv420p"),
    ("SKETCH",     "format=gray,edgedetect=low=0.05:high=0.2,negate,smartblur=lr=1:ls=-1:lt=0,format=yuv420p"),
    ("CROSSHATCH", "split[a][b];[a]format=gray,sobel[s];[b]format=gray,sobel,hue=h=90[s2];[s][s2]blend=all_mode=screen,negate,format=yuv420p"),
    ("FRACTAL",    "split[a][b];[b]negate,hue=h=90:s=2[inv];[a][inv]blend=all_mode=difference,format=yuv420p"),
    ("REDACT",     "format=gray,negate,curves=all='0/0 0.49/0 0.5/1 1/1',noise=alls=40:allf=p,format=yuv420p"),
    ("CUBISMO",    "spp=6:4,format=yuv420p"),

    // ── MOVIMIENTO / ESPACIO ──────────────────────────────────
    ("GHOST",      "split[a][b];[a]format=yuva420p,lut=a=128[a_trans];[b]lagfun=decay=0.9[b_slow];[b_slow][a_trans]overlay,format=yuv420p"),
    ("PINTURA",    "nlmeans=s=7,unsharp=5:5:1.0,format=yuv420p"),
    ("VERTIGO",    "split[a][b];[b]rotate=1*PI/180:c=black@0,format=yuva420p,lut=a=150[r];[a][r]overlay,lagfun=decay=0.95,format=yuv420p"),
    ("STARDUST",   "split[a][b];[b]noise=alls=80:allf=t,gblur=10[noise];[a][noise]blend=all_mode=screen,hue=h=45:s=2,format=yuv420p"),
    ("NEBULA",     "split[a][b];[b]gblur=5,hue=h=300:s=3[blur];[a][blur]blend=all_mode=lighten:all_opacity=0.7,format=yuv420p"),
    ("ZOOMBLUR",   "split[a][b];[b]vignette=angle=0.5,gblur=10[v];[a][v]blend=all_mode=lighten,format=yuv420p"),
    ("MIRROR",     "split[a][b];[b]scale=iw/1.5:ih/1.5,pad=iw:ih:(ow-iw)/2:(oh-ih)/2:black@0[inner];[a][inner]overlay=format=yuv420,format=yuv420p"),

    // ── VAPORWAVE / RETRO ─────────────────────────────────────
    ("VAPOR",      "curves=vintage,drawbox=y=ih/2:w=iw:h=1:t=1:c=black@0.5,tinterlace=mode=interleave_top,format=yuv420p"),
    ("AMBER",      "format=gray,lutrgb=r=val:g=val*0.6:b=0,noise=alls=15:allf=t,curves=all='0/0 0.5/0.4 1/1',format=yuv420p"),
    ("SINCITY",    "hue=s=0,curves=all='0/0 0.3/0 0.7/1 1/1',format=yuv420p"),
    ("INK",        "edgedetect=low=0.1:high=0.3,negate,format=gray,curves=all='0/0 0.2/0 0.8/1 1/1',smartblur=lr=5:ls=-1,format=yuv420p"),
    ("PLASMA",     "hue=h=60:s=2,colorchannelmixer=rr=1.3:gg=0.8:bb=1.5,format=yuv420p"),
]