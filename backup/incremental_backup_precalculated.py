##############################
# Simple script that performs an incremental, one-directional backup between two folders.
# File comparison is done by checking last update date and size of the file.
##############################

import os
import shutil
import time

########### GLOBAL ###########

rootSrc = "D:"
rootDst = "E:"
errorLogFile = "C:/BACKUP ERROR.txt"
backupLogName = "backup_log.txt"
backupLogFile = os.path.join(rootDst, backupLogName)

toAdd = []
toDelete = []

added = 0
deleted = 0
ignored = 0

processing = None
status = "FAILED"

startTime = time.time()

########### FUNC ###########

def getElapsedTime():
	global startTime
	return time.strftime("%H:%M:%S", time.gmtime(time.time() - startTime))

def printWithElapsedTime(line):
	print("[" + getElapsedTime() + "] " + line)

def logError(line):
	with open(errorLogFile, "a") as error_log:
		error_log.write(line + '\n')

# Compute difference of contents from src to dst. Performs recursive calls for matching items on src and dst.
def diff(src, dst):

	global backupLogName
	global ignored

	# Both are files
	if os.path.isfile(src) and os.path.isfile(dst):

		srcStats = os.stat(src)
		dstStats = os.stat(dst)

		# File was modified or size is different
		if srcStats.st_mtime != dstStats.st_mtime or srcStats.st_size != dstStats.st_size:
			toDelete.append(dst)
			toAdd.append((src, dst))
		else:
			ignored += 1

	# One of them is a file and the other a folder
	elif os.path.isfile(src) or os.path.isfile(dst):
		toDelete.append(dst)
		toAdd.append((src, dst))

	# Both are folders
	else:
		src_items = os.listdir(src);
		dst_items = os.listdir(dst);

		for item in src_items:
			if item in dst_items:
				# Item is on both src and dst
				diff(os.path.join(src, item), os.path.join(dst, item))
			else:
				# Item is only on src
				toAdd.append((os.path.join(src, item), os.path.join(dst, item)))

		for item in dst_items:
			if item != backupLogName and item not in src_items:
				# Item is only on dst and not backup_log
				toDelete.append(os.path.join(dst, item))

# Deletes item from dst
def delete(dst):

	global processing
	global deleted

	printWithElapsedTime("Del > " + dst)
	processing = dst

	if os.path.isfile(dst):
		os.remove(dst)
	else:
		shutil.rmtree(dst)

	processing = None
	deleted += 1

# Copies item from src to dst
def add(src, dst):

	global processing
	global added

	printWithElapsedTime("Add > " + dst)
	processing = dst

	if os.path.isfile(src):
		shutil.copy2(src, dst)
	else:
		shutil.copytree(src, dst)

	processing = None
	added += 1

########### MAIN ###########

timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(startTime))
printWithElapsedTime("Starting backup on " + timestamp)

if backupLogName in os.listdir(rootSrc):
	logError("[" + timestamp + "] Backup log found on source folder: " + rootSrc)
	printWithElapsedTime("Backup log found on source folder: " + rootSrc)
	exit(1)

if backupLogName not in os.listdir(rootDst):
	logError("[" + timestamp + "] Backup log not found on destination folder: " + rootDst)
	printWithElapsedTime("Backup log not found on destination folder: " + rootDst)
	exit(2)

try:
	printWithElapsedTime("Computing differences...")
	diff(rootSrc, rootDst)
	printWithElapsedTime(str(len(toAdd)) + " additions, " + str(len(toDelete)) + " deletions")

	for deletion in toDelete:
		delete(deletion)

	for addition in toAdd:
		add(addition[0], addition[1])

	status = "OK"
	printWithElapsedTime("Finished backup")
	exit(0)

except Exception as e:
	logError("[" + timestamp + "] Unknown exception: " + str(e))
	printWithElapsedTime("Unknown exception: " + str(e))
	exit(3)

finally:
	with open(backupLogFile, "a") as backup_log:
		backup_log.write('{"timestamp": "' + timestamp + '", "status": "' + status + '", "elapsed": "' + getElapsedTime() + '", "added": "' + str(added) + '", "deleted": "' + str(deleted) + '", "ignored": "' + str(ignored) + '", "failed": "' + str(processing) + '"}\n')