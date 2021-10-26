import socket
import time
import sys
import hashlib
from datetime import datetime, timedelta
import os
import select


sys.path.append('../')
from protocol import *

# Configuration
secret          = "SECRET_KEY"    
ipAddr          = "127.0.0.1"
port            = 3000
bufferSize      = 512

users           = [{"id":0,"username":"eduardo","password":"123","path":"./data/eduardo"}]
outTransfers    = []
maxActivePackets = 20

 
# Create socket
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind((ipAddr, port))

print("Welcome to the TFTP+ server")

def getNextMessage(timeoutSecs):
    if len(select.select([UDPServerSocket],[],[],timeoutSecs)[0]) == 0:
        return (False,False)
    else:
        return UDPServerSocket.recvfrom(bufferSize)

def findUserById(id):
    for user in users:
        if user["id"] == id:
            return user
    return False

def loginRequest(message,address):
    global secret
    reqId,expTime,username,password = reqLogin.unpack(message)
    print("New login request from: "+username+" with passwd "+password)
    
    # Validate user credentials
    for user in users:
        if user["username"] == username.rstrip('\x00') and user["password"] == password.rstrip('\x00'):
            eventId = 0
            userId = user["id"]
            expDatetime = (datetime.now()+timedelta(hours=expTime)).strftime("%d%m%Y%H%M%S")
            token = hashlib.sha256(secret+str(userId)+expDatetime).digest()
            event = eveLogin.pack(eventId,userId,expDatetime,token)
            UDPServerSocket.sendto(event, address)
            print("User "+username+" logged in!")
            return
    # Invalid credentials
    print("Error: invalid credentials.")
    event = eveLoginErr.pack(-1)
    UDPServerSocket.sendto(event, address)

def validateToken(address,userId,expDatetime,token):
    global secret
    if hashlib.sha256(secret+str(userId)+expDatetime).digest() == token:

        # Check exp date
        if datetime.strptime(expDatetime,"%d%m%Y%H%M%S") > datetime.now():
            return True
        else:
            event = eveExpErr.pack(-3)
            UDPServerSocket.sendto(event, address)
            print("\nRequest failed due to expired token.")
            return False
    else:
        event = eveAuthErr.pack(-2)
        UDPServerSocket.sendto(event, address)
        print("\nRequest failed due to invalid token.")
        return False

def processOutTransfers():
    global outTransfers
    transferTimeout = timedelta(seconds=60)
    packetTimeout = timedelta(seconds=15)
    for i in range(len(outTransfers)):
        transfer = outTransfers[i]

        # Check if trasnfer timedout
        if transfer["lastACK"] + transferTimeout < datetime.now():
            print("\nIndex transfer failed due to 60 secconds ACK timeout.")

            if "fd" in transfer:
                transfer["fd"].close()

            outTransfers.pop(i)
            return
        
        # Index transfer
        if transfer["transferType"] == 1:
            activePackets = 0 # Packets being send
            sentPackets = 0 # Packets that received ACK
            for packet in transfer["packets"]:
                if packet["receivedACK"] == False and packet["lastSend"] != None and packet["lastSend"] + packetTimeout > datetime.now():
                    activePackets += 1
                if packet["receivedACK"] == True:
                    sentPackets += 1

            totalPackets = len(transfer["packets"])
            print("\n"+str(100*sentPackets/totalPackets)+"% index data sent to user " + transfer["username"])

            if sentPackets == totalPackets:
                print("\nIndex transfer finished successfully.")
                outTransfers.pop(i)
                return
            else:
                index = 0
                while activePackets < maxActivePackets and index < totalPackets:
                    packet = transfer["packets"][index]
                    # If the packet hasn't received ACK and hasn't been sent or ACK has timed out, it is sent again
                    if packet["receivedACK"] == False and (packet["lastSend"] == None or packet["lastSend"] + packetTimeout < datetime.now()):
                        activePackets += 1
                        event = eveIndexTransfer.pack(2,index,len(packet["data"]),packet["data"])
                        UDPServerSocket.sendto(event, transfer["client"])
                        outTransfers[i]["packets"][index]["lastSend"] = datetime.now()
                    index+=1

        if transfer["transferType"] == 2:
            activePackets = 0 # Packets being send
            sentPackets = 0 # Packets that received ACK
            for packet in transfer["packets"]:
                if packet["receivedACK"] == False and packet["lastSend"] != None and packet["lastSend"] + packetTimeout > datetime.now():
                    activePackets += 1
                if packet["receivedACK"] == True:
                    sentPackets += 1

            totalPackets = len(transfer["packets"])
            print("\n"+str(100*sentPackets/totalPackets)+"% file data sent to user " + transfer["username"])

            fd = transfer['fd']
            if sentPackets == totalPackets:
                print("\nFile transfer finished successfully.")
                fd.close()
                outTransfers.pop(i)
                return
            else:
                index = 0
                while activePackets < maxActivePackets and index < totalPackets:
                    packet = transfer["packets"][index]
                    # If the packet hasn't received ACK and hasn't been sent or ACK has timed out, it is sent again
                    if packet["receivedACK"] == False and (packet["lastSend"] == None or packet["lastSend"] + packetTimeout < datetime.now()):
                        activePackets += 1
                        fd.seek(501*index)
                        print(packet["length"])
                        event = eveFileTransfer.pack(6,transfer["fileIndex"],index,packet["length"],fd.read(packet["length"]))
                        UDPServerSocket.sendto(event, transfer["client"])
                        outTransfers[i]["packets"][index]["lastSend"] = datetime.now()
                    index+=1
                
                        



def indexRequest(message,address):
    global outTransfers
    _,userId,expDatetime,token = reqIndex.unpack(message)

    # Check auth
    if validateToken(address,userId,expDatetime,token):
        
        # Creates index and calculate size size
        user = findUserById(userId)
        indexData = ""
        for file in os.listdir(user["path"]):
            L = len(file)
            format = '=?I'+str(L)+'s'
            # Is directory ? | name length | name
            indexData += bytes(struct.pack(format,os.path.isdir(user["path"]+"/"+file),L,file))

        totalBytes = len(indexData)
        print("\nIndex size is: "+str(totalBytes)+" bytes.")
        event = eveIndex.pack(2,totalBytes)

        for i in range(4):
            print("\nSending index size to "+user["username"]+".")
            UDPServerSocket.sendto(event, address)

            if totalBytes == 0:
                return

            request,addr = getNextMessage(30)

            if request:
                messageId = getMsgId(request)
                if messageId == 2:
                    _,answer,userId,expDatetime,token = reqIndexInitTransfer.unpack(request)

                    # Check auth again
                    if validateToken(addr,userId,expDatetime,token):

                        # Init index transfer ( server must keep the client address and port because auth data wont be sent during transfer )
                        if answer == True:
                            user = findUserById(userId)
                            # Create the new transfer
                            newTransfer = {"transferType":1,"lastACK":datetime.now(),"client":addr,"username":user["username"],"packets":[]}

                            # Total packets to send
                            totalPackets = int(totalBytes/505)
                            if totalBytes % 505 != 0:
                                totalPackets += 1
                            
                            # Each packet contains max 505 bytes of data
                            for j in range(totalPackets):
                                offset = j*505
                                length = 505
                                if j == totalPackets-1:
                                    length = totalBytes - offset
                                
                                newTransfer["packets"].append({"receivedACK":False,"lastSend":None,"data":indexData[offset:offset+length]})
                            
                            outTransfers.append(newTransfer)
                            print("\nTransfering index to user "+user["username"]+".")
                            processOutTransfers()
                            return
                        else:
                            print("\nClient cancelled index transfer.")
                            return



            else:
                print("\nSending index size to "+user["username"]+" again "+str(i+1)+".")
        
        print("\nError: Index directory transfer failed due to cliente response timeout.")
        return

    return

def processIndexACK(message,address):
    _,packetNumber,userId,expDatetime,token = reqIndexACKTransfer.unpack(message)
    if validateToken(address,userId,expDatetime,token):
        for i in range(len(outTransfers)):
            transfer = outTransfers[i]
            if transfer["client"] == address:
                print("\nGot index packet ACK " + str(packetNumber))
                outTransfers[i]["packets"][packetNumber]["receivedACK"] = True
                outTransfers[i]["lastACK"] = datetime.now()
                return
            
def goBackRequest(message,address):
    _,userId,expDatetime,token = reqBack.unpack(message)
    if validateToken(address,userId,expDatetime,token):
        # Here you should validate if user has access privileges in target directory ( not implemented )

        for i in range(len(users)):
            if users[i]["id"] == userId:
                users[i]["path"] += "/.."

        print("\nGo back request successfull.")
        event = eveBack.pack(3)
        UDPServerSocket.sendto(event, address)

def goToRequest(message,address):
    _,index,userId,expDatetime,token = reqGoto.unpack(message)
    if validateToken(address,userId,expDatetime,token):
        # Here you should validate if user has access privileges in target directory ( not implemented )
        user = findUserById(userId)
        files = os.listdir(user["path"])
        lenFiles = len(files)

        # Check if index exist
        if index >= lenFiles:
            event = eveNotDirErr.pack(-5)
            UDPServerSocket.sendto(event, address)
            print("\nError: Dir index doesn't exist.")
            return

        # Check if item at index is dir
        newPath = user["path"] + "/" + files[index]
        if not os.path.isdir(newPath):
            event = eveNotDirErr.pack(-5)
            UDPServerSocket.sendto(event, address)
            print("\nError: Item at index is not a dir.")
            return
        else:
            for i in range(len(users)):
                if users[i]["id"] == userId:
                    users[i]["path"] = newPath
                    event = eveGoto.pack(4)
                    UDPServerSocket.sendto(event, address)
                    print("\nGoto request successfull.")


def fileRequest(message,address):
    global outTransfers
    _,fileIndex,userId,expDatetime,token = reqFileInfo.unpack(message)

    # Check auth
    if validateToken(address,userId,expDatetime,token):
        
        user = findUserById(userId)
        files = os.listdir(user["path"])

        # Check if file exists
        if fileIndex >= len(files):
            print("\nFile doesn't exists.")
            event = eveNotFileErr.pack(-6)
            UDPServerSocket.sendto(event, address)
            return

        # Check if item at index is file
        filePath = user["path"] + "/" + files[fileIndex]
        if os.path.isdir(filePath):
            print("\nItem is not a file.")
            event = eveNotFileErr.pack(-6)
            UDPServerSocket.sendto(event, address)
            return


        totalBytes = os.path.getsize(filePath)
        fileName = files[fileIndex]
        event = eveFileInfo.pack(5,totalBytes,fileName)

        for i in range(4):
            UDPServerSocket.sendto(event, address)
            request,addr = getNextMessage(30)

            if request:
                messageId = getMsgId(request)
                if messageId == 7:
                    _,answer,userId,expDatetime,token = reqFileInitTransfer.unpack(request)

                    # Check auth again
                    if validateToken(addr,userId,expDatetime,token):

                        # Init index transfer ( server must keep the client address and port because auth data wont be sent during transfer )
                        if answer == True:
                            user = findUserById(userId)
                            fd = open(filePath,"r")
                            # Create the new transfer
                            newTransfer = {"fd":fd,"transferType":2,"filePath":filePath,"lastACK":datetime.now(),"fileIndex":fileIndex,"client":addr,"username":user["username"],"packets":[]}

                            # Total packets to send
                            totalPackets = int(totalBytes/501)
                            if totalBytes % 501 != 0:
                                totalPackets += 1
                            
                            # Each packet contains max 501 bytes of data
                            for j in range(totalPackets):
                                offset = j*501
                                length = 501
                                if j == totalPackets-1:
                                    length = totalBytes - offset
                                
                                newTransfer["packets"].append({"receivedACK":False,"lastSend":None,"length":length})
                            
                            outTransfers.append(newTransfer)
                            print("\nTransfering file to user "+user["username"]+".")
                            processOutTransfers()
                            return
                        else:
                            print("\nClient cancelled file transfer.")
                            return



            else:
                print("\nSending file info to "+user["username"]+" again "+str(i+1)+".")
        
        print("\nError: File transfer failed due to cliente response timeout.")
        return

    return       

def processFilePacketACK(message,address):
    _,fileIndex,packetNumber,userId,expDatetime,token = reqFileACKTransfer.unpack(message)
    if validateToken(address,userId,expDatetime,token):
        for i in range(len(outTransfers)):
            transfer = outTransfers[i]
            if transfer["client"] == address:
                if "fileIndex" in transfer:
                    if transfer["fileIndex"] == fileIndex:
                        print("\nGot file packet ACK " + str(packetNumber))
                        outTransfers[i]["packets"][packetNumber]["receivedACK"] = True
                        outTransfers[i]["lastACK"] = datetime.now()
                        return
while(True):

    # Get message
    message,address = getNextMessage(0)

    if message != False:
        messageId = getMsgId(message)

        # Login request
        if messageId == 0:
            loginRequest(message,address)
        # Index directory request
        if messageId == 1:
            indexRequest(message,address)
        # Index directory ACK
        if messageId == 3:
            processIndexACK(message,address)
        # Go back request
        if messageId == 4:
            goBackRequest(message,address)
        # Goto request
        if messageId == 5:
            goToRequest(message,address)
        # File request
        if messageId == 6:
            fileRequest(message,address)
        # File packet ACK
        if messageId == 8:
            processFilePacketACK(message,address)
                
    processOutTransfers()


   

# Sending a reply to client
#UDPServerSocket.sendto("hola", address)