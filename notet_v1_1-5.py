import eel
from tkinter import Tk # for minimizing the useless window
from tkinter.filedialog import askopenfilenames # for importing source(s)
from tkinter.filedialog import askdirectory # for importing project
import os, sys
from glob import glob
import compress_pickle
import base64
from zipfile import ZipFile, ZIP_LZMA
import shutil
import importlib

from pdf_annotate import PdfAnnotator, Appearance, Location
import time

NOTET_VERSION = '1.0.0'

welcomeData = None

sNn = {'sourcesList':[{'Name':None, 'Files':None, 'Refs':None}], 'nodeList':[]}
currentProjectName = None
activeNodes = []
currentTabList = []
selectedSourceName = None
currentTabName = None


DIR_DEFAULT = os.getcwd()
DIR_PROJECTSFOLDER = DIR_DEFAULT +'/notet_projects'
DIR_PROJECT = None
DIR_SOURCES = None

try: os.mkdir(DIR_PROJECTSFOLDER)
except: pass

# os.chdir(DIR_PROJECTSFOLDER) # Maybe I can use it for save state for opened project 

# try: 
# 	with open('pn', 'rb') as fh: projectNames = compress_pickle.load(fh, compression='lzma')
# except:
# 	projectNames = []
# 	with open('pn', 'wb') as fh: compress_pickle.dump(projectNames, fh, compression='lzma')

# os.chdir(DIR_DEFAULT)

@eel.expose
def LoadWelcome():
	welcomeB64 = base64.b64encode(welcomeData).decode('utf-8')
	eel.LoadWelcome(welcomeB64)


def isPFvalid(pfPath):
	folderName = pfPath[pfPath.rfind('/')+1:]

	os.chdir(pfPath)
	print('BEACON sonucu: ', glob('.beacon'))	
	if any(glob('.beacon')): # Invisible validator
		with open('.beacon', 'rb') as fh: beaconContent = compress_pickle.load(fh, compression='lzma')
		if(beaconContent['version'] == NOTET_VERSION): # chosen project's version is important to compatibility so if project passes this stage it can be imported
			return {'isValid':True, 'reason':'compatible_beacon_file'}

		else: # Not compatible version
			return {'isValid':False, 'reason':f'{folderName} is not compatible with this version of notet\nPlease choose a valid project folder'}

	else: # Has no beacon file even
		print('NO BEACON')
		return {'isValid':False, 'reason':f'{folderName} is not a valid project folder\nPlease choose a valid project folder'}


@eel.expose
def importProject():
	root = Tk() 
	root.geometry('0x0')

	folderPath = askdirectory(initialdir = DIR_DEFAULT, 
									title = "Select project folder") 
	
	print(folderPath)
	if folderPath == () or folderPath == '':
		# root.mainloop()
		root.destroy()
		return
	root.destroy()
	folderName = folderPath[folderPath.rfind('/')+1:]
	print(folderPath)
	print(folderName)

	os.chdir(DIR_PROJECTSFOLDER)
	if folderName in next(os.walk('.'))[1]: # If there is a project with the same name already
		eel.confirm_importWithOverwrite(f'There is a project named {folderName}.\nDo you want to overwrite?', folderPath)

	else:
		res = isPFvalid(folderPath)
		if res['isValid']:
			shutil.copytree(folderPath, DIR_PROJECTSFOLDER+'/'+folderName) ## THIS is THE IMPORTING process
			setOpenedProject_PY_START(folderName)

		else:
			eel.alert_JS(res['reason'])
			importProject()


@eel.expose
def importWithOverwrite(folderPath): ## beacon validation will be done again after confirming overwrite
	folderName = folderPath[folderPath.rfind('/')+1:]
	
	res = isPFvalid(folderPath)
	if res['isValid']:
		os.chdir(DIR_PROJECTSFOLDER)
		shutil.rmtree(folderName) # First phase of overwrite: Removing same named old  project folder
		
		shutil.copytree(folderPath, folderName) # Phase two: Copying new project folder to projects folder
		setOpenedProject_PY_START(folderName)

	else:
		eel.alert_JS(res['reason'])
		importProject()


@eel.expose
def setOpenedProject_PY_START(projectName):
	global currentProjectName
	global DIR_PROJECT
	global DIR_SOURCES

	# Opening the project
	""" Opening a project is actually setting all global variables towards to chosen project"""


	currentProjectName = projectName
	DIR_PROJECT = DIR_PROJECTSFOLDER + '/' + currentProjectName
	DIR_SOURCES = DIR_PROJECT + '/src' 

	try: os.mkdir(DIR_SOURCES)
	except: pass

	eel.setOpenedProject_JS_END(currentProjectName)



@eel.expose
def createProject(projectName):
	os.chdir(DIR_PROJECTSFOLDER)

	try:
		os.mkdir(projectName)
		os.chdir(projectName)
		with open('.beacon', 'wb') as fh: compress_pickle.dump({'version':'1.0.0'}, fh, compression='lzma') # Compatibility is being decided here!
		setOpenedProject_PY_START(projectName)

	except:
		eel.confirm_createWithOverwrite(f'There is a project named {projectName}.\nDo you want to overwrite?', projectName)

@eel.expose
def createWithOverwrite(projectName):
	os.chdir(DIR_PROJECTSFOLDER)
	shutil.rmtree(projectName)
	os.mkdir(projectName)
	os.chdir(projectName)
	with open('.beacon', 'wb') as fh: compress_pickle.dump({'version':'1.0.0'}) # Compatibility is being decided here!
	setOpenedProject_PY_START(projectName)


@eel.expose
def setAvailableProjects_PY_START():
	os.chdir(DIR_PROJECTSFOLDER)
	ps = next(os.walk('.'))[1]
	if any(ps):
		avps = []
		if currentProjectName != None:
			avps.append(currentProjectName) ## Therefore we appending the current project to first element to avps, it is important in JS
			ps.remove(currentProjectName) ## Preventing displaying currrent project name twice in the list 

		avps.extend(ps) ## Extending avps with whatever is remained on ps 
		eel.setAvailableProjects_JS_END(avps)


# @eel.expose
# def unpackProject(projectMeta):
# 	# projectData = {'name':name1, 'isImport':bool}
# 	global currentProjectName
# 	global DIR_PROJECT
# 	global DIR_SOURCES

# 	if currentProjectName != None: ## We need to pack project if there is an opened one
# 		packProject(currentProjectName)

# 	if projectMeta['isImport']:
# 		projectPackPath = projectMeta['name']
# 		projectPackName = projectPackPath[projectPackPath.rfind('/')+1:]

# 		with open(projectPackPath, 'rb') as fh: projectPackData = compress_pickle.load(fh, compression='lzma')
# 		os.chdir(DIR_PROJECTSFOLDER)

# 	else:
# 		projectPackName = projectMeta['name']
# 		os.chdir(DIR_PROJECTSFOLDER)
# 		with open(projectPackName, 'rb') as fh: projectPackData = compress_pickle.load(fh, compression='lzma')


# 	# opening project

# 	projectName = projectPackName[:projectPackName.find('.')]

# 	currentProjectName = projectName
# 	DIR_PROJECT = DIR_PROJECTSFOLDER + '/' + currentProjectName
# 	DIR_SOURCES = DIR_PROJECT + '/src' 

# 	try: os.mkdir(DIR_PROJECT)
# 	except: pass

# 	try: os.mkdir(DIR_SOURCES)
# 	except: pass


# 	## pwd = DIR_PROJECTSFOLDER
# 	# Real unpacking operation

# 	with open(projectPackName, 'wb') as fh: fh.write(projectPackData)

# 	with ZipFile(projectPackName, 'r') as z:

# 		for name in z.namelist():
# 			ind = name.rfind('/')+1
# 			fileName = name[ind:]
# 			if fileName == "sNn":
# 				os.chdir(DIR_PROJECT)
# 				sNn_file = z.read(name)
# 				with open(fileName, 'wb') as fh: fh.write(sNn_file)
# 			else: # It's a source
# 				os.chdir(DIR_SOURCES)
# 				source_file = z.read(name)
# 				with open(fileName, 'wb') as fh: fh.write(source_file)


# 	os.chdir(DIR_PROJECTSFOLDER)
# 	os.remove(projectPackName)

# 	eel.setOpenedProject(currentProjectName)


@eel.expose
def delProject(pname):
	os.chdir(DIR_PROJECTSFOLDER)

	ps = next(os.walk('.'))[1]

	if pname in ps:
		shutil.rmtree(pname)
		eel.reset2NullProject()

	else: # This is imposiible right now because the opened project is not listed in open project list
		print('FATAL ERROR, FILE CONFUSION')


def get_sNn():
	os.chdir(DIR_PROJECT)

	global sNn
	sNn = {'sourcesList':[{'Name':None, 'Nodes':None, 'Refs':None}], 'nodeList':[]}

	try: 
		with open('sNn', 'rb') as fh: sNn = compress_pickle.load(fh, compression='lzma')
	except: 
		with open('sNn', 'wb') as fh: compress_pickle.dump(sNn, fh, compression = 'lzma')




@eel.expose
def updateLocalSourcesList():
	os.chdir(DIR_PROJECT)
	if(sNn['sourcesList'][0]['Name'] == None):
		sNn['sourcesList'].remove({'Name':None, 'Nodes':None, 'Refs':None}) ## If there is no source in database

	with open('sNn', 'wb') as fh: compress_pickle.dump(sNn, fh, compression='lzma')
	


@eel.expose
def updateLocalNodeList(newNodeList):
	os.chdir(DIR_PROJECT)

	global sNn
	sNn['nodeList'] = []

	for n in newNodeList:
		if n['data'] != {}:
			sNn['nodeList'].append({'id':n['id'], 'text':n['text'], 'data':n['data'], 'state':n['state'], 'parent':n['parent']}) # purifying the unordered list for storing
		else:	
			sNn['nodeList'].append({'id':n['id'], 'text':n['text'], 'data':{'rawRefs':[], 'htmlRefs':""}, 'state':n['state'], 'parent':n['parent']}) # purifying the unordered list for storing
	with open('sNn', 'wb') as fh: compress_pickle.dump(sNn, fh, compression='lzma')
	## You need to add "save state" like function for continuity 



@eel.expose
def displaySources_PY():
	setActiveNodes_PY([]) # Precaution to blindfolded coding

	get_sNn()
	# return sNn['sourcesList'] ## Do not use return because toughness of JS about this subject, so we CHEAT ! :)
	eel.displaySources_JS(sNn['sourcesList'])

@eel.expose
def displayNodeTree_PY():
	get_sNn()
	# return str(sNn['nodeList']) ## Do not use return because toughness of JS about this subject, so we CHEAT ! :)
	eel.displayNodeTree_JS(sNn['nodeList'])


@eel.expose
def setActiveNodes_PY(nodes):
	global activeNodes
	activeNodes = []

	activeNodes_JS = {}

	for n in nodes:
		if(n['state']['selected']):
			activeNodes.append(n['id'])
			activeNodes_JS[n['id']] = n['text']

	eel.setActiveNodes_JS(activeNodes_JS)
	print(activeNodes)


def setCurrentTabName(cs):
	global currentTabName
	if(cs != ""):
		currentTabName = cs # For getting only node name but parent name
		print('Current tab name is:', currentTabName)

@eel.expose
def setSelectedSourceName(rowHTML):
	
	if(rowHTML != ""):
		global selectedSourceName
			
		s = rowHTML.find('>')+1 # real world try/except 
		e = rowHTML[s:].find('<')+4 # real world try/except 
		selectedSourceName = rowHTML[s:e]

		print('selected source name is:', selectedSourceName)

	else:
		pass


@eel.expose
def openSourceFile(rowHTML):
	s = rowHTML.find('>')+1 # real world try/except 
	e = rowHTML[s:].find('<')+4 # real world try/except 
	fileName = rowHTML[s:e]

	if fileName not in currentTabList: 
		eel.addNewTab(fileName)
		currentTabList.append(fileName)

@eel.expose
def delSource():
	get_sNn()
	global sNn

	for i in range(len(sNn['sourcesList'])):
		if sNn['sourcesList'][i]['Name'] == selectedSourceName:
			del sNn['sourcesList'][i] 
			break

	updateLocalSourcesList() 

	os.chdir(DIR_SOURCES)
	os.remove(selectedSourceName)
	os.chdir(DIR_DEFAULT)
	

# @eel.expose
# def exportNode():
# 	get_sNn()

# 	for nodeID in activeNodes:
# 		for n in sNn['nodeList']:
# 			if nodeID == n['id']:
# 				htmlContent = n['data']['htmlRefs']
# 				with open('cnt.html', 'w') as fh: fh.write(htmlContent)


def generateNodeHTML(nodeID, rawRefs): # !! For only one node !! #
	# rawRefs = [{'sourceName':sourceName1 'pageNum':pageNum1, 'citationText':citationText1, 'coords':coords1}]

	allDivs = ""
	i = 0


	for refID in range(len(rawRefs)):
		aDiv = f'<div id="{nodeID}_{refID}">\
					<button class="refButton" style="background: transparent; border: none !important; font-size:15; color:DodgerBlue; width:49%;">\
					S:{rawRefs[refID]["sourceName"]} P:{rawRefs[refID]["pageNum"]}</button><!--\
					--><button class="refCopy" style="width:17%;">Copy</button><!--\
					--><button class="refMove" style="width:17%;">Move</button><!--\
					--><button class="refDel" style="width:17%;">Delete</button>\
					<p>{rawRefs[refID]["citationText"]}</p>\
					<hr></div>'
		allDivs += aDiv
		i+=1


	srcdoc = f'<html><body>{allDivs}</body></html>'

	return srcdoc


def highlightPDF(pdfName, coordsData):
	os.chdir(DIR_SOURCES)

	annotator = PdfAnnotator(pdfName)

	for page in coordsData:
		for c in coordsData[page]:
			annotator.add_annotation(
				'square',
				location=Location(x1=c[0], y1=c[1], x2=c[2], y2=c[3], page=page),
				appearance=Appearance(fill=(1, 0, 0, 0.3))
						)
	annotator.write('hl.pdf')

@eel.expose
def goToRefPDF(refData, nodeIframeID):
	# nodeIframeID will be modified, shrunk for refIframe

	get_sNn()

	nodeID = refData[:refData.rfind('_')]
	refID = int(refData[refData.rfind('_')+1:])

	coordsData = {}

	for i in range(len(sNn['nodeList'])):
		if sNn['nodeList'][i]['id'] == nodeID:
			pageNum = sNn['nodeList'][i]['data']['rawRefs'][refID]['pageNum']
			sourceName = sNn['nodeList'][i]['data']['rawRefs'][refID]['sourceName']

			# rawRefs = [{'sourceName':sourceName1 'pageNum':pageNum1, 'citationText':citationText1, 'coords':coords1}]
			for ref in sNn['nodeList'][i]['data']['rawRefs']:
				if ref['sourceName'] == sourceName:
					if ref['pageNum']-1 in coordsData:
						for c in ref['coords']:
							coordsData[ref['pageNum']-1].append(c)

					else:
						coordsData[ref['pageNum']-1] = ref['coords']
			break # for optimization

	highlightPDF(sourceName, coordsData)
	time.sleep(2)
	base64Data = getPDFdata('hl.pdf') # Added on 20201030T215934TZ0300

	eel.openRefPDF(nodeIframeID, base64Data, pageNum)


@eel.expose
def copyORmoveRef(refData, targetNodes, oprName):
	get_sNn()
	
	nodeID = refData[:refData.rfind('_')]
	refID = int(refData[refData.rfind('_')+1:])

	theRef = None

	for i in range(len(sNn['nodeList'])):
		if sNn['nodeList'][i]['id'] == nodeID:
			theRef = sNn['nodeList'][i]['data']['rawRefs'][refID] ## Getting the ref itself

			if(oprName == 'm'): # for moving operation
				print(refID)
				print(type(refID))
				del sNn['nodeList'][i]['data']['rawRefs'][refID]

			for nodeID in targetNodes:
				for j in range(len(sNn['nodeList'])):
					if sNn['nodeList'][j]['id'] == nodeID:
						sNn['nodeList'][j]['data']['rawRefs'].append(theRef) ## Appended but not sorted

						sNn['nodeList'][j]['data']['rawRefs'].sort(key= lambda x: (x.get('sourceName'), x.get('pageNum'))) # sorted but html is not generated

						sNn['nodeList'][j]['data']['htmlRefs'] = generateNodeHTML(nodeID, sNn['nodeList'][j]['data']['rawRefs']) # appended, sorted, html generated

						break	

			break

	updateLocalNodeList(sNn['nodeList'])



@eel.expose
def delRef(refData):
	get_sNn()

	nodeID = refData[:refData.rfind('_')]
	refID = int(refData[refData.rfind('_')+1:])

	for i in range(len(sNn['nodeList'])):
		if sNn['nodeList'][i]['id'] == nodeID:
			sNn['nodeList'][i]['data']['rawRefs'].pop(refID)

			sNn['nodeList'][i]['data']['htmlRefs'] = generateNodeHTML(nodeID, sNn['nodeList'][i]['data']['rawRefs'])
			break

	updateLocalNodeList(sNn['nodeList'])


@eel.expose
def generateNodeView(nodeID):
	get_sNn()

	nodeName = ""
	nodeList = sNn['nodeList']

	for node in nodeList:
		if node['id'] == nodeID:
			if node['data'] != {'rawRefs':[], 'htmlRefs':""} and node['data'] != {}:
				nodeName = node['text']
	
			else:
				pass

			break

	if(nodeName != ""):

		if nodeName+'.html' not in currentTabList: 
			eel.addNewTab(nodeName+'.html')# updated node pdf's will not be displayed, you need to figure out how to update them
			currentTabList.append(nodeName+'.html')

	else:
		pass


def getPDFdata(pdfName):
	os.chdir(DIR_SOURCES)
	with open(pdfName, 'rb') as fh: pdfData = fh.read()

	base64Data = base64.b64encode(pdfData).decode('utf-8')

	if(pdfName == 'hl.pdf'):
		os.remove(pdfName)
	return base64Data


@eel.expose
def tabActivated(containerName, rawHTML):
	get_sNn()
	fileName = rawHTML[:rawHTML.find('<')]

	if fileName[-4:] == '.pdf': # If it is a source file
		setCurrentTabName(fileName)
		base64Data = getPDFdata(fileName)

		eel.LoadPdfDocument(fileName[:-4]+'PDF', containerName, base64Data)

	elif fileName[-5:] == '.html': # if it is a node file
		setCurrentTabName(fileName)
		for i in sNn['nodeList']:
			if i['text'] == fileName[:-5]:
				newID = fileName[:-5].replace(' ', '_')+'_HTML'
				eel.LoadNodeFile(newID, containerName, i['data']['htmlRefs'])



@eel.expose
def willBeClosed(rawHTML):
	global currentTabList

	pdfName = rawHTML[:rawHTML.find('<')]
	currentTabList.remove(pdfName)


@eel.expose
def importSource():
	global sNn
	root = Tk() 
	root.geometry('0x0') # I can't destroy the little window so I made it invisible

	fPaths = askopenfilenames(initialdir = DIR_DEFAULT, 
								title = "Select Files", 
								filetypes = (("PDF file", 
												"*.pdf*"), 
											("all files", 
												"*.*"))) 

	if fPaths==() or fPaths =='':
		root.destroy()
		return
	root.destroy()

	for p in fPaths:
		sourceName = p[p.rfind('/')+1:]
		with open(p, 'rb') as fh: sourceData = fh.read()

		newSource = {'Name':sourceName, 'Nodes':0, 'Refs':0}
		sNn['sourcesList'].append(newSource)

		os.chdir(DIR_SOURCES)

		with open(sourceName, 'wb') as fh: fh.write(sourceData)

	updateLocalSourcesList()


# @eel.expose
# def addFile2Sources(fileName, data):
# 	global sNn
# 	newFile = {'Name':fileName, 'Nodes':0, 'Refs':0}
# 	sNn['sourcesList'].append(newFile) ## new sources list

# 	os.chdir(DIR_SOURCES)
# 	s = data.find(',')
# 	data = data[s:]
# 	data = base64.b64decode(data)
# 	with open(fileName, 'wb') as h: h.write(data)

# 	updateLocalSourcesList()


@eel.expose
def checkActiveNodes():
	if any(activeNodes):
		eel.code2node_JS_START()

@eel.expose
def code2node_PY_END(data):
	get_sNn()
	if any(activeNodes):
		for activeNode in activeNodes:
			for nodeIdx in range(len(sNn['nodeList'])):
				if sNn['nodeList'][nodeIdx]['id'] == activeNode:
					## First things first, coding to the rawRefs in sNn['nodeList'][nodeIdx]['data']
					# rawRefs = [{'sourceName':sourceName1 'pageNum':pageNum1, 'citationText':citationText1, 'coords':coords1}]
					 
					# csl = [csl[c] for c in range(len(csl)) if c == 0 or c==len(csl)-1 or c%2 != 0] ## Simplification-Purification of raw selection co-ordinates | by nbsas - 20201030T233437TZ0300 ## Commented out on 20201101T184135TZ0300 for javascript equivalent in viewer.html
					sNn['nodeList'][nodeIdx]['data']['rawRefs'].append({'sourceName': currentTabName,
																		'pageNum': data['highlightCoordsData']['page']+1, 
																		'citationText': data['citation'],
																		'coords': data['highlightCoordsData']['coords']})
				
					sNn['nodeList'][nodeIdx]['data']['rawRefs'].sort(key= lambda x: (x.get('sourceName'), x.get('pageNum')))

					## At second phase, coding to the htmlRefs in sNn['nodeList'][nodeIdx]['data']
					sNn['nodeList'][nodeIdx]['data']['htmlRefs'] = generateNodeHTML(sNn['nodeList'][nodeIdx]['id'], sNn['nodeList'][nodeIdx]['data']['rawRefs'])
					break

		updateLocalNodeList(sNn['nodeList'])



@eel.expose
def printOutPy(p):
	print(p)




eel.init("guiDEV")

eel.start("index_v1_1-5.html", size=(1360,768))

# os.chdir(DIR_PROJECTSFOLDER)
