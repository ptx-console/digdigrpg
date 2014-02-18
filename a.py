# -*- coding: utf-8 -*-
import json
import copy

def Input(msg):
	return raw_input(msg)

class Skill:
	def __init__(self):
		self.name = ""
		self.ident = ""
		self.desc = ""
		self.point = 10
		self.tick = 3
		self.count = 0
		self.targetSelf = True # True: self, False: enemy

	def SpawnBuf(self):
		buf = Buf()
		for key in self.__dict__:
			setattr(buf, key, self.__dict__[key])

		return buf

class Buf(Skill):
	def __init__(self):
		Skill.__init__(self)

class Char:
	def __init__(self):
		self.hp = 200
		self.maxhp = 200
		self.mp	= 200
		self.maxmp = 200
		self.skills = [Skill()]
		self.bufs = []
		self.target = None

		"""
		self.test = Skill()
		print self.test.__dict__
		testbuf = self.test.SpawnBuf()
		print testbuf.__dict__
		"""

class App:
	def __init__(self):
		self.char = Char()
		self.mobs = []
		self.Initialize()

	def Print(self, msg):
		print msg
	def Prompt(self, msg):
		return Input(msg)
	def ParseRegularCommand(self, args):
		cmd = copy.deepcopy(args)
		while cmd.find("  ") != -1:
			cmd = cmd.replace("  ", " ")

		cmds = cmd.split(" ")
		if cmds[0] == "quit":
			return False

		

	def Launch(self):
		while True:
			cmd = self.Prompt("""[%d/%d %d/%d] """ % (self.char.hp, self.char.maxhp, self.char.mp, self.char.maxmp))
			if self.ParseRegularCommand(cmd) == False:
				break

	def GenSaveFile(self, objects):
		obj = {
			"version": "alpha",
			"objects": objects
		}	
		return json.dumps(obj, sort_keys=True, indent=8, separators=(',', ': '))

	def Initialize(self):
		try:
			self.char.hp = 100
			self.char.maxhp = 100
			self.char.mp = 100
			self.char.maxmp = 100

			f = open("saveFile.txt", "rb")
			string = f.read()
			objects = json.loads(string)
			version = objects["version"]
			s = objects["objects"]
			char = s["char"]
			for name in char:
				setattr(self.char, name, char[name])
		except:
			self.char.hp = 50
			self.char.maxhp = 50
			self.char.mp = 50
			self.char.maxmp = 50

	def Finalize(self):
		"""
		print "\n\n\nFinalizing..."
		string = json.dumps({'4': 5, '6': [1,2,3,"asd"]}, sort_keys=True,
		                     indent=4, separators=(',', ': '))
		print string
		"""
		print "\n*****************\nSaving File\n****************"
		objects = {}
		objects["char"] = {"hp":self.char.hp, "maxhp":self.char.maxhp, "mp":self.char.mp, "maxmp":self.char.maxmp}
		string = self.GenSaveFile(objects)
		f = open("saveFile.txt", "w")
		f.write(string)
		f.close()

if __name__ == "__main__":
	app = App()
	try:
		app.Launch()
		app.Finalize()
	except:
		app.Finalize()
		raise
