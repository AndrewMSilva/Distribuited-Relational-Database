from threading import Lock
from Service import Service
import json

class GroupManager(Service):
	# Group settings
	_Group = []
	__GroupLock = Lock()
	# Message types
	_InviteMessage  = 'invite'
	_ExitMessage	= 'exit'
	# Configs settings
	_ConfigsDirectory = './Configs/'
	__GroupConfigs	   = 'Group.config'

	def _InitializeGroup(self):
		if not self.__GetGroup():
			self._Group = [self._IP]
			self.__SaveGroup()
	
	def __GetGroup(self):
		try:
			file = open(self._ConfigsDirectory+self.__GroupConfigs, 'r')
			group_json = file.read()
			file.close()
			self._Group = json.loads(group_json)
			if not self._IP in self._Group:
				print('Local IP not found in', self.__GroupConfigs)
				return False
			return True
		except:
			return False

	def __SaveGroup(self):
		try:
			file = open(self._ConfigsDirectory+self.__GroupConfigs, 'w')
			group_json = json.dumps(self._Group)
			file.write(group_json)
			file.close()
			return True
		except:
			return False
	
	def _SendMessage(self, ip, data, type, wait_result=False):
		enconded_message = self._EncodeMessage(data, type, True)
		s = self._NewSocket()
		s.settimeout(self._Timeout)
		result = True
		try:
			s.connect((ip, self._Port))
			s.send(enconded_message)
			if wait_result:
				result = self._Receive(s)
		except:
			result = False
		finally:
			s.close()
			return result
	
	def _GroupBroadcast(self, data, type):
		for ip in self._Group:
			if ip != self._IP:
				self._SendMessage(ip, data, type)

	def _Invite(self, ip):
		# Verifying the connection is itself
		if ip == self._IP:
			return 'Unable to connect to itself'
		# Verifying if the connection already exists
		if ip in self._Group:
			return 'Already connected'
		# Sending invitation
		result = self._SendMessage(ip, self._Group, self._InviteMessage)
		if result:
			return 'Invitation sent'
		else:
			return 'Unable to connect'

	def _UpdateGroup(self, message):
		# Using mutex to update group
		result = False
		self.__GroupLock.acquire()
		try:
			group = message['data']
			# Checking if the groups match
			if isinstance(group, list) and group != self._Group:
				# Creating a copy of the group before update it
				result = self._Group.copy()
				# Updateing group
				for ip in group:
					if not ip in self._Group:
						self._Group.append(ip)
				self._Group = sorted(self._Group)
				# Updating group
				self.__SaveGroup()
				print('Group updated')
				# Sending the new group to other devices
				self._GroupBroadcast(self._Group, self._InviteMessage)
			# Checking if the message is an exit message
			elif isinstance(group, str):
				self._Group.remove(group)
				# Updating group
				self.__SaveGroup()
				print('Group updated')
		except:
			result = False
		finally:
			self.__GroupLock.release()
			return result

	def _ExitGroup(self):
		result = False
		self.__GroupLock.acquire()
		try:
			old_group = self._Group.copy()
			self._Group = [self._IP]
			self.__SaveGroup()
			self._GroupBroadcast(self._IP, self._ExitMessage)
			result = old_group
		finally:
			self.__GroupLock.release()
			return result
		