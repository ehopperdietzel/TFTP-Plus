import struct

def getMsgId(msg):
    if msg[0] == '\0':
        return 0
    else:
        return struct.Struct('=b').unpack(msg[0])[0]


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