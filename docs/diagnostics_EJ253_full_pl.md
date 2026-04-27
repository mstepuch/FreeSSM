# Subaru EJ253 — pełna analiza diagnostyczna na podstawie logów FreeSSM

*Dokument sporządzony na podstawie dwóch logów:*
- *`FreeSSM_log2.csv` — jazda na LPG (liquefied petroleum gas, autogaz)*
- *`FreeSSM_log_cleared_memory_cold_start_gasoline_only.csv` — jazda na benzynie po skasowaniu pamięci sterownika*

---

## ⚠️ SPROSTOWANIE (data: 27 kwietnia 2026)

Po dyskusji z Michałem i ponownej analizie z poprawionym narzędziem (analizator v3, bump v1.3.0-ms.10), wycofuję trzy stwierdzenia z tego dokumentu:

### 1. **Bank 2 nie istnieje fizycznie w EJ253 NA**
Protokół SSM2 ma sloty B1/B2/B3/B4, ale **bank** to konstrukt ECU, nie geometryczny — istnieje tam, gdzie ECU ma dla niego osobną szerokopasmową sondę przedkatową i osobną pętlę regulacji. EJ253 NA ma **jedną zbiorczą sondę przedkatową** za Y-pipe i **jedną pętlę**. Z perspektywy regulacji to **jeden bank**. Sloty B2/B3/B4 w protokole są niewykorzystane.
Kanał LTFT B3 w Twoim logu to **placeholder** (stałe 0); STFT B3 to mikro-trim ±2.5 % o innej naturze. Analizator v3 wykrywa to automatycznie (`placeholder_channels`) i pomija w punktacji.

### 2. **Vacuum leak NIE występuje**
Poprzedni alarm opierał się na pojedynczym wskaźniku (LTFT idle nieco ujemny + MAP 33 kPa zinterpretowane jako „za wysokie"). To była luka analizatora.
Prawidłowy fingerprint nieszczelności wymaga **trzech niezależnych pillarów**:

| Pillar | Co byłoby przy wycieku | Co masz | Werdykt |
|---|---|---|---|
| P1: LTFT idle dodatni > +5 % | tak | **−6.3 %** (ujemny!) | ❌ |
| P2: MAP idle > 40 kPa abs | tak | **33.0 kPa** (zdrowy 27–35) | ❌ |
| P3: gradient idle−cruise > +5 pp | tak | **−6.3 pp** (odwrotny!) | ❌ |

Trzy z trzech pillarów **negatywne**, w tym jeden **odwrotny**. Wycofuję wątek wycieku w całości. Wykluczyłem go też z listy podejrzanych w problemie WOT.

### 3. **„Idle hunting std=367" to artefakt klasyfikatora**
Mój klasyfikator faz wpuszczał do worka „IDLE" próbki gdy faktycznie naciskałeś gaz (TPS do 46.7 %, RPM do 4232). Po prawidłowej filtracji do **stabilizowanego idle** (TPS przy podłodze closed-throttle, RPM 550–850, ECT > 75 °C, ciągłe okna ≥ 3 s):

- mediana RPM = **653** (cel ~700 dla EJ253)
- std RPM = **37** (warn-band: lekkie wahania, prawdopodobnie AC + alternator load steps; nie hunting)
- n = 230 stabilizowanych próbek

Silnik nie pulsuje dramatycznie. Lekkie szorstkie wahania ±37 RPM mieszczą się w granicach normalności dla 200k-km EJ253. Wycofuję narrację o adaptacji DBW po Clear Memory jako przyczynie — nic nie wymaga „adaptacji", bo nic się nie pulsuje.

### Co **pozostaje definitywnie potwierdzone**

| Fakt | Dowód |
|---|---|
| **Pod WOT na benzynie mieszanka uboga** | Lambda 1.02 (cel 0.85–0.92), STFT p95 +24 %, std 10.9 %, mean +9.4 % |
| **Pod WOT na LPG silnik zdrowy** | Lambda 0.99, STFT p95 +2.3 %, std 1.7 % |
| **Sonda przedkatowa B1 sprawna** | Ri ≈ 31 Ω — w idealnym zakresie roboczym dla LSU 4.9 |
| **Knock correction ≈ 0** | Brak ujemnych odejść w obu logach |
| **Idle ciepły zdrowy z lekką szorstkością** | mediana 653 RPM, std 37 RPM |

**Jedyny realny problem: dostarczanie benzyny pod dużym zapotrzebowaniem masowym** (WOT/wysokie obciążenie). Manometr w listwie paliwowej pod WOT to najtańsza i pierwsza weryfikacja. Szczegóły w rozdziale „Co zostaje jako problem" poniżej.

Dalsza część dokumentu (przed sprostowaniem) zawiera materiał edukacyjny o anatomii sondy lambda, układzie dolotowym i układzie paliwowym — pozostawiony bez zmian, bo wartość edukacyjna jest niezależna od mojej błędnej interpretacji konkretnych liczb.

---

## Słowniczek — co oznaczają skróty i pojęcia

| Skrót / pojęcie | Pełna nazwa polska | Co to jest |
|---|---|---|
| **ECU** | Elektroniczna jednostka sterująca, sterownik silnika | Komputer zarządzający pracą silnika |
| **SSM2** | Subaru Select Monitor 2 | Własny protokół diagnostyczny Subaru (nie jest to standardowe OBD-II) |
| **RPM** | Obroty na minutę | Prędkość obrotowa silnika |
| **STFT** | Krótkoterminowa korekta składu mieszanki | Wartość w %, o ile sterownik koryguje dawkę paliwa w danej chwili |
| **LTFT** | Długoterminowa korekta składu mieszanki | Wartość w %, wyuczona przez sterownik na przestrzeni dziesiątek minut jazdy |
| **Lambda (λ)** | Grecka litera λ, współczynnik nadmiaru powietrza | λ = 1,0 = stoichiometria (idealny skład), λ < 1 = bogata mieszanka, λ > 1 = uboga mieszanka |
| **Stoichiometria** | — | Idealny chemiczny stosunek powietrza do paliwa: dla benzyny 14,7 kg powietrza : 1 kg paliwa |
| **Sonda wideband / AFR** | Szerokopasmowa sonda składu mieszanki | Mierzy lambdę ciągłą, umieszczona przed katalizatorem |
| **Sonda narrowband** | Wąskopasmowa sonda składu mieszanki | Mierzy tylko czy mieszanka jest bogata lub uboga (przełącznik bogatej/ubogiej), za katalizatorem |
| **MAP** | Ciśnienie bezwzględne w kolektorze ssącym | Mierzone w kPa (kilopaskalach); na luzie przy zdrowym silniku ~25 kPa bezwzględnych (~−75 kPa podciśnienia) |
| **MAF** | Masowy przepływomierz powietrza | Mierzy ile powietrza wchodzi do silnika w gramach na sekundę (g/s) |
| **ECT** | Temperatura cieczy chłodzącej silnik | Mierzone w °C; pętla zamknięta aktywna powyżej ok. 70 °C |
| **IAT** | Temperatura powietrza dolotowego | Mierzone w °C; wysoka IAT = mniejsza gęstość powietrza |
| **TPS / DBW** | Czujnik położenia przepustnicy / elektroniczna przepustnica | W EJ253 przepustnica jest sterowana elektronicznie, bez linki mechanicznej |
| **DFCO** | Odcięcie wtrysku przy zwalnianiu | Sterownik wyłącza wtrysk paliwa przy zamkniętej przepustnicy i obrotach >1300 RPM, np. podczas hamowania silnikiem |
| **PCV** | Zawór kontroli wydmuchu skrzyni korbowej (zawór gases-blow-by) | Element wentylacji oparów olejowych — obowiązkowe połączenie między pokrywą zaworową a kolektorem ssącym |
| **FPR** | Regulator ciśnienia paliwa | Utrzymuje stałe ciśnienie w listwie wtryskiwaczy (~3,4 bara) |
| **FKL / FBKC** | Uczenie wyprzedzenia zapłonu / korekcja stuku | FKL = wartość wyuczona (długoterminowa), FBKC = chwilowe cofnięcie przy stuku |
| **AVCS** | System zmiennych faz rozrządu Subaru | Elektryczno-hydrauliczny system na wałku rozrządu ssącym, działa jak VVT |
| **VVT** | Zmienny rozrząd | Ogólna nazwa systemów zmiany faz rozrządu w różnych markach |
| **Smoke test** | Test dymem | Wpompowanie dymu pod ciśnieniem do układu dolotowego w celu znalezienia nieszczelności |
| **Odchylenie standardowe (std)** | Standard Deviation | Miara rozrzutu wartości — opisana szczegółowo poniżej |
| **Open loop / Closed loop** | Pętla otwarta / zamknięta | CL = sterownik koryguje dawkę paliwa na bieżąco wg sygnału sondy lambda; OL = stała mapa bez korekty |
| **Bank / rząd cylindrów** | — | Opisany szczegółowo w rozdziale poniżej |

---

## Czym jest „odchylenie standardowe RPM" — czyli co naprawdę znaczy std = 367

**Odchylenie standardowe** to **miara tego o ile dane wartości różnią się od swojej średniej**. To nie jest wartość obroty na minutę silnika — to informacja o tym, jak bardzo obroty skakały.

### Przykład praktyczny

Wyobraź sobie, że ktoś mierzy strzały do tarczy. Średnia trafia w środek. Odchylenie standardowe mówi — jak daleko od środka rozrzucone są trafienia.

Dla obrotów silnika na luzie (średnia ≈ 700 RPM):

| Wynik std | Co to znaczy fizycznie | Jak to odczuwa kierowca |
|---|---|---|
| std < 25 RPM | Obroty wahają się między 675 a 725 RPM | Praktycznie nieodczuwalne — igła obrotomierza stoi w miejscu |
| std = 41 RPM | Obroty wahają się między ~659 a ~741 RPM | Lekkie drgania, silnik pracuje nieco szorstko |
| **std = 367 RPM** | **Obroty wahają się między ~333 a ~1067 RPM** | **Silnik dosłownie gaśnie i przyspiesza w rytm — igła obrotomierza chodzi jak wahadło** |

**Twoje wyniki:**
- Log LPG: std = **41 RPM** → szorstkie, ale stabilne jałowe obroty (charakterystyczne dla zużytych wtrysków LPG Stag)
- Log benzyna (po skasowaniu pamięci): std = **367 RPM** → silnik pulsował dramatycznie, prawie gasło

Zjawisko to po angielsku nazywa się **idle hunting**, co dosłownie przetłumaczyć można jako **„polowanie na biegu jałowym"** — silnik szuka stabilnego punktu pracy i nie może go znaleźć, więc obroty wędrują góra-dół. To jest bardzo wymowna nazwa.

**Skąd std = 367 akurat po skasowaniu pamięci?** Elektroniczna przepustnica uczy się przez dziesiątki minut jazdy, ile dokładnie powinna się otworzyć na biegu jałowym. Po skasowaniu tej nauki (procedura Clear Memory) sterownik wraca do fabrycznej wartości środkowej — która może nie pasować do stanu Twojego silnika — i przez kilkadziesiąt minut poprawia (adaptuje). Dramatyczne pulsowanie po Clear Memory jest spodziewane, jednak ustąpienie trwa 30–60 minut jazdy. Jeśli nie ustępuje po kilku dniach normalnej jazdy — jest problem mechaniczny.

---

## Układ cylindrów i bankowania w EJ253 — co to Bank 1, Bank 2 i skąd Bank 3

### Miałem rację zauważając niespójność — wyjaśniam to raz konkretnie

**EJ253 to silnik bokser 4-cylindrowy** (zwany też flat-4 lub H4). Oznacza to, że cylindry leżą poziomo w dwóch szeregach, po dwa z każdej strony:

```
   Przód samochodu
   ┌──────────────┐
   │   cyl. 1     │ ← prawa strona (pasażer)    → BANK 1
   │   cyl. 3     │ ← prawa strona (pasażer)    → BANK 1
   │──────────────│
   │   cyl. 2     │ ← lewa strona (kierowca)    → BANK 2
   │   cyl. 4     │ ← lewa strona (kierowca)    → BANK 2
   └──────────────┘
```

W numeracji Subaru:
- **Cylinder 1**: z przodu, po prawej stronie samochodu (strona pasażera)
- **Cylinder 2**: z przodu, po lewej stronie (strona kierowcy)
- **Cylinder 3**: z tyłu, po prawej stronie
- **Cylinder 4**: z tyłu, po lewej stronie

**Bank 1** = prawa strona = cylindry 1 i 3
**Bank 2** = lewa strona = cylindry 2 i 4

### Dlaczego w SSM2 widzisz kolumny #1, #2, #3, #4 dla STFT i LTFT?

Protokół SSM2 Subaru obsługuje różne silniki z jednego systemu. Firma Subaru produkuje:
- Silniki **H4** (4-cylindrowe): EJ25, EJ20 — mają **2 banki (1 i 2)**
- Silniki **H6** (6-cylindrowe): EZ30, EZ36 — mają **4 banki (1, 2, 3, 4)**

Dlatego SSM2 zawsze zawiera 4 kanały dla korekcji mieszanki (#1, #2, #3, #4). Na Twoim 4-cylindrowym EJ253:

| Kanał SSM2 | Odpowiedź w EJ253 |
|---|---|
| Air/Fuel Correction #1 (STFT Bank 1) | **Aktywny** — prawa strona (cyl. 1, 3) |
| Air/Fuel Correction #2 (STFT Bank 2) | **Aktywny** — lewa strona (cyl. 2, 4), ale na EJ253 bez osobnej sondy jest sprzężony z Bank 1 |
| Air/Fuel Correction #3 (STFT Bank 3) | **Zero** — tylko dla 6-cylindrowych |
| Air/Fuel Correction #4 (STFT Bank 4) | **Zero** — tylko dla 6-cylindrowych |

### To co reprezentuje prawa strona cylindrów (cyl. 2 i 4)?

To jest właśnie **Bank 2** — lewa strona (z perspektywy siedzącego kierowcy). Pomyłka w mojej poprzedniej wypowiedzi: napisałem, że Bank 3 to spuścizna po silnikach 6-cylindrowych — **to prawda dla kanałów #3 i #4**, natomiast błędnie zasugerowałem, że na EJ253 jest tylko Bank 1. Są **dwa banki** (1 i 2), obie strony silnika. To, że w Twoim logu Bank 2 wygląda jak kopia Bank 1, wynika z faktu, że EJ253 SOHC NA (silnik bez doładowania) ma **jedną sondę lambda** przy zbiorniku spalin — oba banki są sterowane tym samym sygnałem.

---

## PROBLEM 1 — Sonda lambda przed katalizatorem (Ri = 31 Ω)

### Co pokazały logi

W obu logach (LPG i benzyna) parametr "Front O2 Sensor #1 Resistance" (odporność elektryczna sondy lambda #1) wynosi mediana **31 Ω**.

### Wcześniejszy błąd w analizatorze

Mój analizator zgłaszał przy tej wartości ostrzeżenie "sonda się starzeje" — to było błędne. **Przepraszam za dezinformację i corrector właśnie wprowadzony do kodu.**

### Jak działa sonda lambda wideband (szerokopasmowa)

Sonda wideband (producenci: Bosch LSU 4.9, Denso UEGO) jest zbudowana z **dwóch ceramicznych celek elektrochemicznych**:

**Celka pompująca (Pumping Cell, oznaczenie Ip):**
Dosłownie pompuje jony tlenu między komorą pomiarową a atmosferą. Prąd potrzebny do tego pompowania jest sygnałem informującym, o ile mieszanka odbiega od ideal (lambda 1,0). Przy mieszance ubogiej prąd jest dodatni, przy bogatej ujemny. Przy stoichiometrii prąd jest bliski zeru.

**Celka Nernsta (Nernst Cell, oznaczenie Vs):**
Generuje napięcie referencyjne stoichiometrii (jak w klasycznej sondzie narrowband). Sterownik porównuje z nią sygnał z celki pompującej.

**Grzałka:**
Sonda musi pracować w temperaturze około 750–800 °C, żeby ceramika przewodziła jony. Sterownik steruje grzałką elektronicznie, mierząc **impedancję elektryczną celki Nernsta (oznaczana Ri, w omach)**. Im gorąca sonda — tym niższa Ri.

### Czemu Ri = 31 Ω oznacza sondę ZDROWĄ, a nie starzejącą

| Stan sondy | Wartość Ri |
|---|---|
| Sonda zimna (silnik wyłączony) | Kilka kiloomów (kilkaset do kilkutysiąca Ω) |
| Sonda nagrzewana (pierwsze minuty pracy) | Stopniowo opada od setek Ω do kilkudziesięciu |
| **Sonda w pełni nagrzana, praca normalna** | **~30 Ω (Bosch LSU 4.9) lub ~80 Ω (niektóre sondy Denso)** |
| Sonda zestarzała, grzałka nie daje rady | Powoli rośnie powyżej 100–150 Ω przy normalnej pracy |

**Twoje 31 Ω podczas jazdy = sonda pracuje w idealnej temperaturze.** Nowa sonda miesiąc temu, Ri = 31 Ω = wszystko gra.

### Skąd więc nerwowe STFT na LPG?

Sprawca nerwowego STFT (wahania ±5% w czasie cruise) to **nie sonda**, a **wtryskiwacze LPG Stag** które klekoczą — każdy wtrysk powoduje drobne wahanie ciśnienia gazu, co przenosi się na niestabilną dawkę i natychmiastową reakcję sondy i sterownika.

### Co sprawdzić w złączu elektrycznym sondy

Masz rację wspominając o złączu. Sonda ma kilkupinowe złącze (najczęściej Bosch 4- lub 6-pinowe). Typowe miejsca problemów w Subaru:

1. **Korozja styków** — złącze jest blisko koła i kolektora wydechowego, woda po deszczu trafia w te rejon. Objaw: zielony nalot na stykach, wahania sygnału.
2. **Niedokręcona masa grzałki** — pin masy grzałki to oddzielny przewód, czasem montowany do karoserii. Poluzowanie = wolniejsze nagrzewanie = sonda wolniej wchodzi w pętlę zamkniętą = nerwowy STFT przez pierwsze minuty jazdy.
3. **Uszczypnięty przewód** podczas montażu — oplot wygląda dobrze, ale wewnątrz żyłki są pęknięte.

**Jak sprawdzić:** przy zimnym silniku, po odłączeniu akumulatora: miernikiem sprawdzić rezystancję grzałki sondy (dwa piny grzałki, wartość prawidłowa: 2–4 Ω). Jeśli powyżej 10 Ω lub brak ciągłości — grzałka uszkodzona. Wzrokowo sprawdzić złącze pod kątem korozji.

---

## PROBLEM 2 — Nieszczelność układu dolotowego (vacuum leak)

To jest temat, który powinienem był zidentyfikować jako pierwszy już przy pierwszej analizie. Przepraszam za to, że pojawiło się go "bokiem" w poprzedniej wypowiedzi. Rozkładam go tutaj w pełni.

### Co pokazał log benzyna — trzy liczby które razem tworzą jeden wzorzec

| Pomiar | Wartość z logu | Wartość prawidłowa dla EJ253 | Różnica |
|---|---|---|---|
| MAP (ciśnienie w kolektorze ssącym) | **33 kPa bezwzględne** | 22–28 kPa bezwzględne | Za wysoko o 5–10 kPa — słabsze podciśnienie |
| MAF (przepływ powietrza na biegu jałowym) | **3,89 g/s** | 2,5–3,5 g/s | Za dużo o 0,4–1,4 g/s |
| LTFT idle (długoterminowa korekta na luzie) | **−5,5 %** | ±3 % | Sterownik odejmuje paliwo |

Każdy z tych parametrów osobno mógłby mieć inne wyjaśnienie. Razem, **wszystkie trzy wskazują jednoznacznie na nieszczelność w układzie dolotowym za przepustnicą**.

### Skąd wiemy, że chodzi o nieszczelność — wyjaśnienie fizyczne

Silnik pracuje jak ogromna pompa — cylindry zasysają powietrze przy każdym takcie ssania. Przy zamkniętej przepustnicy (biegu jałowym) przez wąską szczelinę wchodzi tylko tyle powietrza ile potrzeba. Wytwarza to **podciśnienie w kolektorze ssącym** (ciśnienie jest niższe niż atmosferyczne, stąd słowo "vacuum" = próżnia).

Jeśli **gdzieś w kolektorze jest szczelina, pęknięcie lub poluzowany wąż** — po tej szczelinie wpada dodatkowe powietrze, którego przepływomierz MAF nie zmierzył. Cylindry dostają za dużo powietrza, mieszanka staje się uboga. Sterownik to widzi przez sondę lambda i reaguje:
- Podnosi ciśnienie w kolektorze (**MAP rośnie** — podciśnienie słabnie)
- **MAF rośnie** — przepustnica otwiera się szerzej, żeby dopasować się do wyższego RPM i przepływu przez uszczelkę
- **LTFT spada na minus** — sterownik długoterminowo odejmuje paliwo, bo mieszanka wychodzi bogata (paradoks: nieszczelność powietrzna, a sterownik odejmuje paliwo? Tak — bo z perspektywy ECU mierzy "za dużo MAF w stosunku do faktycznej energii spalania")

**Podciśnienie 33 kPa** oznacza, że ciśnienie w kolektorze jest tylko o 68 kPa niższe od atmosferycznego. Prawidłowo powinno być ok. 75–78 kPa niższe. To jakby silnik pracował z lekko otwartą przepustnicą cały czas — a tak właśnie odczuwa się nieszczelność.

### Mapa układu dolotowego EJ253 — gdzie typowo wycieka

```
[Filtr powietrza]
       │
       ▼
[Przepływomierz MAF]  ← mierzy g/s wchodzące TUTAJ
       │
       ▼
[Przepustnica DBW]    ← sterowana elektrycznie
       │
       ▼
[Kolektor ssący — z tworzywa sztucznego]
       │
   ┌───┴──────────────────────────────┐
   ▼                                  ▼
[Uszczelki pod ssawkami        [Wąż do wzmacniacza
 do głowic — 4 szt.]            hamulca]
   │                                  │
   ▼                                  ▼
[Zawór PCV]                    [Wąż FPR]
(wentylacja                    (referencja
 oparów olejowych)              ciśnienia)
   │
   ▼
[Wąż EVAP — purge solenoid]
(odświeżanie kanistra węgla aktywnego)
```

**Każde z tych połączeń, jeśli nieszczelne, daje się wciągnąć do kolektora powietrze omijające MAF.**

### Punkty nieszczelności w kolejności prawdopodobieństwa dla 200 000 km Subaru

**1. Wąż PCV (zawór kontroli wydmuchu)**

Co to jest: Przy pracy silnika w cylindrach powstają gazy przeddmuchowe — spaliny i pary olejowe które przebijają się przez pierścienie tłokowe do skrzyni korbowej. Gdyby je tam zamknąć, skrzynia korbowa byłaby pod ciśnieniem i olej zaczęłoby wypchnąć uszczelkami. Dlatego te gazy są odprowadzane do kolektora ssącego przez zawór PCV i tam spalane.

Skąd wyciek: Wąż gumowy łączący pokrywę zaworów z kolektorem twardnieje z wiekiem, pęka szczególnie przy złączkach. Po 150 000+ km jest to bardzo częsta usterka.

Jak sprawdzić wzrokowo: odszukać gruby gumowy wąż idący z pokrywy zaworów do kolektora ssącego, sprawdzić czy gumowe końcówki nie są popękane.

**2. Uszczelki kolektora ssącego**

Co to jest: Kolektor ssący (plastikowy) jest przymocowany do obu głowic (lewa i prawa strona silnika). Na każdym porcie ssącym (4 cylindry = 4 porty) jest uszczelka — gumowy o-ring lub uszczelka papierowa. Po wielu cyklach termicznych (rozgrzanie/ostudzenie przez 200 000 km) pękają lub tracą sprężystość.

Jak sprawdzić: smoke test lub test sprayem (patrz niżej).

**3. Wąż wzmacniacza hamulca**

Co to jest: Wzmacniacz hamulca (servo) działa właśnie dzięki podciśnieniu w kolektorze ssącym. Gruby czarny wąż idzie od kolektora przez jednokierunkowy zawór zwrotny do servo. Jeśli pęka lub wychodzi ze złączki — wpada do kolektora duże niekontrolowane powietrze.

Dodatkowy objaw oprócz lambda: pedał hamulca robi się "twardy" i ciężki.

**4. Wąż regulatora ciśnienia paliwa (FPR)**

Co to jest: W niektórych wersjach EJ253 regulator ciśnienia paliwa ma referencję podciśnienia — cienki wąż łączy go z kolektorem. Pęka często u końców.

Jak sprawdzić: wzrokowo, cienki wąż przy listwie wtryskiwaczy lub FPR.

**5. Solenoid purge (odświeżania kanistra węgla aktywnego — EVAP)**

Co to jest: Opary benzyny ze zbiornika trafiają do kanistra z węglem aktywnym (filtr pochłaniający opary). Co pewien czas sterownik otwiera solenoid i opary są zasysane do kolektora i spalane. Jeśli solenoid jest zacięty w pozycji otwartej — do kolektora płynie ciągły strumień powietrza i oparów paliwa.

Dodatkowy objaw: sporadyczny zapach benzyny w przestrzeni silnika.

**6. Uszczelka pod przepustnicą DBW**

Co to jest: platka przepustnicy wkręca się pierścieniem w kolektor. Uszczelka gumowa między nimi może pęknąć po odkręceniu (np. przy czyszczeniu przepustnicy).

**7. Popękana pokrywa zaworów lub uszczelka VVT/AVCS**

Co to jest: solenoid AVCS wkręcony jest w pokrywę zaworów. Jego uszczelka gumowa może przepuszczać powietrze przez przewody odpowietrzania.

### Jak zlokalizować wyciek — metody od najtańszej

**Metoda 1 — Smoke test w warsztacie (100–150 zł)**

Najdetektywiniejsza metoda. Warsztat zatyka wlot powietrza za MAF, wpompowuje pod małym ciśnieniem dym. Wycieka widać gołym okiem. Zajmuje 15 minut, zdecydowanie polecam.

**Metoda 2 — Test sprejem/propan (DIY, koszt: puszka WD-40 lub propanu)**

Przy pracującym silniku na biegu jałowym, spryskujesz po kolei każde podejrzane goldacze. Jeśli w danym miejscu jest wyciek powietrza, silnik wciągnie butane/propan przez nieszczelność → mieszanka chwilowo wzbogaci się → obroty na chwilę wzrosną → masz znaleziony wyciek.

**Uwaga bezpieczeństwa:** pracujący silnik + otwarty ogień = pożar. Używać propanu w małych dawkach, mieć gaśnicę w zasięgu. Osoby bez doświadczenia niech oddadzą auto do warsztatu.

**Metoda 3 — Wzrokowa**

Przy wyłączonym silniku przejrzeć każdy gumowy wąż na kolektorze ssącym. Pęknięcia często widać gołym okiem — guma popękana, białe ślady spękań na czarnym tle.

---

## PROBLEM 3 — Niewystarczające dostarczanie paliwa benzyna pod pełnym obciążeniem

### Co pokazał log benzyna

Przy pełnym wciśnięciu pedału gazu (faza WOT — Wide Open Throttle, pełna przepustnica), na silniku atmosferycznym wymagana jest bogata mieszanka (lambda ok. 0,85–0,88) dla ochrony silnika i maksymalnej mocy:

| Pomiar | Wartość z logu | Wartość prawidłowa | Stan |
|---|---|---|---|
| Lambda przy pełnym gazie | **1,02** | 0,85–0,88 | Uboga — 1,02 zamiast 0,87 to błąd o 17% |
| STFT p95 przy pełnym gazie | **+24,2 %** | max −10 do +5 % | Sterownik na granicy korekcji |
| STFT średnia przy pełnym gazie | **+9,4 %** | <+5 % | Silnik woła o paliwo |
| STFT odchylenie standardowe | **10,9 %** | <3 % | Korekta nie może ustabilizować |

"p95" oznacza wartość 95. percentyla — 95% pomiarów było poniżej +24,2%. Czyli prawie cały czas przy pełnym gazie STFT był powyżej normy.

**Co to oznacza w języku zrozumiałym:** sterownik silnika próbuje dodać paliwo bo widzi ubogą mieszankę (lambda 1,02), ale wpompowuje go do granic swoich możliwości (limit autorytetu sterownika Subaru to typowo ±25% dla STFT) i nadal nie jest w stanie wzbogacić mieszanki do wymaganej wartości. Benzyna po prostu **nie przybywa wystarczająco szybko**.

### Jak działa układ zasilania benzyną w EJ253

```
[Zbiornik paliwa]
       │
       ▼
[Elektryczna pompa paliwa]  ← montowana wewnątrz zbiornika, ciśnienie nominalne ~3,4 bara
       │
       ▼
[Filtr paliwa]  ← na starszych Subaru wymienialny, na nowszych wewnątrz modułu pompy (tzw. "lifetime")
       │
       ▼
[Listwa wtryskiwaczy]  ← 4 wtryskiwacze, jeden na każdy cylinder
       │
       ▼
[Regulator ciśnienia paliwa (FPR)]  ← utrzymuje stałe ciśnienie 3,4 bara
```

### Prawidłowe parametry układu paliwowego benzyna

- **Ciśnienie przy wyłączonym silniku, kluczyk w pozycji ON** (pompa prymuje): **3,4 bara / 340 kPa**
- **Ciśnienie na biegu jałowym**: 3,0–3,4 bara
- **Ciśnienie przy pełnym gazie**: **stabilne 3,4 bara** — jeśli spada o więcej niż 0,3 bara, pompa lub filtr nie wyrabia
- **Utrzymanie ciśnienia po wyłączeniu silnika**: nie powinno spaść o więcej niż 0,5 bara w ciągu 5 minut (sprawdza szczelność wtrysków i zaworu pompy)

### Co się najczęściej psuje

**1. Filtr paliwa benzynowego**

Zatyka się stopniowo przez 100–150 000 km jazdy. U Ciebie — po latach jazdy duet benzyna+LPG — benzyna **pracuje w układzie dużo krócej niż powinna** (auto jeździ głównie na LPG). Filtr może być stary, bo nie był wymieniany liczac na to, ze "benzyna mało jedzie". Wymiany: ok. 50–100 zł za filtr.

**2. Pompa paliwa**

Po 200 000+ km zaczyna tracić wydajność szczególnie pod obciążeniem. Na wolnych obrotach i trasie dysze sobie — przy konieczności dostarczenia dużej ilości paliwa pod WOT nie wyrabia. Objaw charakterystyczny: silnik jest słabszy przy przyspieszaniu od wyższych prędkości (np. 100–130 km/h WOT) niż przy przyspieszaniu z miejsca. Pompa w Subaru jest montowana w module w zbiorniku — wymiana kosztuje 400–1200 zł (zależnie od oryginał vs zamiennik).

**3. Wtryskiwacze benzyna po długiej pracy głównie na LPG**

Wtryskiwacze benzynowe w samochodzie z instalacją LPG przez większość czasu stoją bezczynne. Benzyna w nich **wysycha i zostawia osad** (lakier). Po kilku latach benzyna jest wtryskiwana przez połowicznie zatkane dysze, z mniejszym przepływem. Objaw: nierównomierna praca, szczególnie przy pełnym gazie gdy wtrysk jest bardzo intensywny.

**Twoja sytuacja jest podręcznikowym przypadkiem** tego problemu: kilka lat LPG, długoterminowe stanie benzyny w wtryskach = osad.

**4. Zużyte styki przekaźnika pompy paliwa (relay)**

Przekaźnik elektromagnetyczny steruje pompą paliwa. Wypalony styk powoduje **spadek napięcia zasilania pompy pod obciążeniem** — pompa kręci się słabiej i nie tłoczy dostatecznie. Sprawdzenie: oscyloskop lub miernik napięcia na pompie przy WOT (powinno być >12 V ciągle).

### Co sprawdzić w kolejności

1. **Wymiana filtra paliwa** — najtańszy ruch, jeśli nie był wymieniany od dawna (filtr inline jeśli jest, lub zalecenie warsztatu co do stanu siatki w module pompy)
2. **Pomiar ciśnienia w listwie wtryskiwaczy przy WOT** — warsztat podłącza manometr na adapter w listwie. Jazda próbna z manometrem. Spadek przy pełnym gazie = pompa lub zatkany filtr
3. **Czyszczenie ultradźwiękowe wtrysków benzyna** — warsztat demontuje, czyści, mierzy przepływ i atomizację. Komplet 4 sztuk 300–500 zł + diagnostyka
4. **Wymiana wtrysków** — jeśli czyszczenie nie dało efektu (komplet używanych ok. 400 zł, nowych ok. 1500 zł)

---

## PROBLEM 4 — Pulsujące obroty biegu jałowego (idle hunting) po skasowaniu pamięci

Szczegółowo wyjaśnione powyżej w rozdziale o odchyleniu standardowym.

**Podsumowanie:**
- Log benzyna po Clear Memory: std = 367 RPM → silnik pulsował między ~333 a ~1067 RPM
- Po pełnej adaptacji przepustnicy DBW (~50 km mieszanej jazdy) std powinno spaść poniżej 50 RPM
- Jeśli nie spada nawet po tygodniu normalnej jazdy → przyczyną jest problem mechaniczny (nieszczelność lub brudna przepustnica)

**Anatomia elektronicznej przepustnicy Subaru (DBW):**

W EJ253 nie ma linki przepustnicy. Pedał gazu **jest tylko sensorem** (dwa niezależne napięcia = podwójna redundancja). Sterownik sam decyduje ile otworzyć przepustnicę. Zaletą jest precyzyjna kontrola biegu jałowego — sterownik sam reguluje obroty dostosowując otwarcie przepustnicy.

Adaptacja (uczenie) przepustnicy na biegu jałowym polega na tym, że sterownik zapisuje: "przy tej temperaturze silnika + ten stan klimatyzacji + ta pozycja skrzyni → otwórz przepustnicę na X procent". Ta tabela jest budowana przez kilkadziesiąt minut jazdy w różnych warunkach.

**Procedura relearn po wymianie/czyszczeniu przepustnicy lub Clear Memory:**
1. Kluczyk w pozycji ON (nie starter), poczekaj 30 s
2. Wyłącz zapłon
3. Powtórz 3 razy
4. Uruchom silnik i poczekaj na stabilizację obrotów ~10 min

**Co się typowo psuje w układzie biegu jałowego:**
1. **Nieszczelność dolotowa** (patrz Problem 2) — sterownik nie może ustabilizować obrotów bo przepływ powietrza jest chaotyczny
2. **Brudna przepustnica** — osad z olejów PCV + kurz. Mechaniczne otwieranie "klei się". Czyszczenie środkiem B12 lub CRC po zdemontowaniu jednostki
3. **Zużyte świece zapłonowe** lub **słabe cewki** — misfire na jednym cylindrze powoduje drgania na biegu jałowym nieodróżnialne od vacuum leak; po wymianie świec często ustępuje samoistnie
4. **Zanieczyszczona sonda MAP** — fałszywe odczyty

---

## PROBLEM 5 — Wyuczone wyprzedzenie zapłonu przeniesione z LPG na benzynę 95

### Co pokazał log

Parametr "Ignition – Knock Correction" (korekcja zapłonu, stosownie FKL — Fine Knock Learning = wyuczone wyprzedzenie):
- Wartość p95 w fazach obciążenia: **+6,0°**
- Oznacza to, że sterownik wyuczył się dodawać 6 stopni wyprzedzenia zapłonu do bazowej mapy

### Jak działa mapa zapłonu w Subaru

Sterownik EJ253 zarządza chwilą zapłonu dwoma tabelami:

**Tabela bazowa:** fabryczna, kalibrowana na benzynę 95-oktan. To jest "bezpieczne minimum" — może od razu zapalać wcześniej, ale ryzykuje stuk, więc jest konserwatywna.

**Tabela wyuczonego wyprzedzenia (FKL — Fine Knock Learning):** modyfikator do tabeli bazowej. Sterownik co kilkadziesiąt minut jazdy sprawdza: "w tej komórce RPM × obciążenie nie słyszę stuku — mogę dodać 1,4° wyprzedzenia". Robi to komórka po komórce, przez wiele godzin jazdy, aż zbuduje optymalne wyprzedzenie dla Twojego konkretnego paliwa.

**Na LPG:** autogaz propan-butan ma wyższą liczbę oktan (około 100–110 MON dla propanu) niż benzyna 95. Sterownik nigdy nie słyszy stuku przy LPG → FKL systematycznie rośnie → po tygodniach jazdy na gazie FKL osiąga +6 do +8° w komórkach obciążeń.

**Problem po Clear Memory i przejściu na benzynę 95:** Clear Memory kasuje FKL, ale tylko jeśli procedura obejmuje kasowanie adaptacji (nie tylko DTC). W Twoim logu po Clear Memory FKL już wynosi +6° po 17 minutach jazdy. Dwie możliwości:

1. FKL nie zostało wyzerowane — Clear Memory w FreeSSM/SSM2 nie zawsze kasuje wszystkie adaptacje (DTC = błędy kasowane na pewno; FKL bywa w innej partycji pamięci sterownika)
2. W ciągu tych 17 minut jazdy (spokojna trasa, brak stuku) sterownik zdążył odbudować +3 do +6° w komórkach cruise

### Ryzyko praktyczne

+6° na benzynie 95 przy **zbieżnym problememie ubogiej mieszanki pod WOT** tworzy warunki na detonację:
- Uboga mieszanka (lambda 1,02 zamiast 0,87) = wolniejsze spalanie, temperatura spalin wyższa
- Za duże wyprzedzenie zapłonu = zapłon przed osiągnięciem TDC, ciśnienie narasta zanim tłok zakończy suw sprężania
- Wynik: stukanie silnika, uszkodzenie panewek korbowodów przy dłuższym działaniu

**Dobra wiadomość:** w Twoich logach "Active Knock Retard" (chwilowe cofnięcie przy stuku) wynosi maks. −0,5° — czyli sterownik chwilowo korygował, detonacja nie była intensywna. Jednak naprawienie problemu paliwa JEST PILNE.

### Co zrobić

1. Sprawdzić w SSM2 procedurę pełnego reset adaptacji (nie tylko "Clear Codes" ale też "Clear Learning Values")
2. Po naprawie vacuum leak i układu paliwowego: **2–3 pełne baki benzyny 98** przy wyłączonym LPG — pozwala FKL re-nauczyć marginesu bezpieczeństwa na paliwie 98
3. Następnie log WOT na 98: lambda powinna wrócić do 0,85–0,88, FKL po 200 km jazdy zbliżać się do 0 lub małych wartości dodatnich

---

## WYNIKI LOG LPG — zdrowy tor gazowy

Dla porównania — log na LPG pokazuje zdrowy silnik na właściwym paliwie:

| Parametr | Wynik | Ocena |
|---|---|---|
| Lambda przy WOT | 0,99 | Prawidłowe — LPG nie wymaga tak bogatej mieszanki jak benzyna |
| STFT p95 przy WOT | +2,3 % | Sterownik spokojny, paliwo dostarczone |
| Przepływ MAF na biegu jałowym | 2,85 g/s | W normie dla EJ253 |
| Podciśnienie w kolektorze | 25 kPa bezwzgl. | W górnym zakresie normy, ale OK |
| LTFT biegu jałowego | −5,5 % | Graniczny minus — wtryski LPG seepują nieco na benzyny |
| TPS — korelacja tor główny/zapasowy | r = 1,000 | Idealna redundancja — przepustnica zdrowa |
| Pedał — korelacja tor główny/zapasowy | r = 1,000 | Idealna redundancja — czujnik pedału zdrowy |
| MAF napięcie vs g/s | r = 0,973 | Spójność sensora prawidłowa |
| Alternator podczas jazdy | 14,0 V | Ładowanie prawidłowe |
| Temperatura oleju vs cieczy | ECT 82°C, olej 85°C | Różnica −3°C — zdrowy silnik |
| Katalizator (sonda za katem) | Aktywna 25,4 % bogato | Katalizator pracuje |

**Wniosek z logu LPG:** silnik mechanicznie jest w bardzo dobrym stanie. Jedyny aktywny problem to klekoczące wtryski Stag (odchylenie std obrotów 41 RPM = clattering) oraz minimalnie nerwowe STFT w cruise (~5% std). Instalacja LPG **doskonale dostarcza paliwo pod pełnym obciążeniem** — żaden problem z WOT przy jeździe na gazie.

---

## Synteza — dwa niezależne problemy, hierarchia napraw

### Tor LPG (stabilny, naprawy planowe)

```
[Problem A-LPG]  Klekot wtrysków Stag
         ↓
  Wymiana wtrysków gazu (planowo)
  Wtryski Stag po ok. 150 000 km gazu tracą
  sprężyny lub dysze — klikają mechanicznie
  przy każdym wtrysku, powodując
  idle std 41 RPM i STFT std 5%
```

### Tor benzyna (dwa niezależne problemy, oba wymagają diagnostyki)

```
[Problem B-benzyna-1]   NIESZCZELNOŚĆ DOLOTOWA
  Sygnatura: MAP 33 kPa / MAF 3,89 g/s /
             LTFT idle −5,5%
         ↓
  PILNE: Smoke test
  Najczęstsze miejsca: wąż PCV,
  uszczelki kolektora, wąż boostera

[Problem B-benzyna-2]   ZA MAŁO PALIWA POD PEŁNYM GAZEM
  Sygnatura: lambda 1,02 WOT /
             STFT p95 +24,2%
         ↓
  1. Wymiana filtra paliwa (jeśli >100k km od ostatniego)
  2. Pomiar ciśnienia przy WOT (manometr)
  3. Czyszczenie/wymiana wtrysków benzyna
     (stały osad po wielu latach LPG)

[Problem B-benzyna-3]   WYPRZEDZENIE ZAPŁONU Z NAUKI NA LPG
  Sygnatura: FKL p95 +6° na benzynie 95
         ↓
  Samo niebezpieczne w połączeniu z B-benzyna-2
  Rozwiązanie: pełny reset adaptacji + 2 baki 98
  po naprawie B i C
```

### Sugerowana kolejność działań

| Krok | Czynność | Priorytet |
|---|---|---|
| 1 | Smoke test układu dolotowego | PILNY — najtańszy, odpowiada na Problem B-1 |
| 2 | Wymiana filtra paliwa benzynowego | Niedrogi, profilaktyczny |
| 3 | Pomiar ciśnienia paliwa przy WOT | Diagnoza — warsztat lub DIY manometr |
| 4 | Czyszczenie ultradźwiękowe wtrysków benzyna | Odpowiada na Problem B-2 |
| 5 | Pełny reset adaptacji + 2 baki benzyny 98 | Po naprawie 1–4 |
| 6 | Log kontrolny na benzynie | Weryfikacja skuteczności napraw |
| 7 | Wymiana wtrysków LPG Stag | Planowo — niezależnie od benzyny |

---

*Dokument wygenerowany na podstawie logów FreeSSM i analizy `tools/log-analyzer/analyze.py`. Data: kwiecień 2026.*
