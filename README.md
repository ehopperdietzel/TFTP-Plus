# TFTP-Plus
An extension of the TFTP 1350 file transfer protocol.

```
Network Working Group                                   E. Hopperdietzel
Request For Comments: TFTP+                                         UACh
STD: 33                                                     October 2021
Obsoletes: RFC 783


                     THE TFTP+ PROTOCOL

Status of this Memo

   This RFC specifies an IAB standards track protocol for the Internet
   community, and requests discussion and suggestions for improvements.
   Please refer to the current edition of the "IAB Official Protocol
   Standards" for the standardization state and status of this protocol.
   Distribution of this memo is unlimited.

Summary

   TFTP is a very simple protocol used to transfer files.  It is from
   this that its name comes, Trivial File Transfer Protocol or TFTP.
   Each nonterminal packet is acknowledged separately.  This document
   describes the protocol and its types of packets.  The document also
   explains the reasons behind some of the design decisions.

Acknowlegements

   The protocol was originally designed by Noel Chiappa, and was
   redesigned by him, Bob Baldwin and Dave Clark, with comments from
   Steve Szymanski. 

   This research was inspired by Christian Lazo, professor of the 
   Networks at Universidad Austral de Chile.

1. Changes

   TFTP+ is an extention to the TFTP protocol, which includes the next
   features:

   User authentication

      TFTP+ includes a token based authentication mechanism.
      This allows clients to comunicate with a server from multiple
      devices simultaneusly.
      It also adds an extra control layer to the server, allowing
      it to restrict file and directory accesss to certain users.

   Servers directory navigation

      Clients can now request for index data of directories on the
      server, and also navigate through them.

   Simultaneus packet transfer

      Servers and clients can now send multiple data packets without
      requiring previous ACK.

   Simultaneus file transfer

      Client and servers can now transfer up to 255 simultaneus files 
      using the same ip and port.



Hopperdietzel                                                   [Page 1]

RFC TFTP+                   TFTP+ Revision                  October 2021

2. Messages

   Messages from clients to server are called requests and messages from 
   server to clients are called events. All messages sizes must be of 
   512 bytes or less. The first byte of every message must contain a 
   signed char with the id of the message. Negative ids represent errors.

3. Data types ( big-endian )

   |-----------------------------
   | bool               | 1 byte
   |-----------------------------
   | signed char        | 1 byte
   |-----------------------------
   | char               | 1 byte
   |-----------------------------
   | unsigned short     | 2 bytes 
   |-----------------------------
   | unsigned integer   | 4 bytes
   |-----------------------------
   | unsigned long long | 8 bytes
   |-----------------------------


3. Authentication

   TFTP+ uses sha256 hash tokens to let servers authenticate users.

   To get an auth token from the server a client must send the 
   following request:

   |------------------------------------------------------------------
   | request id(0) | token expiration time | username  | password
   |------------------------------------------------------------------
   | signed char   | unsigned short        | char(254) | char(254)
   |------------------------------------------------------------------

   Where the request id is 0, the token expiration time is an unsigned 
   short representing the expiration time in hours from now (0 for no 
   expiration), and the username and password are ascii strings.
   If the username or password length are shorter than 254 characters, 
   bytes on the right must be filled with '\0'.

   Once the server gets the request, it must validate the client 
   credentials. If the credentials are invalid it must send the 
   following error event:

   |--------------
   | event id(-1) 
   |--------------
   | signed char  
   |--------------

 

Hopperdietzel                                                   [Page 2]

RFC TFTP+                   TFTP+ Revision                  October 2021

   Otherwise the following event:

   |-----------------------------------------------------------------
   | event id(0) | user id        | token expiration date | token
   |-----------------------------------------------------------------
   | signed char | unsigned short | char(12)              | char(32)
   |-----------------------------------------------------------------

   Where the user id must be unique for each client credentials (users 
   could be stored for example in a database).
   The token expiration date is calculated with the current server time 
   plus the time requested by the client.

   It is a 12 char string with the following structure: 
   
      ddmmyyyyHHMMSS (day,month,year,hour,minute,second). 
   
   If the requested time is 0, then the date string must be random 
   with the first character being '-'.

   The token is calculated using the sha256 hash algorithm, so the 
   server must keep and use a secret key string.

      32 bytes token = sha256(
         concatenated(
            bytes(secretkey),
            bytes(user id),
            bytes(expiration date)
         ))

   The client then must keep the user id, expiration date and token 
   and send it in the future requests that requires it.

   To check if the token is valid the server must calculate the token 
   again with the user Id and expiration date sent
   by the client and check if it matches the token (sent by the client).
   If the tokens doesn't match it must send an auth error event:

   |--------------
   | event id(-2) 
   |--------------
   | signed char  
   |--------------

   Else if the tokens matches but it has expired it must send the 
   following event:

   |------------------
   | event id(-2) 
   |------------------
   | signed char  
   |------------------


   If some of the messages are lost during the login process, then 
   client and server must timemout and try again.

   The client can also request to expire all its active tokens.
   To do so it must send the following request

   |------------------------------------------------------------------
   | event id(127) | user id        | token expiration date | token
   |------------------------------------------------------------------
   | signed char   | unsigned short | char(12)              | char(32)
   |------------------------------------------------------------------

   The server then shoud change the secret key used for future token
   requests (at least for this specific user) and reply with:

   |------------------
   | event id(-128) 
   |------------------
   | signed char  
   |------------------


Hopperdietzel                                                   [Page 3]

RFC TFTP+                   TFTP+ Revision                  October 2021

4. Get the current directory index data

   Clients can request the list of files and directory names of the 
   current directory in the server.

   Where format of the index data is a concatenated list of bytes of 
   blocks with the following structure:

   |-------------------------------------------------------
   | is directory? | filename length (N) | file or dir name
   |-------------------------------------------------------
   | bool          | unsigned short      | char(N)
   |-------------------------------------------------------

   The id of each file or directory is the index in which they 
   appear in the list.

   So to get the index the client must send the following request first 
   to get the total size in bytes of the directory data:

   |------------------------------------------------------------
   | request id(1) | user id        | token exp date | token
   |------------------------------------------------------------
   | signed char   | unsigned short | char(12)       | char(32)
   |------------------------------------------------------------

   The server must validate the auth token and reply with the auth 
   error event if it is invalid.
   If the token is valid it must reply the following event:

   |------------------------------------
   | event id(1) | index size in bytes
   |-----------------------------------
   | signed char | unsigned long long
   |------------------------------------

   Where the second argument is the size in bytes of the current 
   directory index data formatted as mentioned before.

   Once the client gets the index data size, it must reply with:

   |--------------------------------------------------------------------
   | request id(2) | answer | user id        | token exp date | token
   |--------------------------------------------------------------------
   | signed char   | bool   | unsigned short | char(12)       | char(32)
   |--------------------------------------------------------------------

Hopperdietzel                                                   [Page 4]

RFC TFTP+                   TFTP+ Revision                  October 2021

   If the answer is True, the server will begin to transfer the data, 
   else the process ends.

   Each packet of index data sent by the server is as follows:

   |-----------------------------------------------------
   | event id(2)       | packet number | data
   |-----------------------------------------------------
   | signed char       | unsigned int  | char array
   |-----------------------------------------------------

   Where the length of 'data' must be 507 bytes or less in case of the 
   last packet. The packet number must represent the order of the 
   packets begining with 0.
   The server can send any amount of packets without requiring previous 
   client ACK, but it should keep track of the time they were sent and 
   resend them if timeout. If no ACK is received at all in a certain 
   amount of time, the server should stop the transfer.

   The client must be prepared to receive and store the packets in a 
   random order. Each time it receives a packet must send the 
   following ACK:

|---------------------------------------------------------------------------
| request id(3) | packet number | user id        | token exp date | token
|---------------------------------------------------------------------------
| signed char   | unsigned int  | unsigned short | char(12)       | char(32)
|---------------------------------------------------------------------------

   Including the number of the packet received.
   It also should keep track of the total amount of bytes of the 'data' 
   field received. The transfer successfully ends when the server 
   receives all ACKs and the client receive the total amount of 
   bytes of 'data'.

5. Go to previus directory

   Clients can request to go to the previus directory in the server.
   To do so they must send the following request:

   |------------------------------------------------------------
   | request id(4) | user id        | token exp date | token
   |------------------------------------------------------------
   | signed char   | unsigned short | char(12)       | char(32)
   |------------------------------------------------------------

   The server should check if the client has the permissions to access 
   that directory.
   If not, it should reply with one of the following error events:

Hopperdietzel                                                   [Page 5]

RFC TFTP+                   TFTP+ Revision                  October 2021

   Prohibited directory access error.
   |-------------------
   | event id(-4) 
   |-------------------
   | signed char  
   |-------------------

   Directory doesn't exist.
   |-------------------
   | event id(-5) 
   |-------------------
   | signed char  
   |-------------------

   Else it should reply:

   Go back success response
   |-------------------
   | event id(3) 
   |-------------------
   | signed char  
   |-------------------

   The client then should send again the current directory index data 
   request to get the current index data.

6. Go to directory

   Clients can request to go to a certain directory inside the current 
   server directory.
   To do so they must send the index of that directory:

|--------------------------------------------------------------------------
| request id(5) | dir index    | user id        | token exp date | token
|--------------------------------------------------------------------------
| signed char   | unsigned int | unsigned short | char(12)       | char(32)
|--------------------------------------------------------------------------

   The server should check if the client has the permissions to access 
   that directory and if the item at that index is a file instead and reply 
   with one of the following events:

   Prohibited directory access error.
   |-------------------
   | event id(-4) 
   |-------------------
   | signed char  
   |-------------------

   Item at index is not a directory error.
   |-------------------
   | event id(-5) 
   |-------------------
   | signed char  
   |-------------------

Hopperdietzel                                                   [Page 6]

RFC TFTP+                   TFTP+ Revision                  October 2021

   Goto success response
   |-------------------
   | event id(4) 
   |-------------------
   | signed char  
   |-------------------

   The client then should send again the current directory index data 
   request to get the current index data.

7. Get file request

   Clients can request a certain file of the current directory in the 
   server. To do so they first must get a transfer id, server transfer 
   port and the name and size in bytes of the file sending the 
   following request:

   IMPORTANT! : The client ip address and port from which this request 
   is sent is going to be the address and port the server will send and
   receive the future data packets and ACKs.

|--------------------------------------------------------------------------
| request id(6) | file index   | user id        | token exp date | token
|--------------------------------------------------------------------------
| signed char   | unsigned int | unsigned short | char(12)       | char(32)
|--------------------------------------------------------------------------

   Where 'index of the file' is the index of the file in the current 
   directory.

   The server should check if the client has the permissions to access 
   that file, also check if the item at the requested index is not a 
   file and reply with one of the following events:

   Item at index is not a file or doesn't exist error.
   |-------------------
   | event id(-6) 
   |-------------------
   | signed char  
   |-------------------


   Prohibited file access error.
   |-------------------
   | event id(-7) 
   |-------------------
   | signed char  
   |-------------------

   Success.
|-----------------------------------------------------------------------------
| event id(5) | port         | transfer id   | file size in bytes | file name
|-----------------------------------------------------------------------------
| signed char | unsigned int | unsigned char | unsigned long long | char(502)
|-----------------------------------------------------------------------------

Hopperdietzel                                                   [Page 7]

RFC TFTP+                   TFTP+ Revision                  October 2021

   The 'port' param is the port from which the server will send data 
   from and receive the client ACKs.
   The 'transfer id' param let the client and server identify to which 
   file are the data packages and ACKs related to during a transfer.
   This allows up to 255 simultaneus file transfers for each client with 
   the same address and port.
   The server should also save the ip address and port of this request, 
   because the future ACKs wont contain authentication data.

   The client then must send the following request from the same ip 
   address and port of the previus request:

|-----------------------------------------------------------------------------------
| request id(7)| transfer id   | answer | user id        | token exp date | token
|-----------------------------------------------------------------------------------
| signed char  | unsigned char | bool   | unsigned short | char(12)       | char(32)
|-----------------------------------------------------------------------------------

   If the value of 'answer' is True then the server will start the 
   file transfer:

   Each packet of data sent by the server is as follows:

   |----------------------------------------------------------------
   | event id(6) | transfer id   | packet number | data
   |----------------------------------------------------------------
   | signed char | unsigned char | unsigned int  | char(506)
   |----------------------------------------------------------------

   Where the length of 'data' must be 506 bytes or less in case of 
   the last packet.
   The packet number must represent the order of the packets begining 
   with 0. The server can send any amount of packets without requiring 
   previous client ACK, but it should keep track of the time they were 
   sent and resend them if timeout.
   If no ACK is received at all in a certain amount of time, the 
   server should stop the transfer.

   The client must be prepared to receive and store the packets 
   in a random order.
   Each time it receives a packet must send the following ACK:

   |--------------------------------------
   | request id(3) | packet number         
   |--------------------------------------
   | signed char   | unsigned int          
   |--------------------------------------

   IMPORTANT! : Notice that in this case the authentication data is 
   not required, so the ip address and port should not be changed 
   during a transfer as mentioned before.

   Including the number of the packet received.
   It also should keep track of the total amount of bytes of the 
   'data' field received.
   The transfer successfully ends when the server receives all ACKs 
   and the client receive the total amount of bytes of 'data'.

Hopperdietzel                                                   [Page 8]

RFC TFTP+                   TFTP+ Revision                  October 2021

8. Post file request

   Clients can request to send local files to the current directory 
   of the server.

   To do so they first must send the following request (from the ip and 
   port they will use to send the future packets and receive the 
   server ACKs):

|-------------------------------------------------------------------------------------------------
| request id(9) | file size in bytes | user id        | token exp date | token    | dest file name 
|-------------------------------------------------------------------------------------------------
| signed char   | unsigned long long | unsigned short | char(12)       | char(32) | char(457)
|-------------------------------------------------------------------------------------------------

   Where 'dest file name' is the name the server will use to 
   save the file.

   The server then must reply with one of the following events:

   Prohibited file posting.
   |--------------
   | event id(-8) 
   |--------------
   | signed char  
   |--------------

   Success
   |-----------------------------------------------
   | event id(7) | port         | transfer id   
   |-----------------------------------------------
   | signed char | unsigned int | unsigned char 
   |-----------------------------------------------

   The client then can start sending packets to the port specified 
   by the server.

   |-----------------------------------------------------------
   | request id(10) | transfer id   | packet number | data
   |-----------------------------------------------------------
   | signed char    | unsigned char | unsigned int  | char(506)
   |-----------------------------------------------------------

   The server must ACK every packet with:

   |------------------------------------------------
   | request id(8) | transfer id   | packet number 
   |------------------------------------------------
   | signed char   | unsigned char | unsigned int  
   |------------------------------------------------

   The transfer successfully ends when the client receives all 
   ACKs and the server receive the total amount of bytes of 'data'.


Hopperdietzel                                                   [Page 9]

RFC TFTP+                   TFTP+ Revision                  October 2021


References

   [1]  USA Standard Code for Information Interchange, USASI X3.4-1968.

   [2]  Postel, J., "User Datagram  Protocol," RFC 768, USC/Information
        Sciences Institute, 28 August 1980.

   [3]  Postel, J., "Telnet Protocol Specification," RFC 764,
        USC/Information Sciences Institute, June, 1980.

   [4]  Braden, R., Editor, "Requirements for Internet Hosts --
        Application and Support", RFC 1123, USC/Information Sciences
        Institute, October 1989.

Security Considerations

   Since TFTP+ includes no encryption mechanism, it is not recomended 
   to be used in public networks.

Author's Address

   Eduardo A. Hopperdietzel
   Universidad Austral de Chile
   Instituto de Informática
   Av Otto Uebel s/n
   Puyuhuapi,Aysén

   Phone: (+56) 982-6409-33

   EMail: EDUARDO.HOPPERDIETZEL@ALUMNOS.UACH.CL


Hopperdietzel                                                   [Page 10]```