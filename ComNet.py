from collections import namedtuple
import base64
import json
import os
import socket
import time
   

def getConfig(jsonPath):
    try:
        with open (jsonPath,'r') as jsonFile:
            data = json.load(jsonFile)
    except FileNotFoundError:
        print(f"File Not Found: {jsonPath}")
        return []
    return data
def deathLoopCSVInput(string):
    res = ""
    i = 1
    while True:
        data = input(string + str(i) + ": ")
        if not data:
            break
        if(res != ""):
            res += ", "
        res += data 
        i += 1
    return res  

def getMailDataFromKeyboard(jsonData):
    print("You want to send this to ? Each mail address separated by a space(Example: to1 to2 to3).")
    print("Leave blank to finish.")
    to = deathLoopCSVInput("To ")
    cc = deathLoopCSVInput("Cc ")
    bcc = deathLoopCSVInput("Bcc ")
    while not (to or cc or bcc):
        print("You must input at least one receiver.")
        to = deathLoopCSVInput("To ")
        cc = deathLoopCSVInput("Cc ")
        bcc = deathLoopCSVInput("Bcc ")
    subject = input("Subject: ")
    content = []
    print("Email content (Type \"done\" in an seperated line to finish): ")
    while True:
        line = input()
        if line.lower() == "done":
            break
        content.append(line)   
   
    attachments =[]
    attachment = input("Do you want to attach (\"yes\" / \"no\"): ")
    attachment = attachment.lower()
    if attachment == "no":
        pass
    elif attachment == "yes":
        attPath = ""
        print("Input the path of the attachments (Max datasize = 3Mb).\n")
        print("Leave blank to end input process.\n")
        while True: 
            attPath = input("Attachment " + str(len(attachments) + 1) + ":")
            if not attPath:
                    break
            elif not os.path.exists(attPath):
                print("File path not exist.")
                pass
            fileSize = os.path.getsize(attPath)
            if fileSize > int (jsonData['misc']['size']) * 1024 * 1024:
                print("File size exceed limit.")
                pass
            else:
                attachments.append(attPath)
            
    else:
        print("Your choice is illegal.")

    emailMakeTuple = namedtuple("Maildata", "to cc bcc subject content attachments")
    emailData = emailMakeTuple(to, cc, bcc, subject, content, attachments)    

    return emailData

def split_data(input_string, chunk_size):
    return [input_string[i:i + chunk_size] for i in range(0, len(input_string), chunk_size)]


def encode_attachment(attPath):
    with open(attPath, "rb") as file:
        data = file.read()
        data = str(base64.b64encode(data))
        data = data[2:len(data)-1]
        splited_data = split_data(data, 72)
    encodedContent = base64.b64encode(data)
    return encodedContent

def getLocalDate():
    return time.asctime(time.localtime(time.time()))

def createBoundary():
    boundary = base64.b64encode(str(time.localtime()).encode('utf-8'));
    return str(boundary)

def generateMailId():
    ID = base64.b64encode(str(time.time()).encode('utf-8'));
    mailId = "Message-ID: <" + str(ID) + "@sample.vn>"
    return mailId

def formatEmailData(jsonData,emailData):
    sendEmailData = ""
    if emailData.attachments:
        boundary = createBoundary()
        boundary = "-----------" + sendEmailData[0:23]
        sendEmailData = "Content-Type: multipart/mixed; boundary=\""+ boundary +"\"\r\n"    
    sendEmailData += generateMailId()
    sendEmailData = generateMailId()
    sendEmailData += "\r\n" + "Date: " + getLocalDate()
    sendEmailData += "\r\n" + "MIME-Version: 1.0"
    sendEmailData += "\r\n" + "User-agent: SMail-HHH"
    sendEmailData += "\r\n" + "Content-Language: en-US"
    sendEmailData += "\r\n" + "To: " + emailData.to + "\r\n"

    if(emailData.cc != ""):
        sendEmailData += "Cc: " + emailData.cc
        
    sendEmailData += "From: " + jsonData['user']['username']
    sendEmailData += "<" + jsonData['user']['mail'] + ">" + "\r\n" 
    sendEmailData += "Subject: " + emailData.subject +"\r\n";
    
    if emailData.attachments:
        sendEmailData += "\r\n"
        sendEmailData += "This is a multi-part message in MIME format.\r\n"             
        sendEmailData += "--" + boundary + "`\r\n"
    
    sendEmailData += "Content-Type: text/plain; charset=utf-8; format=flowed\r\n"
    sendEmailData += "Content-Transfer-Encoding: 7bit\n\r\n"
    for line in emailData.content:
        sendEmailData += line + "\r\n"
    
    if emailData.attachments:
        for att in emailData.attachments:
            filename = os.path.basename(att)
            sendEmailData += "\r\n" + "--" + boundary + "\r\n"
            sendEmailData += "Content-Type: application/octet-stream; charset=UTF-8; name=\"" + filename + "\"\r\n"
            sendEmailData += "Content-Disposition: attachment; filename=\"" + filename + "\"\r\n"
            sendEmailData += "Content-Transfer-Encoding: base64\n"
            sendEmailData += "\r\n"
            with open(att, "rb") as f:
                data = f.read(int (jsonData['misc']['size']) *1024 *1024)
                data = str(base64.b64encode(data))
                data = data[2:len(data)-1]
                splited_data = split_data(data, 72)
                for line in splited_data:
                    sendEmailData += line + "\r\n"
    sendEmailData += ".\r\n"
    return sendEmailData

def send(jsonData, emailData , sendEmailData):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverIP = (jsonData['mail_server']['address'], int(jsonData['mail_server']['smtp_port']))
    try:
        client.connect(serverIP)
    except Exception as e:
        print("Unable to connect sever.")
        return
    ans = client.recv(1024)
    
    COMMAND = "EHLO [" + jsonData['mail_server']['address'] + "]\r\n"
    client.send(COMMAND.encode('utf-8'))
    ans = client.recv(1024)
    ans = str(ans)
    if(ans.find("250") == -1):
        print("EHLO failed.")
        return
    
    MAILFROM = "MAIL FROM: <" + jsonData['user']['username'] + ">\r\n"
    client.send(MAILFROM.encode('utf-8'))
    ans = client.recv(1024)
    ans = str(ans)
    if(ans.find("250") == -1):
        print("MAIL FROM failed.")
        return
    to_list = emailData.to.split()
    cc_list = emailData.cc.split()
    bcc_list = emailData.bcc.split()
    unique_list = set(to_list + cc_list + bcc_list)
    for to in unique_list:
        RCPTO = "RCPT TO: <" + to + ">\r\n"
        client.send(RCPTO.encode('utf-8'))
        ans = client.recv(1024)
        ans = str(ans)
        if(ans.find("250") == -1 & ans.find("251") == -1):
            print("RCPT TO failed.")
            return
        
    client.send("DATA\r\n".encode('utf-8'))
    ans = client.recv(1024)
    ans = str(ans)
    if(ans.find("354") == -1 & ans.find("250") == -1):
        print("DATA failed.")
        return
    for line in sendEmailData.splitlines():
        client.send(line.encode('utf-8') + b"\r\n")
    
    print("Mail sent successfully.")
    client.send('QUIT'.encode('utf-8'))
    client.close()
    return
        
def pop3connect(jsonData):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverIP = (jsonData['mail_server']['address'], int(jsonData['mail_server']['pop3_port']))
    try:
        client.connect(serverIP)
    except Exception as e:
        print("Unable to connect to server.")
        return
    
    ans = client.recv(1024).decode('utf-8')
    print(ans)
    
    user_command = f'USER {jsonData["user"]["mail"]}\r\n'
    client.sendall(user_command.encode('utf-8'))
    print(client.recv(1024).decode('utf-8'))
    
    pass_command = f'PASS {jsonData["user"]["password"]}\r\n'
    client.sendall(pass_command.encode('utf-8'))
    print(client.recv(1024).decode('utf-8'))
    
    client.sendall('LIST\r\n'.encode('utf-8'))
    ans = client.recv(1024).decode('utf-8')
    print(ans)
    
    x = input('RETR ')
    print ('\r\n')
    client.sendall(f'RETR {x}\r\n'.encode('utf-8'))
    print (client.recv(1024).decode('utf-8'))
    

    print ('QUIT\r\n')
    client.sendall('QUIT\r\n'.encode('utf-8'))
    print (client.recv(1024).decode('utf-8'))
    client.close()
    return
    
                    
#temp main

jsonData = getConfig('config.json')

x = input('0 for smtp, 1 for pop3 : ')
os.system('cls' if os.name == 'nt' else 'clear')
if x:
    pop3connect(jsonData)
elif not x:
    emailData = getMailDataFromKeyboard(jsonData)
    sendEmailData = formatEmailData(jsonData, emailData)
    send(jsonData, emailData, sendEmailData)
else:
    print('invalid')
    








