# Sim racing akciófigyelő

Háromóránként lekéri a `shops.json`-ban megadott Shopify-boltok termékeit és árait, naplózza őket a `history.json`-ba, és a `docs/index.html` oldalra csak azt teszi ki, ami a saját árelőzmény szerint tényleg olcsóbb lett.

## Beüzemelés (kb. 5 perc)
1. Hozz létre egy új GitHub repót, és töltsd fel ezt a mappa tartalmát (a rejtett `.github` mappával együtt).
2. Settings → Pages → Source: „Deploy from a branch”, ág: `main`, mappa: `/docs`.
3. Actions fül → „Árfigyelés” → Run workflow. Utána háromóránként magától fut.
4. Az oldal a `https://FELHASZNALONEV.github.io/REPO/` címen lesz elérhető.

## Fontos tudnivalók
- Minél előbb indítod el, annál jobb: a „valódi akció” jelzéshez legalább 3 nap előzmény kell, a megbízható szokásos árhoz a Black Friday (nov. 27.) előtti pár hét.
- Új bolt: írd be a `shops.json`-ba. Csak Shopify-alapú bolttal működik (ellenőrzés: nyisd meg a `bolt.hu/products.json` címet).
- A küszöb (`threshold_percent`) a `shops.json`-ban állítható.
