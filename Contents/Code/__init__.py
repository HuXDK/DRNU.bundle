import re

#Ex.MediaNotAvailable
#Ex.MediaNotAuthorized
#Ex.MediaGeoblocked
#import time
#import datetime
###################################################################################################
VIDEO_PREFIX = "/video/drnu"
MUSIC_PREFIX = "/music/drnu"
BETA_EXCLUDE = ['']

RADIO_NOWNEXT_URL = "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/programInfo.drxml?channelId=%s"
RADIO_TRACKS_URL = "http://www.dr.dk/tjenester/LiveNetRadio/datafeed/trackInfo.drxml?channelId=%s"
NAME = unicode(L('name'))
ART = 'art-default.jpg'
ICON = 'icon-default.png'
jsDrRadioLive = "http://www.dr.dk/radio/channels/channels.json.drxml/"
BUNDLE_URL = 'http://www.dr.dk/mu/Bundle'
PROGRAMCARD_URL = 'http://www.dr.dk/mu/programcard'
PROGRAMVIEW_URL = 'http://www.dr.dk/mu/ProgramViews/'
BUNDLESWITHPUBLICASSET_URL = 'http://www.dr.dk/mu/View/bundles-with-public-asset'
CHANNEL_OMMIT = ['dr-web-1']
#CHANNEL = {'TVH':'DR HD','TVK':'DR K','DR1':'DR1','DR2':'DR2','TVR':'DR Ramasjang','TVU':'DR Update'}


####################################################################################################

def ValidatePrefs():
	
	Locale.DefaultLocale = Prefs['PO_LANG']


###################################################################################################

def Start():
	
	Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, NAME, R(ICON), R(ART))
#	Plugin.AddPrefixHandler(MUSIC_PREFIX, MusicMainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	ObjectContainer.art = R(ART)
#	ObjectContainer.thumb = R(ICON)
	DirectoryObject.art = R(ART)
	DirectoryObject.thumb = R(ICON)
	VideoClipObject.art = R(ART)
	VideoClipObject.thumb = R(ICON)
	
	HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.7; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13"
	HTTP.PreCache("http://www.dr.dk/mu/View/bundles-with-public-asset?ChannelType='TV'&limit=$eq(0)&DrChannel=true&Title=$orderby('asc')")
	
###################################################################################################

@route('/video/drnu')
def VideoMainMenu():
	
	# create OC
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = unicode(L('TVTitle')))
	
	# check if DR is available
	try:
		conf = JSON.ObjectFromURL('http://www.dr.dk/mu/Configuration')
	except :
		dir.header = unicode( L('jsonConnectionErrorTitle'))
		dir.message = unicode(L('jsonConnectionErrorMessage'))
	else:
		
		# add live stream
		dir.add(DirectoryObject(
							title 		=unicode( L('liveTVTitle')), 
							summary 	= unicode(L('liveTVSummary')), 
							key 		= Callback(Bundle, 
											title1		= NAME,
											title2		= unicode(L('liveTVTitle')),
											BundleType	="'Channel'", 
											ChannelType	="'TV'", 
											DrChannel 	= 'true', 
											limit		='$eq(0)', 
											SourceUrl	="$orderby('asc')")))
		
		#=======================================================================
		# # add live radio
		# dir.add(DirectoryObject(
		#					title 		= 'Live Radio', 
		#					summary 	= 'Lyt til live Radio', 
		#					key 		= Callback(LiveRadioMenu)))
		#=======================================================================
		
		# add program overview
		dir.add(DirectoryObject(
							title 		= unicode(L('programsTitle')), 
							summary 	= unicode(L('programsSummary')), 
							key 		= Callback(ProgramMenu)))
		
		# add news overview
		dir.add(DirectoryObject(
	 						title 		= unicode(L('newsTitle')), 
							summary 	= unicode(L('newsSummary')), 
							key 		= Callback(NewsMenu)))
							
		# add preview overview
		dir.add(DirectoryObject(
							title 		= unicode(L('preReleaseTitle')), 
							summary 	= unicode(L('preReleaseSummary')), 
							key 		= Callback(ProgramCard, 
											title1		= NAME,
											title2 		= unicode(L('preReleaseTitle')),
											Relations_Slug='"forpremierer"',
											limit		="$eq(0)")))
		
		# add preference
		#dir.add(PrefsObject(title = unicode(L('preferences'))))
		
		return dir
	
###################################################################################################

@route('/music/drnu')
def MusicMainMenu():
	
	# create OC
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = unicode(L('radioTitle')))
	
	# add radio overview
	dir.add(DirectoryObject(
						title 		= unicode(L('liveRadioTitle')), 
						summary 	= unicode(L('liveRadioSummary')), 
						key 		= Callback(LiveRadioMenu)))
	
	# add tv overview
	dir.add(DirectoryObject(
						title 		= unicode(L('tvFromRadioTitle')), 
						summary 	= unicode(L('tvFromRadioSummary')), 
						key 		= Callback(VideoMainMenu)))
	

	return dir

###################################################################################################

@route('/music/drnu/live')
def LiveRadioMenu():

	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = L("liveRadioTitle"), art = R(ART))
	for myLoop in CONFIGURATION['Data']:
		if myLoop.get('Id') == 'RADIOVisibleFrontPageChannels':
			for Order in myLoop['Order']:
				if '{' not in Order:
					drMeta = JSON.ObjectFromURL("http://www.dr.dk/mu/Bundle?BundleType='Channel'&ChannelType='RADIO'&DrChannel=true&limit=$eq(1)&SourceUrl=$eq('dr.dk/mas/whatson/channel/%s')" % Order.rsplit('/',1)[1])
					dir.add(VideoClipObject(title = drMeta['Data'][0]['Title'], url = 'http://www.dr.dk/radio/player/?%s' % 'P3'))
				else:
					dir.add(DirectoryObject(title = 'P4', key = Callback(LiveRadioP4Menu)))
	return dir

###################################################################################################

@route('/music/drnu/live/p4')
def LiveRadioP4Menu():
	
	# create OC
	dir = ObjectContainer(view_group="List",title1 = NAME, title2 = unicode(L('P4Title')))
	
	# try fetch url or raise exception
	try:
		conf = JSON.ObjectFromURL('http://www.dr.dk/mu/Configuration')
	except:
		raise Ex.MediaNotAvailable
	
	# run through all P4 channels
	for p4Loop in conf['Data']:
		
		if p4Loop.get('Id') == 'RADIOLocalNews':
			
			for ChannelsAndNews in p4Loop['ChannelsAndNews']:
				
				if '4' in ChannelsAndNews['PrimaryChannel']:
					
					channel 	= ChannelsAndNews['Cid']
					description = getRadioMetadata(channel);
					
					dir.add(VideoClipObject(
										title 		= ChannelsAndNews['Title'], 
										summary		= description,
										url 		= 'http://www.dr.dk/radio/player/?%s' % channel))
					
	return dir

###################################################################################################

@route('/video/drnu/programmenu')
def ProgramMenu():
	
	# create OC
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = unicode(L('programsTitle')))
		
	# add program overview by firstChar
	dir.add(DirectoryObject(
						title 		= unicode(L('programsByFirstCharTitle')), 
						summary 	= unicode(L('programsByFirstCharSummary')), 
						key 		= Callback(bundles_with_public_asset, 
											title 		= unicode(L('programsTitle')), 
											groupby 	= 'firstChar', 
											DrChannel	= "true", 
											ChannelType = "'TV'", 
											limit		="$eq(0)", 
											Title 		= "$orderby('asc')")))
	
	# add newest overview
	dir.add(DirectoryObject(
						title 		= unicode(L('mostWatchedProgramsTitle')), 
						summary 	= unicode(L('mostWatchedProgramsSummary')), 
						key 		= Callback(ProgramViews, 
											title 		= unicode(L('mostWatchedProgramsTitle')),
											type		= 'MostViewed',
											ChannelType = "'TV'", 
											limit		="$eq(0)",
											TotalViews	="$orderby('asc')")))
	
	# add newest overview
	dir.add(DirectoryObject(
						title 		= unicode(L('latestProgramsTitle')), 
						summary 	= unicode(L('latestProgramsSummary')), 
						key 		= Callback(ProgramViews, 
											title 		= unicode(L('latestProgramsTitle')),
											type		= 'RecentViews',
											ChannelType = "'TV'", 
											limit		="$eq(0)",
											TotalViews	="$orderby('asc')")))
	
	# add search options
	
	#dir.add(SearchDirectoryObject(identifier='com.plexapp.plugins.drnu', name='DR NU Search Service', title=unicode('searchTitle')))
#	dir.add(InputDirectoryObject(
#						title 		= unicode(L('searchTitle')), 
#						summary 	= unicode(L('searchSummary')),
#						prompt		= unicode(L('searchPrompt')),
#						key 		= Callback(bundles_with_public_asset, 
#											title 		= unicode(L('programsTitle')),
#											groupby 	= 'name', 
#											DrChannel	= "true", 
#											ChannelType = "'TV'", 
#											limit		="$eq(0)", 
#											Title 		= "$orderby('asc')")))
	dir.add(SearchDirectoryObject(identifier='com.plexapp.plugins.drnu', name='DRNU', title=unicode(L('searchTitle')), prompt = 'Search on dr.dk'))
	
	return dir

###################################################################################################

@route('/video/drnu/newsmenu')
def NewsMenu():
	
	# create OC
	dir = ObjectContainer(view_group = "List", title1 = NAME, title2 = unicode(L('newsTitle')))
		
	# add DR Update overview
	dir.add(DirectoryObject(
						title 		= unicode(L('newsUpdateTitle')), 
						summary 	= unicode(L('newsUpdateSummary')), 
						thumb 		= R('dr-update-2_icon-default.png'), 
						key 		= Callback(ProgramCard, 
										title2 		= unicode(L('newsUpdateTitle')),
										Relations_Slug ="'dr-update'",
										Assets_Kind	="'VideoResource'",
										Broadcasts_BroadcastDate ="$orderby('desc')",
										limit		="$eq(10)")))
	
	# add Deadline 17.00 overview
	dir.add(DirectoryObject(
						title 		= unicode(L('newsDeadline1700Title')), 
						summary 	= unicode(L('newsDeadline1700Summary')), 
						key 		= Callback(ProgramCard, 
										title2 		= unicode(L('newsDeadline1700Title')),
										Relations_Slug ="'deadline-17'",
										Assets_Kind	="'VideoResource'",
										Broadcasts_BroadcastDate ='$orderby("desc")',
										limit		="$eq(10)")))
	
	# add TV Avisen 18.30 overview
	dir.add(DirectoryObject(
						title 		= unicode(L('newsTVAvisen1830Title')), 
						summary 	= unicode(L('newsTVAvisen1830Summary')), 
						key 		= Callback(ProgramCard, 
										title2 		= unicode(L('newsTVAvisen1830Title')),
										Relations_Slug ="'tv-avisen-med-sporten'",
										Assets_Kind	="'VideoResource'",
										Broadcasts_BroadcastDate ="$orderby('asc')",
										limit		="$eq(10)")))
	
	# add TV Avisen 21.00 overview
	dir.add(DirectoryObject(
						title 		= unicode(L('newsTVAvisen2100Title')), 
						summary 	= unicode(L('newsTVAvisen2100Summary')), 
						key 		= Callback(ProgramCard, 
										title2 		= unicode(L('newsTVAvisen2100Title')),
										Relations_Slug ="'tv-avisen'",
										Assets_Kind	="'VideoResource'",
										Broadcasts_BroadcastDate ="$orderby('desc')",
										limit		="$eq(10)")))
	
	# add Deadline 22.30 overview
	dir.add(DirectoryObject(
						title 		= unicode(L('newsDeadline2230Title')), 
						summary 	= unicode(L('newsDeadline2230Summary')), 
						key 		= Callback(ProgramCard, 
										title2 		= unicode(L('newsDeadline2230Title')),
										Relations_Slug ="'deadline'",
										Assets_Kind	="'VideoResource'",
										Broadcasts_BroadcastDate ="$orderby('desc')",
										limit		="$eq(10)")))
	
	return dir

###################################################################################################

@route('/video/drnu/asset')
def Asset(**kwargs):
	return None

###################################################################################################

@route('/video/drnu/bar')
def Bar(**kwargs):
	return None

###################################################################################################

@route('/video/drnu/bundle/{title1}/{title2}')
def Bundle(title1 = NAME, title2 = NAME, **kwargs):
	
	# set variables
	
	#create OC
	dir = ObjectContainer(view_group="List", title1 = title1, title2 = title2)
		
	# try fetch url or raise exception
	try:
		programcards = JSON.ObjectFromURL(argsToURLString(APIURL = BUNDLE_URL, args = kwargs))
	except:
		pass
	
	# strip programcards
	programcards = stripProgramCards(programcards, False)
	
	# run through all channels
	for program in programcards:
				
		# Live
		if 'Channel' in kwargs.get('BundleType'):
			if program.get('Slug') not in CHANNEL_OMMIT:
				try:
					description = getTVLiveMetadata(program['Slug'])
				except:
					description = ''
				
				vco = VideoClipObject()
				vco.title = program.get('Title')
				vco.thumb = R('%s_icon-default.png' % program.get('Slug'))
				vco.summary = description 
				vco.tagline = program.get('Subtitle')
				vco.url = 'http://www.dr.dk/TV/live/%s' % program.get('Slug')
				dir.add(vco)
			
		# On-demand
		else:
			vco = getProgram(program) 
			dir.add(vco)
		
		# add vco to directory
#		dir.add(vco)
	
	return dir

###################################################################################################

@route('/video/drnu/programcard/{title1}/{title2}' )
def ProgramCard(title1 = NAME, title2 = NAME, **kwargs):
	
	dir = ObjectContainer(view_group = "List", title1 = title1, title2 = title2)
	
	# try to fetch program cards or raise exception
	try:
		programcards = JSON.ObjectFromURL(argsToURLString(APIURL=PROGRAMCARD_URL, args=kwargs))
	except:
		raise Ex.MediaNotAvailable
	
	# strip programcards
	programcards = stripProgramCards(programcards)
	
	# run through all programcards
	for program in programcards:
		
		# get and add program VCO
		dir.add(getProgram(program))
		
	return dir

###################################################################################################

@route('/video/drnu/programviews/{title}/{type}')
def ProgramViews(title = NAME, type = '/', **kwargs):
	
	# create OC
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = title)
	
	# get programcards
	try:
		programcards= JSON.ObjectFromURL(argsToURLString(APIURL = PROGRAMVIEW_URL + type, args = kwargs))
	except:
		raise Ex.MediaNotAvailable
	
	# strip programcards
	programcards = stripProgramCards(programcards)
	
	# run through all programcards
	for program in programcards:
		
		# get and add program VCO
		dir.add(getProgram(program))
	
	return dir

###################################################################################################

@route('/video/drnu/bundleswithpublicasset/{title}/{groupby}/{kwargs}')
def bundles_with_public_asset(title = NAME, groupby = 'firstChar',  **kwargs):
	
	# create OC
	dir = ObjectContainer(view_group="List", title1 = NAME, title2 = title)
	
	#create url
	url = argsToURLString(APIURL = BUNDLESWITHPUBLICASSET_URL, args = kwargs)
	
	# add search query if any
#	if query: url += "&Title=$like('" + urllib.quote_plus(query) + "')"
	
	# set variables
	programcards = JSON.ObjectFromURL(url)
	
	 # group by first letter
	if groupby == 'firstChar':
		
		# set variables
		bucket = dict()
		letter = ''
		
		# run through all programs
		for program in programcards['Data']:
			
			if program.get('Assets'):
				# add program to letter bucket
				if program['Title'][0] not in bucket:
					bucket[program['Title'][0].upper()] = list()
				bucket[program['Title'][0].upper()].append(program)
		
		# add DO for each letter in bucket
		for firstChar in sorted(bucket.iterkeys()):
			dir.add(DirectoryObject(title = firstChar,
								summary 	= unicode(L('fistCharBucketTitle')) + firstChar,
								key 		= Callback(bundles_with_public_asset,
													title 		= NAME, 
													groupby 	= 'name',
													Title 		= "$like('" + firstChar +"'),$orderby('asc')",
													ChannelType = "'TV'", 
													limit 		= "$eq(0)"))
								)
	 
	 # group by name
	else:
		
		# strip programcards
		programcards = stripProgramCards(programcards)
		
		# run through all programs
		for program in programcards:
			
			# get variables
			title 		= program.get('Title')
			punchline	= program.get('Subtitle')
			year		= program.get('ProductionYear')
			description = program.get('Description')
			slug		= program.get('Slug')
			thumb		= program.get('Thumb',R(ICON))
			    	
			# create DO and add to OC
			dir.add(DirectoryObject(
								title	= title,
								summary = description,
								thumb 	= thumb,
								key 	= Callback(ProgramCard,
												title1 		= NAME,
												title2 		= title,
												Relations_Slug = "'%s'" % slug,
												Assets_Kind	="'VideoResource'",
												Relations_BundleType="'Series'"
												)))
			
	return dir

###################################################################################################

def argsToURLString(APIURL, args):
	
	# set varaible
	url = APIURL;
	
	# only add args if there are any
	if len(args)>0:
		url += '?'
		for urlArgs in args:
			try:
				arg = urlArgs.replace('_','.')
				val = args[urlArgs].replace(' ','_')
			except:
				pass
			url += arg + '=' + val + '&'
		url = url.rstrip('&')
		
	return url

###################################################################################################

def getProgram(program):
	
	# set variables
	title 		= program.get('Title')
	punchline	= program.get('Subtitle')
	year		= program.get('ProductionYear')
	date		= Datetime.ParseDate(program.get('FirstBroadcastStartTime'))
	description = program.get('Description')
	slug		= program.get('Slug')
	serie_slug	= program.get('Serie_Slug','plex')
	duration	= program.get('Duration')
	thumb		= program.get('Thumb',R(ICON))
	studio		= "Danmarks Radio"
	
	# return vco
	return VideoClipObject(
				title 		= title,
				tagline 	= punchline,
				summary 	= description,
				originally_available_at = date,
				duration	= duration,
				studio		= studio,
				thumb 		= thumb,
				url 		= "http://www.dr.dk/TV/se/%s/%s" % (serie_slug, slug))

###################################################################################################

def stripProgramCards(programcards, order=True):
	
#	# get globals
#	global SERIERULES
	
	# set variables
	checkList 	= ['Title', 'Description']
	serierules 	= JSON.ObjectFromURL('http://www.dr.dk/mu/configuration/SeriesRules')['Data'][0]['Rules']
		
	try:
		
		# strip 'Data' if exists
		if programcards.get('Data'):
			programcards = programcards['Data']
		
		# run through all programcards
		for programcard in programcards:
		
			# set variables
			hasMedia = False
			programcard['Duration'] = 0
			
			# if programcard indside
			if programcard.get('ProgramCard'):
				
				# find assets
				if programcard.get('ProgramCard').get('Assets'):
					programcard['Assets'] = programcard.get('ProgramCard').get('Assets')
				
				# find broadcasts
				if programcard.get('ProgramCard').get('Broadcasts'):
					programcard['Broadcasts'] = programcard.get('ProgramCard').get('Broadcasts')
			
				# find broadcasts
				if programcard.get('ProgramCard').get('Relations'):
					programcard['Relations'] = programcard.get('ProgramCard').get('Relations')
			
			# find slug
			if not programcard.get('Slug') and programcard.get('ProgramCard'):
				if programcard.get('ProgramCard').get('Slug'):
					programcard['Slug'] = programcard.get('ProgramCard').get('Slug')
			
			# run through program if media available	
			if programcard.get('Assets'):
				
				# run through assets
				for asset in programcard.get('Assets', dict()):
	
					# if asset.get('Kind') == 'VideoResource' and asset.get('Uri') and asset.get('RestrictedToDenmark') is True:
					#	raise Ex.MediaGeoblocked
	
					# check if program has media
					if asset.get('Kind') == 'VideoResource' and asset.get('Uri'):
						hasMedia = True
						if asset.get('DurationInMilliseconds'):
							programcard['Duration'] = asset.get('DurationInMilliseconds')
						
					# check if program has image
					if asset.get('Kind') == 'Image' and asset.get('Uri'):
						programcard['Thumb'] = asset['Uri'] + '?width=512&height=512'
						break
					
				# set hasMedia		
				programcard['hasMedia'] = hasMedia
				
			# run through program if Relations available	
			if programcard.get('Relations'):
				
				# run through each broadcast
				for relation in programcard.get('Relations', dict()):
					if relation.get('BundleType') == 'Series':
						programcard['Serie_Slug'] = relation.get('Slug')
				
			# run through program if broadcasts available	
			if programcard.get('Broadcasts'):
				
				# run through each broadcast
				for broadcast in programcard.get('Broadcasts', dict()):
					
					# if broadcast['IsRerun']: del broadcast
					
					# check must have variables
					for checkPar in checkList:
						
						# if not found in programcard, try get it from broadcast json
						if programcard.get(checkPar) is None or programcard.get(checkPar) == "" :
							programcard[checkPar] = broadcast.get(checkPar)
					
					# find first start date in broadcast - assume its first run
					if 'FirstBroadcastStartTime' not in programcard:
					
						if 'AnnouncedStartTime' not in programcard:
							programcard['AnnouncedStartTime'] = broadcast.get('AnnouncedStartTime', '0001-01-01T00:00:00Z')
						else:
							programTime = Datetime.ParseDate(programcard['AnnouncedStartTime'])
							broadcastTime = Datetime.ParseDate(broadcast.get('AnnouncedStartTime', '0001-01-01T00:00:00Z'))
							if broadcastTime>programTime:
								programcard['AnnouncedStartTime'] = broadcast.get('AnnouncedStartTime', '0001-01-01T00:00:00Z')
						
						# set first broadcast start / end
						if programcard.get('AnnouncedStartTime'):
							programcard['FirstBroadcastStartTime'] = programcard.get('AnnouncedStartTime')
						
					# find first end date in broadcast - assume its first run
					if 'FirstBroadcastEndTime' not in programcard:
						
						if 'AnnouncedEndTime' not in programcard:
							programcard['AnnouncedEndTime'] = broadcast.get('AnnouncedEndTime', '0001-01-01T00:00:00Z')
						else:
							programTime = Datetime.ParseDate(programcard['AnnouncedEndTime'])
							broadcastTime = Datetime.ParseDate(broadcast.get('AnnouncedEndTime', '0001-01-01T00:00:00Z'))
							if broadcastTime>programTime:
								programcard['AnnouncedEndTime'] = broadcast.get('AnnouncedEndTime', '0001-01-01T00:00:00Z')
					
						
						# set first broadcast start / end
						if programcard.get('AnnouncedEndTime'):
							programcard['FirstBroadcastEndTime'] = programcard.get('AnnouncedEndTime')
					
				# set title
				for rules in serierules:
					if re.search(rules['RegEx'], programcard['Title']):
						if programcard.get('PrimaryChannel') in rules.get('Channels', dict()) or 'ReplaceEx' in rules:
							programcard['Title'] = re.sub(rules['RegEx'], rules['ReplaceEx'], programcard['Title'], 1)
						programcard['Title'] = programcard['Title'] + Datetime.ParseDate(programcard['AnnouncedStartTime']).strftime(' (%d-%m-%y)')
						break
					
				# remove broadcasts
				del programcard['Broadcasts']
			
	except Ex.MediaNotAvailable:
		pass
	except Ex.MediaGeoblocked:
		pass
	
	# order programcards by "orderby"
	if order:
		programcards = sorted(programcards, key=lambda item: item.get('Title'))
	
	# remove bad slugs
		
	return programcards

###################################################################################################

def stripBundle(bundle):
	
	return bundle

###################################################################################################

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
		JSONobjTracks = JSON.ObjectFromURL(RADIO_TRACKS_URL % channelId, cacheTime=30)
		if JSONobjTracks['tracks']:
			pre1 = "\n\n%s: " % unicode(L('latestTitle'))
			for track in JSONobjTracks['tracks']:
				if track['displayArtist']:
					trackop = trackop + pre1 + track['displayArtist']
				if track['title']:
					trackop = trackop + "\n" + track['title'] + "\n\n"
				pre1 = "%s: " % unicode(L('previous'))
	except:pass			
					
	strNowNext = title_now + description_now + start_now + stop_now + title_next + description_next + start_next + stop_next + trackop
		
	return strNowNext

###################################################################################################

def getTVLiveMetadata(slug):
	nowNext = JSON.ObjectFromURL('http://www.dr.dk/TV/live/info/%s/json' % slug)
	description = ""
	# now
	if 'Now' in nowNext:	
		description += '%s:' % unicode(L('now'))
		if 'Title' in nowNext['Now']:
			description += ' ' + nowNext['Now']['Title']
	#===========================================================================
	#	if 'StartTimestamp' in nowNext['Now']:
	#		
	#		description += ' (' + datetime.datetime.fromtimestamp(nowNext['Now']['StartTimestamp']/1000).strftime('%H:%M')
	#	if 'EndTimestamp' in nowNext['Now']:
	#		description += ' - ' + datetime.datetime.fromtimestamp(nowNext['Now']['EndTimestamp']/1000).strftime('%H:%M')+')'
	#	else:
	#		description += ')'
	# 
	#	if 'Description' in nowNext['Now']:
	#===========================================================================
			description += '\n' + String.StripTags(nowNext['Now']['Description'])
	else:
		description += unicode(L('noBroadcast'))
	
	# next
	if 'Next' in nowNext:
		description+= u'\n\n%s:' % unicode( unicode(L('next')))
		if 'Title' in nowNext['Next']:
			description += ' ' + nowNext['Next']['Title']
	#===========================================================================
	#	if 'StartTimestamp' in nowNext['Next']:
	#		
	#		description += ' (' + datetime.datetime.fromtimestamp(nowNext['Next']['StartTimestamp']/1000).strftime('%H:%M')
	#	if 'EndTimestamp' in nowNext['Next']:
	#		description += ' - ' + datetime.datetime.fromtimestamp(nowNext['Next']['EndTimestamp']/1000).strftime('%H:%M')+')'
	#	else:
	#		description += ')'
	# 
	#===========================================================================
		if 'Description' in nowNext['Next']:
			description += '\n' + String.StripTags(nowNext['Next']['Description'])
	
	return description

###################################################################################################
