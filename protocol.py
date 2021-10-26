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

# Get the current directory index size in bytes
# request id(1)     | user id               | token expiration date | token
# signed char       | unsigned short        | char array[12]        | char array[32]
reqIndex = struct.Struct('=b H 14s 32s') 

# Start index transfer request
# request id(2)     | answer True or False  | user id               | token expiration date | token
# signed char       | _Bool                 | unsigned short        | char array[12]        | char array[32]
reqIndexInitTransfer = struct.Struct('=b ? H 14s 32s')

# Index transfer packet ACK
# request id(3)     | packet number         | user id               | token expiration date | token
# signed char       | unsigned int          | unsigned short        | char array[12]        | char array[32]
reqIndexACKTransfer = struct.Struct('=b I H 14s 32s')

# Tell the server to go to previous directory
# request id(4)     | user id               | token expiration date | token
# signed char       | unsigned short        | char array[12]        | char array[32]
reqBack = struct.Struct('=b H 14s 32s')

# Tell the server to go to directory at index i
# request id(5)     | index of the dir      | user id               | token expiration date | token
# signed char       | unsigned int          | unsigned short        | char array[12]        | char array[32]
reqGoto = struct.Struct('=b I H 14s 32s')

# Tell the server to get size and name of file at index i
# request id(6)     | index of the file     | user id               | token expiration date | token
# signed char       | unsigned int          | unsigned short        | char array[12]        | char array[32]
reqFileInfo = struct.Struct('=b I H 14s 32s')

# Tell the server to start or cancel transfer of file
# request id(7)     | answer True or False  | user id               | token expiration date | token
# signed char       |  _Bool                | unsigned short        | char array[12]        | char array[32]
reqFileInitTransfer = struct.Struct('=b ? H 14s 32s')

# Index transfer packet ACK
# request id(8)     | file index    | packet number         | user id               | token expiration date | token
# signed char       | unsigned int  | unsigned int          | unsigned short        | char array[12]        | char array[32]
reqFileACKTransfer = struct.Struct('=b I I H 14s 32s')

# Events ( from server to client ) --------------------------------------------------------------------

# Login
# event id(0)       | user id                   | token expiration date | token
# signed char       | unsigned short            | char array[12]        | char array[32]
eveLogin = struct.Struct('=b H 14s 32s') 

# Index Size
# event id(1)       | index size in bytes
# signed char       | unsigned long long
eveIndex = struct.Struct('=b Q') 

# Index Transfer
# event id(2)       | packet number | bytes sent        | data
# signed char       | unsigned int  | unsigned short    | void *[505]
eveIndexTransfer = struct.Struct('=b I H 505s')

# Go back success response
# event id(3) 
# signed char  
eveBack = struct.Struct('=b')

# Goto success response
# event id(4) 
# signed char  
eveGoto = struct.Struct('=b')

# File Size and name response
# event id(5)       | file size in bytes    | file name
# signed char       | unsigned long long    | char array[403]
eveFileInfo = struct.Struct('=b Q 503s') 

# File Transfer
# event id(6)       | file index    | packet number | bytes sent        | data
# signed char       | unsigned int  | unsigned int  | unsigned short    | void *[501]
eveFileTransfer = struct.Struct('=b I I H 501s')

# Login error (invalid credentials)
# event id(-1) 
# signed char  
eveLoginErr = struct.Struct('=b')

# Auth error
# event id(-2) 
# signed char  
eveAuthErr = struct.Struct('=b')

# Token expired error
# event id(-3) 
# signed char  
eveExpErr = struct.Struct('=b')

# Prohibited directory access error
# event id(-4) 
# signed char  
evePohibitedDirAccessErr = struct.Struct('=b')

# Item at index is not a directory or doesn't exist
# event id(-5) 
# signed char  
eveNotDirErr = struct.Struct('=b')

# Item at index is not a file or doesn't exist
# event id(-6) 
# signed char  
eveNotFileErr = struct.Struct('=b')

# Prohibited file access error
# event id(-7) 
# signed char  
evePohibitedFileAccessErr = struct.Struct('=b')

