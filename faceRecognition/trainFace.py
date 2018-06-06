import cognitive_face as CF
import os
import json

def GetFileListFromDir(dir):
    l = []
    for p, d, f in os.walk(dir):
        for fname in f:
            l.append(os.path.join(p,fname))
    return l

def CheckGroupIdExistStatus(groupId):
    for info in CF.person_group.lists():
        if info['personGroupId'] == groupId:
            return True
    return False

# set Key
KEY = 
CF.Key.set(KEY)

# create group and person

personGroupId = "" 
# Valid format should be a string composed 
#by numbers, English letters in lower case,
# '-', '_', and no longer than 64 characters. 

if not CheckGroupIdExistStatus(personGroupId):
    CF.person_group.create(personGroupId,"Description about your group")
user1 = CF.person.create(personGroupId,"Descrption about the person")


# add face
friendImageDir = "img/person"
for fname in GetFileListFromDir(friendImageDir):
    CF.person.add_face(fname, personGroupId, user1['personId'])

# train
CF.person_group.train(personGroupId)


trainingStatus = "running"
while(True):
    trainingStatus = CF.person_group.get_status(personGroupId)
    if trainingStatus['status'] != "running":
        print(trainingStatus)
        break
