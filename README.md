dodane InitialClusterization, po odpaleniu mozna wybrac w Options, wybrać liczbę klastrów n i się tworzy.

póki co testowo są foldery:

INITIAL_IMAGES_FOLDER - pomieszane zdjęcia, docelowo to tak bedzie wygladac input dla naszej aplikacji

INITIAL_CLUSTERIZED_FOLDER - w tym folderze tworzy się n folderów z wstępnymi klastrami


trzeba bedzie DEFAULT_IMAGES_PATH zastapic tym INITIAL_CLUSTERIZED_FOLDER tylko w DEFAULT_IMAGES_PATH masz inna strukture bo jest [nazwy_rodzajów_klocków->podfoldery(321,4314 itd)->zdjecia] a chyba docelowo w aplikacji bedzie [Cluster_0->zdjecia] 

_______________________________________
zeby przetestowac workflow to:

1. INITIAL_IMAGES_FOLDER - tutaj wrzucasz po kilka zdjec z roznych grup

2. INITIAL_CLUSTERIZED_FOLDER - pusty folder, tutaj znajda sie kastry Cluster_0, Cluster_1 itd.

3. DEFAULT_IMAGES_PATH - tą ścieżkę ustawiasz na taka samą jak wyżej czyli jak w 2. docelowo 
te scieżki powinny wskazywać na to samo

4. RESIZED_IMAGES_PATH - pusty folder, tutaj wlecą sformatowane zdjęcia z 2./3.

![image](https://github.com/macius06xd/In-ynieryjka/assets/80836050/d02f708d-b9ab-4506-8462-c41357222486)

Odpalasz maina, wybierasz z Options "Perform initial clusterization" i wskakują nowo stworzone foldery. teraz robisz
create resized dataset i tutaj program się wywala. jesli się nie mylę to dlatego, że w folderach ktore nam dał jest jeden poziom folderów wiecej i CreateResizedDataset to uwzglednia (i pewnie tak samo ta klasteryzacja odpalane tym sliderem) (???). Ale chyba docelowo plik z wektorem cech nie będzie tak uporządkowany tylko będzie w nim po prostu iles tam zdjęc bezpośrednio(???)

InitialClusterization szuka odpowiedniego wektoru cech na podstawie nazwy zdjecia przeszukując podfoldery z xception, to pewnie docelowo tez do zmiany czyli nie bedzie musialo szukac w podfolderach,




