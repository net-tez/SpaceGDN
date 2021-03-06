import os, yggdrasil, sys
from interfaces import *
from gdn import app
from gdn.models import Version, Build

_path = os.path.dirname(os.path.realpath(__file__))

def loadSources():

	import glob, json

	files = glob.glob(_path + '/../sources/*.json')
	output = []

	for f in files:
		with open(f) as handle:
			output.append(json.load(handle))

	return output

def getLastBuild(channel_id):
	return Version.query\
		.filter(Version.channel_id == channel_id)\
		.join(Build, Build.version_id == Version.id)\
		.add_columns(Build.build)\
		.order_by(Build.build.desc())\
		.first()

def getAndMake(filters, model, data, ignore = []):
	item = connection.session.query(model).filter_by(**filters).first()
	if not item:
		item = model(**data)
		session.add(item)
	else:
		for key, value in data.iteritems():
			if not key in ignore:
				setattr(item, key, value)
	return item

def getLoader(name):
	if not 'loader_' + name in globals():
		app.logger.warning('Interface not found, "%s"' % name)
		return False

	return globals()['loader_' + name]()

def load():
	sources = loadSources()

	adder = yggdrasil.Yggdrasil()

	for source in sources:

		jar_obj = adder.addJar(source)

		for channel_data in source['channels']:
			channel = adder.addChannel(channel_data, jar_obj)
			l = getLoader(channel_data['interface'])

			sys.stdout.write("\n\nLoading builds for %s" % (source['name'] + '#' + channel_data['name']))

			if not l: continue;

			data = getLastBuild(channel)
			last_build = 0
			if data:
				last_build = data.build

			for build in l.load(channel_data, last_build):
				adder.addBuild(build, channel)

	adder.commit()
	sys.stdout.write("\n\n")