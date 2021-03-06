# BL CR Parser 
#Date: 08/08/2016
#updated: 09/22/2016  
# Added feature like finding log file from buildID
# and modified date validation code

import os
import subprocess as sp
from sys import argv
import datetime
import re
import time

class Build(object):
	def __init__(self,build):
		self.cmd = "findbuild "+build+" -lo"
	def command(self):
		FP = open("findbuild.txt", 'w')
		process = sp.Popen(self.cmd,shell=False,stderr=sp.STDOUT,stdout=sp.PIPE)
		Data = process.stdout.read(1)
		while Data:
			FP.write(Data)
			Data = process.stdout.read(1)
		FP.close()
class BLCR(object):
	def __init__(self):
		self.Build = ""
		self.List = []
		self.Blocking_list = ["MandatoryBlocking", "TechMandatory", "SecurityCritical", "SecurityBlocking", "StabilityBlocking", "PerformanceBlocking", "GeneralBlocking"]
		self.Pl_Threshold = ""
		self.Pl_Name = ""
		self.CR_Threshold = {}
		self.CR_Date = {}
		self.CR_Subsystem = {}
		self.Final_CR_Threshold = {}
		self.Final_CR_Date = {}
		self.Msg = "Usage : python BLCR_Parser.py BuildID today \n\tDate format: YYYY-MM-DD"
		
	def Get_Build_Path(self):
		FP = open("findbuild.txt", 'r')
		for line in FP:
			words = line.split()
			for word in words:
				if "Location:" == word:
					Build_Path = words[1]
					break
		FP.close()
		self.Build = Build_Path
	
	def Remove_text(self):
		os.remove("findbuild.txt")
	
	def File_Read(self,file):
		try:
			fp = open(file, "r") # opeing verifysrc file for reading
		except IOError:
			print "Can't find the file specified"
			quit()
		with open(file, "r") as FP:
			for line in FP.readline().split('\r'): # Reading line by line from file and storing into variable called line
				self.List.append(line) # appeding each to a List variable
		#print self.List
		FP.close()
		
	def Find_PLName(self): # This method is to read PL Name from List
		for line in self.List:
			if line.find("Product Line is") !=-1:
				self.Pl_Name = line.split()[4].strip('.')
		print "PL Name : " + self.Pl_Name
		
	def Find_PL_Threshold(self): # This method is to read PL threshold from List
		for line in self.List:
			if line.find("Threshold is") != -1:
				self.Pl_Threshold = line.split()[6].strip('.')
		print "PL Threshold is : " + self.Pl_Threshold
		self.Find_PLName()
	
	def Find_BLCR_Info(self,str): #This method is to get the whole CR info like CR, subsystem, date and threshold
		i = 0
		CR_Count = 0
		for line in self.List:
			i += 1
			if line.startswith(str) and line.find("Source Integrity Violations ") ==-1:
				#print line
				CR_Count += 1 # this count is inclusive of repetitions
				Line_List = line.split()
				#[word1 for word1,word2 in zip(Line_List,self.Blocking_list) if word1==word2]#comparing 2 lists and writing result into word1
				Common = list(set(Line_List) & set(self.Blocking_list))#comparing 2 lists and writing result into Common and is a list
				if "Set" in self.List[i-9].split() and "CR:" in self.List[i-9].split(): # finding set and cr: strings in list
					self.CR_Threshold[self.List[i-9].split()[2]] = Common[0] #Getting Threshold of CR and pairing with CR
					self.CR_Subsystem[self.List[i-9].split()[2]] = self.List[i-8].split()[6] #Getting Subsystem of CR and pairing with CR
					j=0
					for word in Line_List: #this loop is to get date
						j += 1
						if word == "date":
							self.CR_Date[self.List[i-9].split()[2]] = Line_List[j+1].strip('.')
		#print self.CR_Date	
		#print self.CR_Threshold
		#print self.CR_Subsystem
		#print "Total Hits: %d" % CR_Count
		
	def Required_Threshold_CRs(self): # finding CRs which are comes under threshold
		Pl_threshold_index = self.Blocking_list.index(self.Pl_Threshold)
		for key in self.CR_Threshold: # Here reading key valuas from dictionary
			if Pl_threshold_index >= self.Blocking_list.index(self.CR_Threshold[key]): 
				self.Final_CR_Threshold[key] = self.CR_Threshold[key]
		#print self.Final_CR_Threshold
	
	def Write_into_File(self,str):
		File_Name = self.Pl_Name +".txt"
		if str == "Error:" and len(self.Final_CR_Threshold) == 0:
			print "No CRs Found in Error...Quiting"
			quit()
		if str == "Warning:" and len(self.Final_CR_Date) == 0:
			print "No CRs Found in Warning...Quiting"
			quit()
		FP = open(File_Name,"w")
		#writing Data into text file in below format
		FP.write("{0:10}{1:20}{2:20}{3:20}".format("CR","Technology","Blocking Date","Threshold")+"\n")
		#This if and else condition is for, to store date based on error or warning
		if str == "Error:":
			for key in self.Final_CR_Threshold:
				FP.write("{0:10}{1:20}{2:20}{3:20}".format(key,self.CR_Subsystem[key],self.CR_Date[key],self.Final_CR_Threshold[key])+"\n")
		else:
			for key in self.Final_CR_Date:
				FP.write("{0:10}{1:20}{2:20}{3:20}".format(key,self.CR_Subsystem[key],self.Final_CR_Date[key],self.Final_CR_Threshold[key])+"\n")
		
		FP.close()
		
	def Required_CRs_Based_Date(self,date): #This method is for Date comparision
		Date_object = datetime.datetime.strptime(date,"%Y-%m-%d").date() # Here coverting string to datetime.date object
		for key in self.Final_CR_Threshold:
			Dir_date_object = datetime.datetime.strptime(self.CR_Date[key],"%Y-%m-%d").date()
			if Date_object.year > Dir_date_object.year:
				if Date_object.month >= Dir_date_object.month or Date_object.month < Dir_date_object.month:
					if Date_object.day >= Dir_date_object.day or Date_object.day < Dir_date_object.day:
						self.Final_CR_Date[key] = self.CR_Date[key]
			elif Date_object.year == Dir_date_object.year:
				if Date_object.month > Dir_date_object.month:
					if Date_object.day >= Dir_date_object.day or Date_object.day < Dir_date_object.day:
						self.Final_CR_Date[key] = self.CR_Date[key]
				elif Date_object.month == Dir_date_object.month:
					if Date_object.day >= Dir_date_object.day:
						self.Final_CR_Date[key] = self.CR_Date[key]
			else:
				pass		
		#print self.Final_CR_Date
	
	def Time_Delta(self,start,end):
		Delta_time = []
		Delta = end-start
		Delta_time.append(Delta/60)
		Delta_time.append(Delta%60)
		return Delta_time
		
	def Main(self):
		start_time = time.time()
		if len(argv) != 3: #This is to check Validating Inputs count
			print self.Print()
			print "\t*****Abroting*****"
			quit()
		Date = argv[2]
		#print Date
		
		Regex = re.compile(r'\d{4}\-') # Date validation
		if Regex.search(Date):
			Date_List = Date.split("-")
			if int(Date_List[1])<=12 and int(Date_List[2])<=31:
				print "Date ok"
			else:
				print "Month or Date is out of range...pls check"
				quit()
		elif  Date == "today":
			pass
		else:
			print "Please enter Date format as below..."
			print self.Print()
			quit()

		Build(argv[1]).command()
		self.Get_Build_Path()
		self.Remove_text()
		if self.Build:
			VerifySrcFile = self.Build + "\VerifySrc.log"
			#print VerifySrcFile
			
		self.File_Read(VerifySrcFile)
		self.Find_PL_Threshold()
		if Date == "today":
			#print "Error based CR info:"
			self.Find_BLCR_Info("Error:")
			self.Required_Threshold_CRs()
			self.Write_into_File("Error:")
		else:
			#print "Error based CR info:"
			self.Find_BLCR_Info("Error:")
			#print "\nWarning based CR info:"
			self.Find_BLCR_Info("Warning:")
			self.Required_Threshold_CRs()
			self.Required_CRs_Based_Date(Date)
			self.Write_into_File("Warning:")
		end_time = time.time()
		Time = self.Time_Delta(start_time,end_time)
		print "Elapsed time: %d mins %d secs" % (Time[0],Time[1])
	
	def Print(self):
		return self.Msg

#**********Main Block***********

if __name__ == "__main__":
	BLCR_obj = BLCR()
	BLCR_obj.Main()
	