# 🧠 SOL26 Interpret – Roadmapa podľa prednášky

Fúha, tak toto je úplne iná liga!  
Zabudni na to prvé video – to bolo len všeobecné pre nejaký jednoduchý stack-based jazyk.

Toto tvoje video je **zlatá baňa**. Prednášajúci (Ondřej Ondryáš) tam presne vysvetľuje, ako funguje **SOL26** – jazyk inšpirovaný **Smalltalkom**, ktorý je **čistý objektový jazyk**.

To znamená, že **všetko je objekt**:

- `true`
- `false`
- čísla
- reťazce
- bloky kódu

Dokonca aj riadiace štruktúry fungujú ako **správy medzi objektmi**.

---

# ⚙️ Architektúra interpretra

Z tohto streamu sa dá presne odvodiť architektúra tvojho interpretra.

Dôležité:

Tvoj interpret **nebude mať**:

- klasický **Program Counter**
- klasický **Stack interpreter**

Namiesto toho bude fungovať ako:

```
AST Evaluator + Object Memory Model
```

Teda:

- program je reprezentovaný ako **AST strom**
- interpret **rekurzívne vyhodnocuje uzly stromu**
- všetky hodnoty sú **objekty**

---

# 🗺️ Ultimátna Roadmapa pre SOL26 Interpret

---

# Kapitola 1: Preskúmanie AST (To, čo máš urobiť dnes)

V `execute` metóde **neparsuješ XML**.

Pydantic ti už vytvoril objekt:

```
self.current_program
```

Tvoja prvá úloha je:

**pochopiť štruktúru AST.**

---

## Preskúmaj štruktúru programu

Pozri napríklad:

```
self.current_program.classes
```

Zisti:

- ako vyzerá **zoznam tried**
- ako vyzerajú **metódy**
- ako vyzerajú **príkazy**

---

## Typy výrazov (Expressions)

Zistíš, že existujú **4 hlavné typy výrazov**.

### Literal

Konštanty:

```
1
"hello"
true
nil
```

---

### Var

Premenné:

```
x
counter
name
```

---

### Block

Blok kódu:

```
[ :x | x + 1 ]
```

---

### Send

Zasielanie správy objektu:

```
x plus: 5
```

alebo

```
condition ifTrue: [ ... ]
```

---

# Kapitola 2: Pamäťový a Objektový model

V SOL26 je **všetko objekt**.

Premenné **neobsahujú hodnotu**, ale **referenciu na objekt**.

Musíš si vytvoriť **svet objektov**.

---

## Základná trieda

Vytvor Python triedu napr.:

```
SolObject
```

Táto trieda bude reprezentovať **každý objekt v SOL26 programe**.

---

## Interné atribúty

Prednášajúci spomínal **interné inštančné atribúty**.

Napríklad integer objekt musí interne držať hodnotu:

```
self.val = 1
```

---

## Built-in typy

Musíš implementovať základné typy:

- `SolInteger`
- `SolString`
- `SolBool`
- `SolNil`

`SolBool` bude mať dve inštancie:

```
true
false
```

---

# Kapitola 3: Zasielanie správ (Message Passing)

V SOL26 **neexistujú operátory ani príkazy**.

Všetko sa robí **zasielaním správ objektom**.

AST to reprezentuje cez:

```
Send
```

---

## Funkcia send_message

V interpretri si vytvor funkciu:

```
send_message(target_object, selector, arguments)
```

Táto funkcia:

1. vezme objekt
2. zistí jeho typ
3. nájde metódu podľa selektora
4. zavolá ju

---

## Príklad

```
5 plus: 3
```

Interpret:

1. vyhodnotí `5`
2. nájde metódu `plus:`
3. zavolá ju s argumentom `3`

---

## Magické atribúty

Prednášajúci spomenul zaujímavú vec.

Ak pošleš správu ktorú objekt **nepozná**, napr.:

```
a: 5
```

Interpret to má chápať ako:

```
vytvor atribút a s hodnotou 5
```

---

# Kapitola 4: Kontext a Premenné

Jediný skutočný príkaz v SOL26 je:

```
l_value := r_value
```

---

## Context / Environment

Potrebujeme **mapu premenných**.

V Pythone napríklad:

```
context = {}
```

Mapuje:

```
názov premennej -> objekt
```

Príklad:

```
context["x"] -> SolInteger(5)
```

---

## Funkcia evaluate_expr

Napíš funkciu:

```
evaluate_expr(expr, context)
```

Príklad:

```
x := 1
```

Interpret:

1. vytvorí `SolInteger(1)`
2. uloží do

```
context["x"]
```

---

# Kapitola 5: Bloky a Riadenie toku

V SOL26 sa riadenie toku robí cez **bloky**.

Blok:

```
[ :arg | ... ]
```

---

## Trieda SolBlock

Vytvor triedu:

```
SolBlock
```

Bude obsahovať:

- sekvenciu príkazov
- argumenty
- referenciu na context

---

## If / Else

`SolBool` reaguje na správu:

```
ifTrue: ifFalse:
```

Príklad:

```
condition ifTrue: [ ... ] ifFalse: [ ... ]
```

---

## Cykly

Integer reaguje na správu:

```
timesRepeat:
```

Príklad:

```
5 timesRepeat: [ ... ]
```

---

Blok reaguje na správu:

```
whileTrue:
```

Interpret to implementuje ako Python `while`.

---

# Kapitola 6: Uzávery (Closures) – Boss level

Najťažšia časť celého projektu.

Keď vznikne blok:

```
[ :x | x + counter ]
```

musí si **zapamätať kontext**, v ktorom vznikol.

---

## Implementácia

`SolBlock` si musí uložiť:

```
self.context
```

Keď sa blok neskôr spustí, musí vedieť:

- čítať premenné
- zapisovať premenné

z **externého kontextu**.

---

# Kapitola 7: Dedičnosť a Metódy

Používatelia môžu definovať triedy:

```
class Dog : Animal
```

---

## Vytváranie objektov

Objekt sa vytvorí správou:

```
Dog new
```

---

## Hľadanie metódy

Pri volaní metódy:

1. pozrieš triedu objektu
2. ak ju nenájdeš
3. hľadáš v nadradenej triede

---

# 📅 Čím začať dnes

Postupuj presne takto:

### 1️⃣ Preskúmaj AST

Do `execute` pridaj debug printy a vypíš:

```
self.current_program
```

Zisti:

- štruktúru tried
- štruktúru metód
- štruktúru výrazov

---

### 2️⃣ Vytvor objektový model

Sprav nový súbor:

```
sol_objects.py
```

A implementuj jednoduché triedy:

- `SolObject`
- `SolInteger`
- `SolString`

---

### 3️⃣ Priprav sa na send_message

Keď bude jasné:

- ako vyzerá AST
- ako držíš objekty v pamäti

môžeš implementovať:

```
send_message()
```

To je **jadro celého jazyka SOL26**.