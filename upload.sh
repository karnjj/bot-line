#!/bin/bash
echob "start"
git add . 
git commit -am "make it better"
git push heroku master
