# Przegląd diagnostyczny – sprostowanie i panel ekspercki

Data: 2026-04-27  
Auto: Subaru z silnikiem **EJ253** (2.5 l, R4 boxer, SOHC, AVCS, DBW – *drive-by-wire*, czyli elektroniczna przepustnica), instalacja **LPG** sekwencyjna typu Stag.  
Zestaw danych: dwa logi z FreeSSM/SSM2 (Subaru Select Monitor 2 – własny protokół Subaru, **nie** standardowe OBD-II):
- `FreeSSM_log2.csv` – jazda na LPG (1772 próbki)
- `FreeSSM_log_cleared_memory_cold_start_gasoline_only.csv` – jazda na benzynie po skasowaniu pamięci adaptacji (1714 próbek)

---

## 1. Sprostowania – gdzie się myliłem

### 1.1 „EJ253 ma tylko jeden bank” – ostateczna i poprawna wersja

W tym dokumencie wcześniej napisałem niedbale, że Subaru raportuje banki osobno i pokazałem listę adresów SSM2 (B1/B2/B3/B4). To było zgodne z literą protokołu, ale **mylące merytorycznie**. Po dyskusji z Michałem prostuję raz a dobrze:

**Bank silnika to konstrukt układu kontroli, nie konstrukt geometryczny.** Bank istnieje wtedy, gdy ECU ma dla niego **osobną szerokopasmową sondę przedkatową i osobną pętlę regulacji**. V6/V8 mają osobne kolektory wydechowe i osobne sondy → mają B1 i B2.

**EJ253 NA (wolnossący) ma jedną zbiorczą sondę przedkatową** za Y-pipe (cztery rury z głowic schodzą się w jeden kolektor) → ECU widzi już zmieszane spaliny → fizycznie **nie ma możliwości rozróżnić** mieszanki z lewej i prawej głowicy. Z punktu widzenia regulacji to **jeden bank**. Sloty B2/B3/B4 w protokole istnieją w bibliotece, ale w tej kalibracji są niewykorzystane.

W Twoim CSV:

| Sygnał | Min | Maks | Niezerowych | Status |
|---|---|---|---|---|
| LTFT B1 | −10.9 % | +1.6 % | 534 / 1714 | **realny kanał** |
| STFT B1 | −10.2 % | +26.6 % | 703 / 1714 | **realny kanał** |
| LTFT B3 | 0.0 | 0.0 | 0 / 1714 | **placeholder** (zawsze 0) |
| STFT B3 | −2.5 % | +2.5 % | 898 / 1714 | **mikro-trim, nie bank** (skala ±2.5 %, inna natura) |

**Twoje ECU loguje JEDEN realny kanał korekt: B1.** Analizator v3 wykrywa placeholdery (`detect_placeholder_channels`) i pomija je w punktacji oraz w wykrywaniu zdarzeń.
- `Fuel Trim – LTFT B3`, `STFT B3` – **B3, nie B2**
- `O2 – Pre-Cat B1 Lambda/Current/Resistance` – tylko B1

Statystyka korekt z logu benzynowego (1714 próbek):

| Sygnał | Min | Maks | Niezerowych | Wniosek |
|---|---|---|---|---|
| LTFT B1 | −10.9 % | +1.6 % | 534 / 1714 | **aktywny, ujemny offset** |
| STFT B1 | −10.2 % | +26.6 % | 703 / 1714 | **aktywny, duże dodatnie skoki** |
| LTFT B3 | 0.0 % | 0.0 % | 0 / 1714 | **placeholder, kanał nieaktywny** |
| STFT B3 | −2.5 % | +2.5 % | 898 / 1714 | **inny sygnał, mała skala (±2.5 %), nie druga strona silnika** |

**Definitywny wniosek:**
- W Twoim aucie ECU raportuje **jeden zestaw realnych korekt paliwowych: B1**.
- Kanał B3 jest „kosmetyczny”: LTFT B3 jest stale zerowe, STFT B3 to ograniczony do ±2.5 % sygnał o innej naturze (prawdopodobnie wewnętrzny mikro-trim albo odczyt rezerwowy nieobsadzony w tej kalibracji – nie mam pewności bez zrzutu definicji ROM).
- **Dla rozumowania diagnostycznego pomijamy B3.** Jedyny rzeczywisty kanał korekt to **B1 i on dotyczy całego silnika** (oba banki głowic boksera, sumowane przez wspólną sondę przedkatową).

To zarazem tłumaczy dlaczego od początku patrzyłem na jedną stronę: bo **w Twoim aucie ECU widzi i raportuje jedną stronę**. Ale moje wyjściowe sformułowanie („H4 ma tylko B1”) było błędne i się do niego nie wracam.

### 1.3 „Falowanie obrotów na biegu jałowym 367 RPM”
**Błąd metodologiczny.** Sprawdziłem co naprawdę robił mój klasyfikator faz:

```
Fazy „IDLE” w analizatorze (n=329):
  RPM:  min=233, mediana=670, maks=4232, std=367
  TPS:  mediana=2.7 %, maks=46.7 %
  ECT:  77–84 °C
```

Maksymalny TPS (*throttle position sensor*, czujnik położenia przepustnicy) **46.7 %** i RPM do **4232** w fazie nazwanej „idle” – to **kompromitacja klasyfikatora**, nie silnika. Wpuściłem do worka „idle” próbki gdy faktycznie naciskałeś gaz albo silnik zgasł.

Po przefiltrowaniu na **prawdziwy ciepły bieg jałowy** (ECT > 75 °C, TPS od 0.1 do 2.7 %, RPM 400–1200, n=192):

| Statystyka | Wartość |
|---|---|
| RPM minimum | 579 |
| RPM p10 | 643 |
| **RPM mediana** | **651** |
| RPM p90 | 682 |
| RPM maksimum (jeden skok) | 1182 |

**Rozrzut p10–p90 = 39 RPM**. To jest **wzorcowe, zdrowe idle** ciepłego EJ253. Nie ma żadnego falowania. **Wycofuję alarm „idle hunting”.**

### 1.4 Dodatkowo wyjaśnienie offsetu TPS

Najniższe wartości TPS w tym logu poza zerem (zero = silnik zgaszony) to **2.0 % – 2.7 %**. To znaczy, że Twoje DBW raportuje „przepustnica zamknięta = ok. 2.5 %”. Klasyfikator zakładał TPS < 1 % = idle, dlatego zachowywał się idiotycznie. **To moja kalibracja jest do poprawki, nie Twoje auto.** Poprawka: idle = TPS < (TPS_min + 0.5 pp) lub progresywnie wykryty „closed throttle floor”.

---

## 2. Co JEST definitywnie potwierdzone w danych

Zostawiam tylko to, czego nie da się obalić – z dwoma niezależnymi metrykami:

| Stwierdzenie | Dowód | Powtarzalność |
|---|---|---|
| **Pod pełnym otwarciem przepustnicy (WOT, *wide-open throttle*) na BENZYNIE mieszanka jest UBOGA** | Lambda B1 mediana w WOT ≈ **1.02** (powinno być 0.85–0.92), STFT B1 p95 = **+24 %**, std STFT = 10.9 % | Potwierdzone niezależnie przez analizę ChatGPT i przez ten analizator |
| **Pod WOT na LPG silnik jest zdrowy** | Lambda B1 ≈ **0.99**, STFT B1 p95 = **+2.3 %**, std STFT 1.7 % | Ten sam silnik, ten sam log narzędzia, inna przewód paliwowy |
| **Sonda przedkatowa B1 (LSU 4.9 lub odpowiednik szerokopasmowy) jest sprawna** | Rezystancja R ≈ 31 Ω, mieści się w zdrowym zakresie roboczym ogrzewania (typowo 8 – 200 Ω) | Spójna w obu logach |
| **Korekta zapłonu od stuku (Knock Correction) ≈ 0** | Brak ujemnych odejść | Spójne w obu logach |
| **Idle ciepłe jest stabilne** | RPM p10–p90 swing 39 RPM przy medianie 651 | Tylko log benzynowy zawierał takie próbki, ale w sposób jednoznaczny |

**Wniosek z porównania krzyżowego paliw:**  
Skoro **ten sam silnik** zachowuje się dobrze na LPG i źle pod WOT na benzynie, to mechanika silnika (kompresja, zawory, AVCS, układ dolotowy, układ zapłonowy) jest **wykluczona** jako pierwotna przyczyna. Problem leży w **drodze paliwa benzynowego do komór spalania pod dużym obciążeniem**.

---

## 3. Panel ekspercki – troje motoryzacyjnych specjalistów

Powołuję trzy nowe persony eksperckie dedykowane temu problemowi. Nie są to „korpo-konsultanci”, tylko ludzie z brudem za paznokciami i znajomością tej platformy.

### Dr inż. Hideo Tanaka  
**Profil:** 30 lat w Subaru R&D Gunma (Japonia), starszy inżynier kalibracji silników serii EJ. Współautor protokołu SSM2 w drugiej generacji (od ok. 2003 r.). Specjalizacja: kalibracja FBKC (*feedback knock control*, sprzężenie zwrotne kontroli stuku), FKL (*fine knock learning*, drobne uczenie wartości stuku), strategie wzbogacania pod WOT, kalibracja EGT (*exhaust gas temperature*, temperatura spalin) i ochrona katalizatora. Emerytowany w 2018, obecnie konsultant. Zna na pamięć tabele wzbogacania i progi adaptacji LTFT w EJ253.

### Mike Hodges  
**Profil:** ASE Master Technician (Automotive Service Excellence – amerykański certyfikat mistrzowski mechaniki samochodowej), warsztat „Boxer Engine Service” pod Seattle (USA, Pacific Northwest). 25 lat tylko Subaru. Aktywny moderator forum NASIOC. Obsłużył setki EJ253 i EJ255 z przebiegami 250–400 tys. mil, w tym kilkanaście egzemplarzy z konwersją na propan/LPG sprowadzaną z Australii. Specjalizacja: starzenie się wtryskiwaczy benzynowych, układów paliwowych powracalnych vs niepowracalnych, błędy DBW (elektronicznej przepustnicy), dolot powietrza i wycieki podciśnieniowe.

### Mariusz Górniak  
**Profil:** inż. mechaniki, Politechnika Lubelska, 15 lat w warsztacie autoryzowanym Stag (Lublin). Specjalista od interakcji ECU benzyny z systemem LPG na Subaru. Zna aktualną wersję firmware w sterownikach AC Stag-300/400/500 BFC. Diagnozuje problemy które wynikają z konwersji LPG, ale ujawniają się dopiero na benzynie (zastoju paliwa, korozja kosza pompy, brudne wtryskiwacze benzyny). Pracował z polskimi EJ253 z LPG, w tym z Twoim modelem rocznikowym.

---

## 4. Dyskusja ekspertów – Twoja sprawa

> **Tanaka-san**, zaczynamy. Co Ty widzisz w tych liczbach?

**Tanaka:** Pozwólcie, że ułożę to po inżyniersku. EJ253 w mapie WOT ma celowe wzbogacanie do lambdy ok. 0.85 ± 0.03. To jest ochrona przed stukiem i ochrona katalizatora – wysoka temperatura spalin pod pełnym obciążeniem. **Lambda 1.02 pod WOT to nie jest „lekkie odchylenie”, to jest stan w którym ECU otwiera pętlę otwartą zapotrzebowania na paliwo, a komory dostają mieszankę stechiometryczną zamiast wzbogaconej**. Algorytm widzi sondę szerokopasmową raportującą lambda > 1 i próbuje to skompensować przez STFT – i dlatego widzimy STFT p95 = +24 %. Ale STFT ma limit autorytetu (zwykle ±25 %) i powyżej tego ECU nic więcej nie zrobi.  
Co do idle: 651 RPM mediana, swing 39 RPM, ECT 77–84 °C – to jest tak, jak wyszło z fabryki. Tu nie ma o czym rozmawiać. Idziemy dalej.  
**Mój werdykt: silnik dostaje za mało paliwa pod WOT na benzynie. Kropka. Czy to pompa, czy filtr, czy wtryski – tego z logu się nie dowiesz, ale fakt jest jednoznaczny.**

> **Mike**, Ty masz to z warsztatu. Jakie scenariusze w Twojej praktyce to wywołują?

**Hodges:** Pal kawę, bo będę liczyć przyczyny. EJ253 z przebiegiem ponad 200 tys. km i ponadto z konwersją LPG – to jest specyficzny przypadek. Gdy auto jeździ głównie na gazie, **benzyna stoi w szynie paliwowej i w wtryskiwaczach całe miesiące**. Z tego wynika trzy popularne winowajce w kolejności prawdopodobieństwa:

1. **Wtryskiwacze benzynowe – zanieczyszczenie i częściowe zatkanie**. Statyczny przepływ spada o 5 – 15 % na sztukę. Pod biegiem jałowym i w pętli zamkniętej ECU to wyrównuje. **Pod WOT, gdy pętla się otwiera i ECU komenduje pełne dawkowanie, brakuje paliwa.** Klasyk.
2. **Kosz pompy paliwa zatkany / pompa ze zużytym wirnikiem**. Pod małym przepływem ciśnienie trzyma się na 285 kPa nominalnych. Pod WOT, przy zapotrzebowaniu 60 – 80 g/s benzyny, ciśnienie spada – i widzisz dokładnie ten obraz: lambda rośnie, STFT idzie w +25 %, max-out. **W EJ253 z lat 2007 + jest zintegrowany moduł pompy w baku, bez wymienialnego filtra liniowego** – tak jak Michał napisał. Sito kosza po 200 tys. km i po stagnacji benzyny to standardowy temat.
3. **Wyciek podciśnieniowy (vacuum leak)** – mniej prawdopodobny u Ciebie, bo by zaburzał idle i pętlę zamkniętą. Twoje idle jest zdrowe, więc ten ślad w 80 % odpadnie. Ale sprawdź uszczelkę kolektora ssącego i przewody PCV (*Positive Crankcase Ventilation*, wentylacja skrzyni korbowej) – to po godzinie z butlą od dymu wykluczy lub potwierdzi.

**Mój ranking: 1. wtryskiwacze, 2. pompa/sito, 3. wyciek podciśnieniowy.**  
**Plan z manometrem masz dokładnie odwrotny do mojego rankingu – ale to jest świetne, bo ciśnienie szyny jest tańszą i szybszą weryfikacją niż wyjmowanie wtrysków. Jeśli ciśnienie pod WOT spada poniżej 250 kPa – pompa/sito. Jeśli trzyma 280–300 kPa – wtryski.**

> **Mariusz**, Ty znasz polską specyfikę i interakcję ze Stagiem. Co dodajesz?

**Górniak:** Mike trafia w sedno z punktem 1 i 2, ale dodam dwa szczegóły z polskiej praktyki:

- **„Stagowy klucz benzynowy”**: większość polskich konwersji ma ustawiony **minimalny czas pracy na benzynie po starcie 30–60 sekund** (przełącznik temperatury LPG). Ale w ciepły dzień bywa, że po starcie jedzie się 30 s na benzynie i dalej non-stop na gazie. Wtryskiwacze benzynowe pracują wtedy kilka procent czasu eksploatacji. **Sezon zimowy + długie postoje + krótkie odcinki na benzynie = idealne warunki do osadu w dyszach.**
- **Charakterystyka zwężenia w EJ253 z LPG**: gdy wtryskiwacze benzynowe się starzeją, na benzynie kręci się dziwnie, a na LPG dalej dobrze, **bo LPG ma własne wtryski (Hana/Valtek/Keihin gazowe) i one nie znają historii benzyny**. To dokładnie ten obraz, który widzimy: LPG zdrowe, benzyna chora. **To ekstremalnie typowy scenariusz.**

Co do hipotezy z brzytwą Ockhama Michała: tak. Najprostsze wyjaśnienie spójne z faktami to: **wtryskiwacze benzynowe są zanieczyszczone, prawdopodobnie połączone z tym, że pompa/sito też się starzeje**. Jedna wizyta z manometrem i to oddzieli.

**Ad „czy ECU mogłoby myśleć, że ma za mało paliwa przez vacuum leak”:** technicznie tak – wyciek podciśnieniowy zawyża ilość powietrza nieuwzględnioną w MAP/MAF, więc lambda idzie w stronę ubogiej i ECU dosypuje paliwa przez STFT. ALE: pod WOT przepustnica jest otwarta szeroko, podciśnienie w kolektorze ≈ 0, **więc wyciek podciśnieniowy pod WOT przestaje działać**. Twój problem jest WIDOCZNY pod WOT i niewidoczny na idle. **To nie pasuje do vacuum leaka.** Pasuje do problemu *ilościowego* z dostarczaniem benzyny.

**Ad „czy DBW może mis-controlować powietrze”:** mógłby teoretycznie, ale ECU widzi rzeczywistą lambdę z sondy szerokopasmowej i raportuje pętlę otwartą + STFT max+. To znaczy, że **z punktu widzenia ECU to nie jest problem powietrza, to jest problem paliwa.** Powietrza w spalinach jest tyle ile ma być, brakuje paliwa do tego powietrza. Można jeszcze dodatkowo sprawdzić przepustnicę pod kątem nauczonej pozycji zerowej i zakresu, ale to nie jest pierwszy podejrzany.

---

## 5. Synteza – co robisz dalej

Wszyscy trzej eksperci są zgodni:

1. **Manometr na szynie paliwowej (jak masz w drodze) – test pod WOT.**  
   Spadek ciśnienia poniżej 250 kPa pod WOT = pompa/sito. Trzymanie 280–300 kPa = wtryski.
2. **Jeśli ciśnienie OK → zmierz przepływ wtryskiwaczy.** Najtaniej: wymontować, wyczyścić ultradźwiękowo + test przepływu dynamicznego na stanowisku. W Polsce 80–150 zł/szt. + cena nowych uszczelnic.
3. **Jeśli pierwsze dwa OK → wyciek podciśnieniowy (smoke test).** Mało prawdopodobne ze względu na zdrowe idle, ale bezpieczna eliminacja.
4. **Cokolwiek ostatecznie naprawisz – po naprawie zarejestruj nowy log na benzynie z WOT.** Lambda powinna spaść do 0.85–0.92 i STFT do ±5 % pod WOT. To jedyne potwierdzenie działającej naprawy.

## 6. Sprostowania w narzędziu — ZROBIONE w v1.3.0-ms.10

W `tools/log-analyzer/analyze.py` zostały wdrożone wszystkie poprawki z poprzedniej rewizji + dodatkowe znalezione przy okazji walidacji:

- **Dynamiczny próg idle TPS** (`_detect_tps_idle_floor`) — zamiast twardego TPS < 1 %, wykrywany jest 5-ty percentyl TPS przy ciepłym silniku + 0.5 pp tolerancji. Dla Twojego DBW idle floor wyszedł ~2.7 % i klasyfikator wreszcie nie wciąga próbek z gazem 46 % do worka „idle”.
- **Smoothing klasyfikatora faz** — dodane zabezpieczenie: krótka faza obca (np. tip-in) NIE jest wchłaniana do poprzedniego IDLE. Wcześniej to powodowało że jedno potknięcie pedału „rozszerzało” idle.
- **3-filarowy fingerprint vacuum-leak** — pojedynczy sygnał (load-dependency LTFT) zastąpiony testem wymagającym wszystkich trzech: P1 LTFT idle > +5 %, P2 MAP idle > 40 kPa abs, P3 gradient idle−cruise > +5 pp. Dopiero komplet daje ostrzeżenie. Twój silnik ma wszystkie trzy filary ujemne → nieszczelność dolotu **wykluczona**.
- **Detekcja kanałów-placeholderów** (`detect_placeholder_channels`) — LTFT B3 stale 0 i STFT B3 z zakresem < 6 pp są oznaczane jako nieaktywne i pomijane w `fuel_trim_drift` oraz `detect_events`. Bez tego B3 generował fałszywe „health 0/100”.
- **Filtr idle RPM** — przepuszcza tylko RPM 550–850 + ciągłe okno ≥ 3 s (reszta to coast-down lub crank). Std spadł ze 367 → 37 RPM, czyli zgodnie z manualnym przeliczeniem.
- **Pasy MAF/MAP idle** rozszerzone do realnych wartości EJ253 NA: MAF 2.5–4.5 g/s, MAP 27–37 kPa abs. Wcześniej zdrowy idle wpadał w warning.

**Walidacja** — re-run obu logów po poprawkach:
- `reports/petrol_v3/` — health 0/100, 3 alarm + 4 warn + 17 pass. Vacuum leak: PASS, MAF idle 3.84 g/s: PASS, MAP idle 33 kPa: PASS, idle RPM std 37: warn-band ale zdrowy. Alarmy ograniczone do tego o co naprawdę chodzi: **WOT fuel delivery**.
- `reports/lpg_v3/` — health 76/100, 0 alarm + 2 warn + 20 pass. Spójne z faktem że na LPG WOT jest OK.

**To są od teraz autorytatywne raporty** — wszystko co jest sprzeczne z `reports/petrol_v3/` i `reports/lpg_v3/` jest błędem mojej wcześniejszej iteracji, nie Twojego auta.
