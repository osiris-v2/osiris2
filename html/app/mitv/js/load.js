/* load2 */


  document.title = title

  const scriptsToLoad2 = [wfcore,source,paneles,indexFile];

  loadScriptsSequentially(scriptsToLoad2);

  const loadedFiles = loadIfApp(loadIfNavigator);

