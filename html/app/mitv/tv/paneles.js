DOC = BODY()
DOC.id = "body"
BODY = Active(DOC)
//alert(HTML.DOC)

const Main = addPanel(MAIN)

const Nav = addPanel(NAV)

const CenterScreen = addPanel(CENTER_SCREEN)

const ScrollPanel = addPanel(SCROLL_PANEL)

const VideoPanel = addPanel(VIDEO_PANEL)

const PlayerPanel = addPanel(PLAYER_PANEL)

const VideoPlayerTop = addPanel(VIDEO_PLAYER_TOP)

const ShareThisDiv = addPanel(SHARE_THIS_DIV)

const ShareThisScript = addPanel(SHARE_THIS_SCRIPT)
ShareThisScript.async = "true"

const VideoPlayer = addPanel(VIDEO_PLAYER)
VideoPlayer.id = "Player"

const VideoPlayerControls = addPanel(VIDEO_PLAYER_CONTROLS)

const VideoFeed = addPanel(VIDEO_FEED)

const SuggestionsPanel = addPanel(SUGGESTIONS_PANEL)

const FooterPanel = addPanel(FOOTER_PANEL)

var script = document.createElement("script");
script.src = "build.js"
script.type = "text/javascript"
document.head.append(script)

