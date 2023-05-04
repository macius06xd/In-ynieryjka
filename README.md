// Co Trzeba(Można nic nie trzeba) zrobić
jakieś zapisywanie tego systemu plików i wczytywanie 
można zmienić żeby nody w klasa FileSystemNode nie trzymałą pełnej ściężki tylko relacyjnie od rodzica i potem napisać funkcje która bierze całą ścieżke
niby można by było dodać informacje ile plików jest w directory
jakąś funkcje która rozdziela directory na jakieś pod directory ( tak jak potem będzie ta clusteryzacja żeby pod to działało)
można by było zrobić że jak już ten system plików będzie zapisany ( można zapisać po pierwszym wczytaniu żeby nie siedział w pamięci cały czas tylko żeby sie wczytywał jak będzie potrzebny ale tu trzeba pomyślec jak wtedy przenoszenie sensowne zrobić)
Jakieś komentarze dodać żeby wyglądało
i podpisać zmienne typami bo mi odjebie
tyle wymyśliłem przez te chwile a tak imo to mamy coś tam zrobione bez wstydu można się pokazać i pogadać z nim ewentualnie pomyślec jakie rozwiązania wymyśliliśmy jak duzo tych plików będzie (żadne ale coś się zakręci) jak na moje poprostu ograniczamy ile plików się ładuje i tyle 
https://www.youtube.com/watch?v=Uq9d9wXYaBY

// Koniec Tego co trzeba zrobić

//Komenatrze
  04.05.2023 03:34
coś tam zrobiłem jakoś działa
tworzy się sztuczny system plików
da się przenosić pliki między folderami 
da sie przenosić foldery ale tak że się wszystko psuje bo się dzieci nie kopiują :) (łatwo to jest naprawić ale zapomniałem o tym)
więc w sumie to działa przenoszenie u góry ale nie do końca a przenoszenie między widgetami i w widgecie na dole nie działa więc w sumie nic nie działa ale wiem już jak to działa

  04.05.2023 19:52
wyodrebnione zmienne ścieżek dla folderów oraz stała rozmiaru zdjecia po resizingu do Configuration.py\
usuniete test.py i CreateSmall.py a small.py zmienione na CreateResizedDataset\
dodane Options gdzie uzytkownik moze uruchomic CreateResizedDataset\


//Do naprawienia
po uruchomieniu CreateResizedDataset trzeba na razie recznie zrestartowac aplikacje żeby pokazało nową zawartość folderu


