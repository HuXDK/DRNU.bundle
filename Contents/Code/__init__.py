import time
####################################################################################################

VIDEO_PREFIX = "/video/drnu"
MUSIC_PREFIX = "/music/drnu"
BETA_EXCLUDE = ['DR HD']

APIURL = "http://www.dr.dk/nu/api/%s"
TV_NOWNEXT_URL = "http://www.dr.dk/nu/api/nownext"
RADIO_NOWNEXT_URL = "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/programInfo.drxml?channelId=%s"
RADIO_TRACKS_URL = "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/trackInfo.drxml?channelId=%s"
NAME  = "DR NU"
ART   = 'art-default.jpg'
ICON  = 'DR_icon-default.png'
bwInt = {"high":1000, "medium":500, "low":250, "auto":20000}
jsDrLive = "http://www.dr.dk/nu/embed/live?height=467&width=830"
jsDrRadioLive = "http://www.dr.dk/radio/channels/channels.json.drxml/"
drODServices = {"TV":[{"title":"Nyeste",
			"summary":"De nyeste videos",
			"json":"videos/newest.json"},
			{"title":"Spot",
			"summary":"Spot light",
			"json":"videos/spot.json"},
			{"title":"Mest sete",
			"summary":"Mest sete",
			"json":"videos/mostviewed.json"},
			{"title":"Sidste chance",
			"summary":"Tidbegrænsede videoer som er ved at udløbe",
			"json":"videos/lastchance.json"}]}

HTTP.CacheTime = 3600

####################################################################################################

def Start():
	Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, ICON, ART)
	Plugin.AddPrefixHandler(MUSIC_PREFIX, MusicMainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	MediaContainer.art = R(ART)
	MediaContainer.title1 = NAME
	DirectoryItem.thumb = R(ICON)
	HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.7; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13"

def VideoMainMenu():
	dir = ObjectContainer(view_group = "List", title1 = "DR NU", title2 = "TV", art = R(ART))
	dir.add(DirectoryObject(title = "Live TV", summary = "Se Live TV", art = R(ART),  thumb = R(ICON), key = Callback(LiveTV)))
	dir.add(DirectoryObject(title = "Programmer", summary = "Alle Programserier", art = R(ART), thumb = R(ICON), key = Callback(ProgramSerierMenu,id = None, title = "Programmer")))	
	for tvOD in drODServices["TV"]:
		dir.add(DirectoryObject(title = tvOD['title'], summary = tvOD['summary'], thumb = R(ICON), art = R(ART), key = Callback(CreateVideoItem, title = tvOD['title'], items = JSON.ObjectFromURL(APIURL % tvOD['json']))))
	dir.add(DirectoryObject(title = "Radio", summary = "Lyt til radio", art = R(ART), thumb = R(ICON), key = Callback(MusicMainMenu)))
	dir.add(PrefsObject(title = "Indstillinger...", summary="Indstil DR NU plug-in", thumb = R(ICON), art = R(ART)))
	return dir


def MusicMainMenu():
	dir = ObjectContainer(view_group="List", title1 = "DR NU", title2 = "Radio", art = R(ART))
	dir.add(DirectoryObject(title = "Live Radio", summary = "Lyt til Live Radio", art = R(ART), thumb = R(ICON), key = Callback(LiveRadioMenu)))
	dir.add(DirectoryObject(title = "TV", summary = "Lyt til radio", art = R(ART), thumb = R(ICON), key = Callback(VideoMainMenu)))
	dir.add(PrefsObject(title = "Indstillinger...", summary="Indstil DR NU plug-in", thumb = R(ICON), art = R(ART)))
	return dir

def LiveRadioMenu():
	dir = ObjectContainer(view_group = "List", title1 = "DR NU", title2 = "Live Radio", art = R(ART))
	P4dir = ObjectContainer(view_group = "List", title1 = "DR NU", title2 = "P4", art = R(ART))
	liveChannels = JSON.ObjectFromURL(jsDrRadioLive)
	groupList = []
	[dir.add(getLiveRadioChannel(channel)) for channel in liveChannels if channel['group'] is None]
	groupList.append([channel for channel in liveChannels if (channel['group'] is not None) & (channel['group'] not in groupList) ])
	[dir.add(DirectoryObject(title = channel[0]['group'], key = Callback(LiveRadioP4Menu, channel = channel))) for channel in groupList]
	
	return dir

def getLiveRadioChannel(source):
	
	vco = VideoClipObject(title = source['title'], summary = source['title'] if source['message'] is None else source['message'].lstrip('(').rstrip(')'), url = "http://www.dr.dk/radio/player/#" + String.StripDiacritics(source['source_url']), art = R(ART), thumb = source['logo'] if source['logo'] is not "" else R(ICON))
	return vco

def LiveRadioP4Menu(channel):
	dir = ObjectContainer(view_group="List",title1 = "DR NU", title2 = "P4", art = R(ART))
	[dir.add(getLiveRadioChannel(str)) for str in channel]
	return dir

def LiveTV():
	liveTVChannels = JSON.ObjectFromString(HTTP.Request(jsDrLive).content.split("'liveStreams':")[1].split("};")[0])
	dir = ObjectContainer(view_group="List", title1 = "DR NU", title2 = "Live TV", art = R(ART) )
	channelList = []
	channelList.append(liveTVChannels)
	for channels in [val for val in channelList[0] if val['channelName'] not in BETA_EXCLUDE] if Prefs['beta_enable'] is False else channelList[0]:
			channelIcon = channels['channelName'].upper().replace(' ','_')+"_icon-default.png"
			dir.add(VideoClipObject(title = channels['channelName'], 
								url = "http://www.dr.dk/nu/live#/%s" % channels['channelName'],
								thumb = R(channelIcon),
								art = R(ART),
								summary = getTVLiveMetadata(channels['channelName'])))
	return dir

def ProgramSerierMenu(id,title):
	dir = ObjectContainer(view_group = "List", title1 = "DR NU", title2 = title )
	JSONObject=JSON.ObjectFromURL(APIURL % "programseries.json")

	bucket = dict()
	letter = ''
	for program in JSONObject:
		slug=program["slug"]
		title=program["title"]
		if program["videoCount"] > 1:
			title = title + " (" + str(program["videoCount"]) + " afs.)"
		subtitle=", ".join(program["labels"])
		
		summary=program["description"]
		thumb=APIURL % "programseries/" + slug + "/images/512x512.jpg"

		letter = title[0].upper()
		if letter not in bucket:
			bucket[letter] = list()
		tuple = dict(title=title,subtitle=subtitle,thumb=thumb,summary=summary,id=slug)
		bucket[letter].append(tuple)

	for firstChar in sorted(bucket.iterkeys()):
		serier = bucket[firstChar]
		if Prefs['group_per_letter']:
			dir.add(DirectoryObject(title = firstChar, 
								art = R(ART), 
								thumb = R(ICON), 
								key = Callback(LetterMenu, 
											title = firstChar, 
											serier = serier )))
		
		else:
			for serie in serier:
				dir.add(DirectoryObject(title = serie['title'], 
									tagline = serie['subtitle'], 
									summary = serie['summary'], 
									art = R(ART), 
									thumb = thumb, 
									key = Callback(CreateVideoItem, 
												items = JSON.ObjectFromURL(APIURL % "programseries/"+serie['id'] + "/videos"),
												title = serie['title'])))
			
	return dir

def LetterMenu(title, serier):
	dir = ObjectContainer(view_group="List", title1 = "DR NU", title2 = title)
	for serie in serier:
		JSONobj = JSON.ObjectFromURL(APIURL % "Programseries/" + serie['id'] + "/videos")
		dir.add(DirectoryObject(title = serie['title'], summary = serie['summary'], art = R(ART), thumb = APIURL % "programseries/"+serie['id']+"/images/512x512.jpg", key = Callback(CreateVideoItem, items = JSONobj, title = serie['title'])))
	return d
		
def CreateVideoItem(items, title):
	dir = ObjectContainer(view_group = "List", title1 = "DR NU", title2 = title)

	titles = set()
	for item in items:
		key=APIURL % "videos/" + str(item["id"])
		thumb=APIURL % "videos/" + str(item["id"]) + "/images/512x512.jpg"

		if 'imagePath' in item:
			art="http://dr.dk/nu" + item["imagePath"]
		elif 'programSerieSlug' in item:
			art="http://dr.dk/nu/api/programseries/" + item['programSerieSlug'] + "/images/1024x768.jpg"
		else:
			art=thumb

			
		if 'spotTitle' in item:
			title=item["spotTitle"]
		elif 'name' in item:
			title=item["name"]
		else:
			title=item["title"]

		if 'isPremiere' in item:
			isPremiere = item["isPremiere"]
		elif 'premiere' in item:
			isPremiere = item['premiere']

		if isPremiere:
			title = title + " *PREMIERE* "
			
		if 'spotSubTitle' in item:
			summary=item["spotSubTitle"]
			subtitle=None
		else:
			summary=item["description"]
			if item['broadcastChannel'] and item['formattedBroadcastTime'] is None:
				subtitle=item["broadcastChannel"]
			elif item['broadcastChannel'] is None and item['formattedBroadcastTime']:
				subtitle=str(item["formattedBroadcastTime"])
			else:
				subtitle=str(item["formattedBroadcastTime"]) + " on " + str(item["broadcastChannel"])
			
			if 'duration' in item:
				subtitle = subtitle + " ["+ str(item["duration"]) + "]"

		if 'videoResourceUrl' in item:
			JSONvideoUrl=item["videoResourceUrl"]
		else:
			JSONvideoUrl = str(JSON.ObjectFromURL(key)["videoResourceUrl"])

		content = JSON.ObjectFromURL(JSONvideoUrl)

		if 'restrictedToDenmark' in content:
			dkOnly = content['restrictedToDenmark']
		else:
			dkOnly = false

		if "name" in content:  ## this is the case for some entries in TV AVISEN
			title = content["name"]

		## hack to get repeated shows to show up with dates
		if title.upper() in titles:
			if 'formattedBroadcastTime' in item:
				title = title + " " + str(item['formattedBroadcastTime'])
			else:
				title = title + " " + subtitle

		if dkOnly and Locale.Geolocation != "DK":
			title = title + " [DK Only] " 

		titles.add(title.upper())
		

		vco = VideoClipObject(title = title, summary = summary, thumb = thumb, url = key)
		if len(content['links'])>0:
			for video in content['links']:
				mo = MediaObject()
				
				if 'bitrateKbps' in video:
					mo.bitrate = video['bitrateKbps']
				else:
					mo.bitrate = 100
				if mo.bitrate <= bwInt[Prefs['quality']]:
					if 'height' in video:
						height = video['height']
					else:
						height = None
						
					if 'width' in video:
						width = video['width']
					else:
						width = None 
	
					if video['fileType'] == "mp4":
						baseUrl = "rtmp://vod.dr.dk/cms/"
						clip = "mp4:" + video["uri"].split(":")[2]
						po = PartObject(key = RTMPVideoURL(baseUrl, clip = clip, height = height, width = width, live = False))
						#Log.Debug("Adding WM PO - key: " + po.key)
					elif video['fileType'] == "wmv":
						po = PartObject(key = WindowsMediaVideoURL(video[uri], height = height, width = width))
					else:
						po = PartObject(key = video['uri'])
					mo.add(po)
					vco.add(mo)
		else:
			vco.add(MediaObject(parts = [PartObject(key = JSON.ObjectFromURL(key)["videoManifestUrl"])]))
		dir.add(vco)
	return dir

def getRadioMetadata(channelId):
	
	# This is a undocumented feature that might break the plugin.
	JSONobj = JSON.ObjectFromURL(RADIO_NOWNEXT_URL % channelId, cacheTime = 60)
	title_now = ""
	description_now = ""
	start_now = ""
	stop_now = "" 
	title_next = "" 
	description_next = "" 
	start_next = ""
	stop_next = ""
	trackop = ""
	
	if JSONobj['currentProgram']:
		if JSONobj['currentProgram']['title']:
			title_now = String.StripTags(JSONobj['currentProgram']['title']).replace("'","\'")
		if JSONobj['currentProgram']['description']:
			description_now = "\n" + String.StripTags(JSONobj['currentProgram']['description']).replace("'","\'")
		if JSONobj['currentProgram']['start'] and JSONobj['currentProgram']['stop']:
			start_now = "'\n" +JSONobj['currentProgram']['start'].split('T')[1].split(':')[0]+":"+JSONobj['currentProgram']['start'].split('T')[1].split(':')[1]
			stop_now = "-"+JSONobj['currentProgram']['stop'].split('T')[1].split(':')[0]+":"+JSONobj['currentProgram']['stop'].split('T')[1].split(':')[1]

	if JSONobj['nextProgram']:
		if JSONobj['nextProgram']['title']:
			title_next = "\n\n" + String.StripTags(JSONobj['nextProgram']['title']).replace("'","\'")
		if JSONobj['nextProgram']['description']:
			description_next = "\n" + String.StripTags(JSONobj['nextProgram']['description']).replace("'","\'")
		if JSONobj['nextProgram']['start'] and JSONobj['nextProgram']['stop']:
			start_next = "\n" + JSONobj['nextProgram']['start'].split('T')[1].split(':')[0]+":"+JSONobj['nextProgram']['start'].split('T')[1].split(':')[1]
			stop_next = "-" + JSONobj['nextProgram']['stop'].split('T')[1].split(':')[0]+":"+JSONobj['nextProgram']['stop'].split('T')[1].split(':')[1]

	try:
		JSONobjTracks = JSON.ObjectFromURL(RADIO_TRACKS_URL % channelId, cacheTime=30, errors='Ingore')
		if JSONobjTracks['tracks']:
			pre1 = "\n\nSeneste Titel: "
			for track in JSONobjTracks['tracks']:
				if track['displayArtist']:
					trackop = trackop + pre1 + track['displayArtist']
				if track['title']:
					trackop = trackop + "\n" + track['title'] + "\n\n"
				pre1 = "Forrige: "
	except:pass			
					
	strNowNext = title_now + description_now + start_now + stop_now + title_next + description_next + start_next + stop_next + trackop
		
	return strNowNext

def getTVLiveMetadata(channelID):
	# this is a undocumented feature that might break the plugin

	channels = JSON.ObjectFromURL(TV_NOWNEXT_URL, cacheTime=60)
	title_now = "Ingen titel tilgængenlig"
	title_next = "Ingen titel tilgængenlig"
	description_now = ""
	description_next = ""
				
	for channel in channels["channels"]:
		if channelID in channel['channel'] :
			if channel['current']:
				if channel['current']:
					title_now = channel['current']['programTitle']
				if channel['current']['description']:
					description_now = channel['current']['description']
			if channel['next']:
				if channel['next']['programTitle']:
					title_next = channel['next']['programTitle']
				if channel['next']['description']:
					description_next = channel['next']['description']
			break
				
	title = "Nu: " + title_now + "\n" + description_now  + "\n\nNaeste: " + title_next + "\n" + description_next
			
	return str(String.StripTags(title))
