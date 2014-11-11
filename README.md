EngineReader
============

RSS Reader

Working sample is [here](http://enginereader-test.appspot.com/).

How to execute EngineReader.
------------

### Execute in local environment.

Clone source files from github.  
`$ git clone https://github.com/lostman-github/EngineReader.git`

Execute development web server.  
`$ dev_appserver.py EngineReader/`

Connect to web server.  
`http://localhost:8080/`

### Deploy to AppEngine.

Clone source files from github.  
`$ git clone https://github.com/lostman-github/EngineReader.git`

Edit application name for AppEngine.  
The value of application must be changed to your application name of AppEngine.  
`$ vi EngineReader/app.yaml`

Deploy to AppEngine.  
`$ appcfg.py update EngineReader/`

Connect to application using WebBrowser.  
`http://<your applicetion name>.appspot.com/`

About version number.
------------
```
v0.1.0
 | | |
 | | + -- bug fixes
 | + ---- new feature
 + ------ something big changes
```
