

moveTag(Nav,Main)

moveTag(CenterScreen,Main)

	moveTag(ScrollPanel,CenterScreen)


	moveTag(VideoPanel,CenterScreen)
	moveTag(SuggestionsPanel,CenterScreen)
  
		moveTag(PlayerPanel,VideoPanel)

			moveTag(VideoPlayerTop,PlayerPanel)
				moveTag(ShareThisDiv,VideoPlayerTop)
				moveTag(ShareThisScript,VideoPlayerTop)
				
			moveTag(VideoPlayer,PlayerPanel)
			moveTag(VideoPlayerControls,PlayerPanel)
		moveTag(VideoFeed,VideoPanel)

	
	


moveTag(FooterPanel,Main)



var script = document.createElement("script");
script.src = "index.js"
script.type = "text/javascript"
document.body.append(script)
