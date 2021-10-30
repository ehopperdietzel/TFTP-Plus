import struct

def getMsgId(msg):
    if msg[0] == '\0':
        return 0
    else:
        return struct.Struct('=b').unpack(msg[0])[0]

# Python structs documentation
# https://docs.python.org/3/library/struct.html

# Requests ( from client to server ) -----------------------------------------------------------------

# Login
# request id(0)     | token expiration time     | username              | password
# signed char       | unsigned short            | char array[254]       | char array[254]
reqLogin = struct.Struct('=b H 254s 254s') 
reqLoginId = 0

# Logout (tells the server to change secret key for this client)
# request id(1)     | user id               | token expiration date | token
# signed char       | unsigned short        | char array[12]        | char array[32]
reqLogout = struct.Struct('=b H 14s 32s')
reqLogoutId = 1

# Get the current directory index size in bytes
# request id(1)     | user id               | token expiration date | token
# signed char       | unsigned short        | char array[12]        | char array[32]
reqIndex = struct.Struct('=b H 14s 32s')
reqIndexId = 1

# Start index transfer request
# request id(2)     | answer True or False  | user id               | token expiration date | token
# signed char       | _Bool                 | unsigned short        | char array[12]        | char array[32]
reqIndexInitTransfer = struct.Struct('=b ? H 14s 32s')
reqIndexInitTransferId = 2

# Index transfer packet ACK
# request id(3)     | packet number         | user id               | token expiration date | token
# signed char       | unsigned int          | unsigned short        | char array[12]        | char array[32]
reqIndexACKTransfer = struct.Struct('=b I H 14s 32s')
reqIndexACKTransferId = 3

# Tell the server to go to previous directory
# request id(4)     | user id               | token expiration date | token
# signed char       | unsigned short        | char array[12]        | char array[32]
reqBack = struct.Struct('=b H 14s 32s')
reqBackId = 4

# Tell the server to go to directory at index i
# request id(5)     | index of the dir      | user id               | token expiration date | token
# signed char       | unsigned int          | unsigned short        | char array[12]        | char array[32]
reqGoto = struct.Struct('=b I H 14s 32s')
reqGotoId = 5

# Tell the server to get size and name of file at index i
# request id(6)     | index of the file     | user id               | token expiration date | token
# signed char       | unsigned int          | unsigned short        | char array[12]        | char array[32]
reqFileInfo = struct.Struct('=b I H 14s 32s')
reqFileInfoId = 6

# Tell the server to start or cancel transfer of file
# request id(7)     | transfer id   | answer True or False  | user id               | token expiration date | token
# signed char       | unsigned char |  _Bool                | unsigned short        | char array[12]        | char array[32]
reqFileInitTransfer = struct.Struct('=b B ? H 14s 32s')
reqFileInitTransferId = 7

# File transfer packet ACK
# request id(8)     | transfer id   | packet number  
# signed char       | unsigned char | unsigned int  
reqFileACKTransfer = struct.Struct('=b B I')
reqFileACKTransferId = 8

# File post request
# request id(9)     | file size in bytes   | user id               | token expiration date | token          | dest file name 
# signed char       | unsigned long long   | unsigned short        | char array[12]        | char array[32] | char array[457]
reqPostTransfer = struct.Struct('=b Q H 14s 32s 457s')
reqPostTransferId = 9

# File post packet
# request id(10)    | transfer id   | packet number | data
# signed char       | unsigned char | unsigned int  | char array[506]    
reqPostPacket = struct.Struct('=b B I 506s')
reqPostPacketId = 10

# Events ( from server to client ) --------------------------------------------------------------------

# Login
# event id(0)       | user id                   | token expiration date | token
# signed char       | unsigned short            | char array[12]        | char array[32]
eveLogin = struct.Struct('=b H 14s 32s') 
eveLoginId = 0

# Index Size
# event id(1)       | index size in bytes
# signed char       | unsigned long long
eveIndex = struct.Struct('=b Q')
eveIndexId = 1

# Index Transfer
# event id(2)       | packet number | data
# signed char       | unsigned int  | void *[507]
eveIndexTransfer = struct.Struct('=b I 507s')
eveIndexTransferId = 2

# Go back success response
# event id(3) 
# signed char  
eveBack = struct.Struct('=b')
eveBackId = 3

# Goto success response
# event id(4) 
# signed char  
eveGoto = struct.Struct('=b')
eveGotoId = 4

# File Size and name response
# event id(5)   | transfer id    | file size in bytes    | file name
# signed char   | unsigned char  | unsigned long long    | char array[502]
eveFileInfo = struct.Struct('=b B Q 502s') 
eveFileInfoId = 5

# File Transfer
# event id(6)   | transfer id   | packet number | data
# signed char   | unsigned char | unsigned int  | void *[506]
eveFileTransfer = struct.Struct('=b B I 506s')
eveFileTransferId = 6

# File Post
# event id(7)   | port          | transfer id   
# signed char   | unsigned int  | unsigned char 
eveFilePost = struct.Struct('=b B')
eveFilePostId = 7

# File post ACK
# request id(8)     | transfer id   | packet number 
# signed char       | unsigned char | unsigned int  
eveFilePostACK = struct.Struct('=b B I')
eveFilePostACKId = 8

# Login error (invalid credentials)
# event id(-1) 
# signed char  
eveLoginErr = struct.Struct('=b')
eveLoginErrId = -1

# Auth error
# event id(-2) 
# signed char  
eveAuthErr = struct.Struct('=b')
eveAuthErrId = -2

# Token expired error
# event id(-3) 
# signed char  
eveExpErr = struct.Struct('=b')
eveExpErrId = -3

# Prohibited directory access error
# event id(-4) 
# signed char  
evePohibitedDirAccessErr = struct.Struct('=b')
evePohibitedDirAccessErrId = -4

# Item at index is not a directory or doesn't exist
# event id(-5) 
# signed char  
eveNotDirErr = struct.Struct('=b')
eveNotDirErrId = -5 

# Item at index is not a file or doesn't exist
# event id(-6) 
# signed char  
eveNotFileErr = struct.Struct('=b')
eveNotFileErrId = -6

# Prohibited file access error
# event id(-7) 
# signed char  
evePohibitedFileAccessErr = struct.Struct('=b')
evePohibitedFileAccessErrId = -7

# Prohibited file post
# event id(-8) 
# signed char  
evePohibitedFilePostErr = struct.Struct('=b')
evePohibitedFilePostsErrId = -8

