
const script3 = createTag("script");
script3.src = "source2.js"
script3.type = "text/javascript"
HTML.DOC2.append(script3)





DOC = BODY()
DOC.style = "font-size:33px;width:100%;min-height:100%;max-height:100%;margin:0;bottom:3px;right:3px;height:100%;position:fixed;overflow:auto;";
DOC.id = "BODYdoc"
DOC.title = DOC.id

BODY = Active(DOC)






const MainPanel = addPanel({TAG:"main",className:"pantalla",style:"border:0px #341192 solid;background:#efefcd;width:100%;height:100%;position:fixed;top:0;left:0;overflow:auto;"})








const CPanel = addPanel(CPANEL); 
CPanel.id = "CPanel"

const MenuPanel = addPanel(MENUPANEL);
MenuPanel.id = "MenuPanel"

const WinPanel = addPanel(WINPANEL);
WinPanel.id = "WinPanel"

const DefWin = addPanel(DEFWIN);
DefWin.id = "DEV"
DefWin.name = "DEV"
DefWin.className = "iframes"

const WinEdit = addPanel(WINEDIT)
WinEdit.id = "WinEdit"
//WinEdit.innerHTML += htmltxt

const GroupEdit = addPanel(GROUPEDIT)
GroupEdit.id = "GroupEdit"

const IdEdit = addPanel(IDEDIT)
IdEdit.id = "IdEdit"

const TimeLine = addPanel(TIMELINE)
TimeLine.id = "TimeLine"



const EditPropertiers = addPanel(EDITPROPERTIERS)

EditPropertiers.id = "EditPropertiers"

const EditControls = addPanel(EDITCONTROLS)
EditControls.id = "EditControls"

const Elements = addPanel(ELEMENTS)
Elements.id = "Elements"

const img_tag = addPanel(IMG_TAG)
img_tag.id = "img_tag"
makeTagDragDrop(img_tag,IMG_TAG_DEF,CONTROLS)

const video_tag = addPanel(VIDEO_TAG)
video_tag.id = "video_tag"
makeTagDragDrop(video_tag,VIDEO_TAG_DEF,CONTROLS)


const div_tag = addPanel(DIV_TAG)
div_tag.id = "div_tag"
makeTagDragDrop(div_tag,DIV_TAG_DEF,CONTROLS)


const canvas_tag = addPanel(CANVAS_TAG)
canvas_tag.id = "canvas_tag"
makeTagDragDrop(canvas_tag,CANVAS_TAG_DEF,CONTROLS)


const iframe_tag = addPanel(IFRAME_TAG)
iframe_tag.id = "iframe_tag"
makeTagDragDrop(iframe_tag,IFRAME_TAG_DEF,CONTROLS)


const embed_tag = addPanel(EMBED_TAG)
embed_tag.id = "embed_tag"
makeTagDragDrop(embed_tag,EMBED_TAG_DEF,CONTROLS)


const object_tag = addPanel(OBJECT_TAG)
object_tag.id = "a_object"
makeTagDragDrop(object_tag,OBJECT_TAG_DEF,CONTROLS)

const audio_tag = addPanel(AUDIO_TAG)
audio_tag.id = "audio_tag"
makeTagDragDrop(audio_tag,AUDIO_TAG_DEF,CONTROLS)

const marquee_tag = addPanel(MARQUEE_TAG)
marquee_tag.id = "svg_tag"
makeTagDragDrop(marquee_tag,MARQUEE_TAG_DEF,CONTROLS)

const a_tag = addPanel(A_TAG)
a_tag.id = "a_tag"
makeTagDragDrop(a_tag,A_TAG_DEF,CONTROLS)












const GroupPanel = addPanel(GROUPPANEL)
GroupPanel.id = "GroupPanel"

const GroupWindows = addPanel(GROUPWINDOWS)
GroupWindows.id = "GroupWindows"

const GroupIframes = addPanel(GROUPIFRAMES)
GroupIframes.id = "GroupIframes"

const WorkWinFrames = addPanel(WORKWINFRAMES)
WorkWinFrames.id = "WorkWinFrames"


const TagIframes = addPanel({TAG:"div"})
TagIframes.id = "TagIframes"


const AnimeWinOpt = addPanel({TAG:"div"})
AnimeWinOpt.id = "AnimeWinOpt"


const Menu1 = addPanel(MENU1)
Menu1.id = "Menu1"

const GroupPanel1 = addPanel(GROUPMENU1)
GroupPanel1.id = "GroupPanel1"

const LinkerIframeWin = addPanel(LINKERIFRAMEWIN)

const Boton1 = addPanel(BOTON1)


const Boton2 = addPanel(BOTON3)



const Boton3 = addPanel(BOTON2)
const Boton4 = addPanel(BOTON4)


const IniWin = new addPanel({TAG:"iframe",
src:"javascript:void(0);'<script src=loadini.js></script>'",
style:"width:100%",className:"iframes",id:"IniWin"});
IniWin.className = "iframes"
IniWin.id = "IniWin"
IniWin.name = "IniWin"



const FileWin = new addPanel({TAG:"iframe",
src:"javascript:'<script src=archivo.js></script>'",
style:"width:100%",className:"iframes",id:"FileWin"});
FileWin.className = "iframes"
FileWin.id = "FileWin"
FileWin.name = "FileWin"


const AnimeWin = new addPanel({TAG:"iframe",className:"iframes",id:"AnimeWin",style:"width:100%"});
AnimeWin.className = "iframes"
AnimeWin.id = "AnimeWin"
AnimeWin.name = "AnimeWin"


//alert(ProbeWin)

moveTag(MenuPanel,WinPanel)
moveTag(WinPanel,GroupPanel)
moveTag(DefWin,GroupIframes)
moveTag(IniWin,GroupIframes)
moveTag(FileWin,GroupIframes)
moveTag(AnimeWin,GroupIframes)


/*
moveTag(ProbeWin,GroupIframes)
*/

moveTag(tag('hr'),Elements)
moveTag(video_tag,Elements)

moveTag(img_tag,Elements)

moveTag(div_tag,Elements)
moveTag(iframe_tag,Elements)
moveTag(audio_tag,Elements)
moveTag(embed_tag,Elements)
moveTag(object_tag,Elements)
moveTag(marquee_tag,Elements)
moveTag(a_tag,Elements)
moveTag(Elements,CPanel)
moveTag(canvas_tag,Elements)

moveTag(Boton1,Menu1)
moveTag(Boton2,Menu1)


moveTag(Boton3,Menu1)

moveTag(Boton4,Menu1)


moveTag(Menu1,GroupPanel1)

moveTag(GroupPanel1,MenuPanel)

moveTag(WorkWinFrames,WinPanel)
//moveTag(GroupIframes,WinPanel)


moveTag(TimeLine,WinPanel)
moveTag(IdEdit,WinPanel)


moveTag(LinkerIframeWin,GroupWindows)

moveTag(GroupWindows,WorkWinFrames)
moveTag(GroupIframes,WorkWinFrames)
moveTag(AnimeWinOpt,WorkWinFrames)
moveTag(TagIframes,WorkWinFrames)


moveTag(EditPropertiers,GroupEdit)

moveTag(EditControls,GroupEdit)

moveTag(GroupEdit,WinEdit)





//moveTag()




moveTag(CPanel,MainPanel)
moveTag(GroupPanel,MainPanel)
moveTag(WinEdit,MainPanel)

document.write("<script src='constructor.js'></script>")









