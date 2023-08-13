# In-ynieryjka

Odnośnie tego 

Tam się w child_ids w DataBase.py wyczarowuje 1000, nie wiem skąd to jest tymczasowo dodałem że jeśli id = 1000 to nie wykonuje dalej nic

Robie prepare datasets z domyslna liczba klastrów 4. Robię Cluster_2 na 4 klastry, robię Cluster_1 na 5 klastrów i dostaję to:

Sprawdzalem czy to moje zmiany z brancha 26.07 to robia ale chyba nie bo na 22.07 tez taki blad dostaje

![image](https://github.com/macius06xd/In-ynieryjka/assets/80836050/70c4ceeb-dc3a-4d3e-9afc-e59561c398a7)

Jakis losowy shit, Cluster_2 na 4, Cluster_1 na 5, Cluster_0 na iles i Cluster_4 na iles i to

![image](https://github.com/macius06xd/In-ynieryjka/assets/80836050/f1e5c76a-8fea-48db-b618-df52278334c8)


_______________________________________________________
Opis wykrywania czy wczytac czy stworzyc bazke

w configuration dodalem zmienna globalna

![image](https://github.com/macius06xd/In-ynieryjka/assets/80836050/49cec067-0b12-4023-9d1b-c823cf449b0c)

w main.py przypisuję jej 1 lub 0 w zaleznosci od czego czy uzytkownik wybierze Prepare datasets czy Skip

![image](https://github.com/macius06xd/In-ynieryjka/assets/80836050/b2127a7f-14c2-4ee5-892f-320ddccc613d)

I na podstawie tego w FileSystem robi co trzeba

![image](https://github.com/macius06xd/In-ynieryjka/assets/80836050/67937a2b-17bd-4a78-a66b-2da60309e7ce)

I teraz pierwsze co sie dzieje to sie wyswietla okno czy Prepare datasets/Skip