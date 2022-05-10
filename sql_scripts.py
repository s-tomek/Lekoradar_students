DROP_DB = """
DROP TABLE IF EXISTS Artysta CASCADE;
DROP TABLE IF EXISTS Eksponat CASCADE;
DROP TABLE IF EXISTS Instytucja CASCADE;
DROP TABLE IF EXISTS Wypozyczenie;
DROP TABLE IF EXISTS Wystawienie;
DROP TABLE IF EXISTS Galeria;
"""


DB_INIT = """
DROP TABLE IF EXISTS Artysta CASCADE;
DROP TABLE IF EXISTS Eksponat CASCADE;
DROP TABLE IF EXISTS Instytucja CASCADE;
DROP TABLE IF EXISTS Wypozyczenie;
DROP TABLE IF EXISTS Wystawienie;
DROP TABLE IF EXISTS Galeria;

CREATE TABLE Artysta (
    id NUMERIC(4) PRIMARY KEY,
    imie VARCHAR(40) NOT NULL,
    nazwisko VARCHAR(40) NOT NULL,
    rok_urodzenia DATE NOT NULL,
    rok_smierci DATE
);

CREATE TABLE Eksponat (
    id NUMERIC(4) PRIMARY KEY,
    tytul VARCHAR(40) NOT NULL,
    typ VARCHAR(40) NOT NULL,
    wysokosc NUMERIC(4) NOT NULL,
    szerokosc NUMERIC(4) NOT NULL,
    waga NUMERIC(4) NOT NULL,
    artysta_id NUMERIC(4) REFERENCES Artysta
);

CREATE TABLE Galeria (
    id NUMERIC(4) PRIMARY KEY, 
    nazwa VARCHAR(40) NOT NULL,
    liczba_sal NUMERIC(4) NOT NULL
);

CREATE TABLE Instytucja (
    id NUMERIC(4) PRIMARY KEY,
    nazwa VARCHAR(40) NOT NULL,
    miasto VARCHAR(40) NOT NULL
);

CREATE TABLE Wystawienie (
    id NUMERIC(4) PRIMARY KEY,
    id_eksponatu NUMERIC(4) NOT NULL REFERENCES Eksponat,
    sala NUMERIC(4) NOT NULL, 
    id_galerii NUMERIC(4) NOT NULL REFERENCES Galeria,
    poczatek DATE NOT NULL,
    koniec DATE NOT NULL
);

CREATE TABLE Wypozyczenie (
    id NUMERIC(4) PRIMARY KEY,
    id_eksponatu NUMERIC(4) NOT NULL REFERENCES Eksponat,
    id_instytucji NUMERIC(4) NOT NULL REFERENCES Instytucja,
    poczatek DATE NOT NULL,
    koniec DATE  NOT NULL
);


-- Trigger zapewniający, że trzymamy tylko artystów, którzy są autorami jakichś eksponatów
CREATE OR REPLACE FUNCTION f1 () RETURNS TRIGGER AS $$
DECLARE
    ile integer;
    autor integer;
BEGIN
    IF old.autor_id IS NOT NULL THEN
        SELECT old.autor_id INTO autor;
        SELECT COUNT(*) INTO ile
        FROM Eksponat
        WHERE autor_id = old.autor_id;
        IF (ile == 0) THEN
            raise notice 'Usunięcia ostatniego dzieła artysty, %', autor;
            raise notice 'Usuwam go z bazy danych';
            DELETE FROM Artysta WHERE id = autor;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER t1
AFTER UPDATE OR DELETE ON Eksponat FOR EACH ROW
EXECUTE PROCEDURE f1();


-- Trigger zapewniający, że eksponat jest jednocześnie tylko w jednym miejscu
CREATE OR REPLACE FUNCTION f2 () RETURNS TRIGGER AS $$
DECLARE
	ile_wystawien integer;
	ile_wypozyczen integer;
	eks_id integer;
BEGIN
	SELECT new.id_eksponatu INTO eks_id;
	SELECT COUNT(*) INTO ile_wystawien
	FROM Wystawienie
	WHERE id_eksponatu = eks_id AND koniec >= new.poczatek AND poczatek <= new.koniec;
	SELECT COUNT(*) INTO ile_wypozyczen
	FROM Wypozyczenie
	WHERE id_eksponatu = eks_id AND koniec >= new.poczatek AND poczatek <= new.koniec;
	IF (ile_wystawien + ile_wypozyczen > 0) THEN
		raise exception 'Eksponat jest w tym okresie niedostępny';
	END IF;
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER t2
BEFORE INSERT OR UPDATE ON Wystawienie FOR EACH ROW
EXECUTE PROCEDURE f2();

CREATE TRIGGER t3
BEFORE INSERT OR UPDATE ON Wypozyczenie FOR EACH ROW
EXECUTE PROCEDURE f2();


-- trigger zapewniający, że stosunek dat jest poprawny (poczatek < koniec)
CREATE OR REPLACE FUNCTION f5 () RETURNS TRIGGER AS $$
BEGIN
    IF (new.poczatek > new.koniec) THEN
        raise exception 'Wprowadzono niepoprawne daty';
    END IF;
 	RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER t6
BEFORE INSERT OR UPDATE ON Wystawienie FOR EACH ROW
EXECUTE PROCEDURE f5();

CREATE TRIGGER t7
BEFORE INSERT OR UPDATE ON Wypozyczenie FOR EACH ROW
EXECUTE PROCEDURE f5();


CREATE OR REPLACE FUNCTION dni_w_roku(rok integer, poczatek date, koniec date) RETURNS integer AS $$
DECLARE
	pocz_r date;
	kon_r date;
	ile integer := 0;
	p date;
	k date;
BEGIN
    SELECT date '2000-01-01' + (rok-2000) * interval '1 year' INTO pocz_r;
    SELECT date '2000-12-31' + (rok-2000) * interval '1 year' INTO kon_r;
	IF (NOT (poczatek > kon_r OR koniec < pocz_r)) THEN
		IF (pocz_r < poczatek) THEN
			p := poczatek;
		ELSE
			p := pocz_r;
		END IF;
		IF (kon_r > koniec) THEN
			k := koniec;
		ELSE
			k := kon_r;
		END IF;
		ile := k - p + 1;
	END IF;
	RETURN ile;
END;
$$ LANGUAGE plpgsql;


-- trigger zapewniający, że żaden eksponat nie przebywa poza muzeum dłużej niż 30 dni rocznie
CREATE OR REPLACE FUNCTION f3 () RETURNS TRIGGER AS $$
DECLARE
	ile1 integer := 0;
	ile2 integer := 0;
	year1 integer;
	year2 integer;
    arow record;
BEGIN
	IF (new.koniec - new.poczatek + 1 > 60) THEN
		raise exception 'Eksponat nie może przebywać więcej niż 30 dni rocznie poza muzeum';
	END IF;
    --SELECT (EXTRACT YEAR FROM date '2012-04-12');
	SELECT EXTRACT (YEAR FROM (new.poczatek)) INTO year1;
	SELECT EXTRACT (YEAR FROM (new.koniec)) INTO year1;
	
	FOR arow IN (SELECT * FROM Wypozyczenie
	WHERE id_eksponatu = new.id_eksponatu) LOOP
		ile1 := ile1 + dni_w_roku(year1, arow.poczatek, arow.koniec);
		ile2 := ile2 + dni_w_roku(year2, arow.poczatek, arow.koniec);
	END LOOP;
	
	IF (ile1 > 30 OR ile2 > 30) THEN
		raise exception 'Eksponat nie może przebywać więcej niż 30 dni rocznie poza muzeum';
	END IF;
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER t4
AFTER INSERT OR UPDATE ON Wypozyczenie FOR EACH ROW
EXECUTE PROCEDURE f3();

-- trigger zapewniający, że muzeum zawsze ma w swoich galeriach lub w magazynie
-- co najmniej jeden eksponat każdego artysty.
CREATE OR REPLACE FUNCTION f4 () RETURNS TRIGGER AS $$
DECLARE
	art_id integer;
	ile_wypozyczonych integer := 0;
	data_ date := new.poczatek;
	ile_autorstwa integer;
    arow record;
BEGIN
    SELECT * FROM Eksponat WHERE id = new.id_eksponatu INTO arow;
	IF (arow.artysta_id IS NOT NULL) THEN
		SELECT artysta_id INTO art_id
		FROM Eksponat
		WHERE id = new.id_eksponatu;
		
		SELECT COUNT(*) INTO ile_autorstwa
		FROM Eksponat
		WHERE artysta_id = art_id;
		
		WHILE new.koniec >= data_ LOOP
			
			SELECT COUNT(*) INTO ile_wypozyczonych FROM 
			(Wypozyczenie LEFT JOIN Eksponat
			ON Wypozyczenie.id_eksponatu = Eksponat.id) AS t
			WHERE t.artysta_id = art_id AND t.poczatek <= data_ AND t.koniec >= data_;
			
			IF (ile_wypozyczonych = ile_autorstwa) THEN
				raise exception 'Nie można jednocześnie wypożyczyć wszystkich dzieł danego artysty';
			END IF;

            data_ := data_ + 1;
		END LOOP;		
	END IF;
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER t5
AFTER INSERT OR UPDATE ON Wypozyczenie FOR EACH ROW
EXECUTE PROCEDURE f4();


CREATE OR REPLACE FUNCTION f6 () RETURNS TRIGGER AS $$
DECLARE
    l_sal integer;
BEGIN
    SELECT SUM(liczba_sal) INTO l_sal
    FROM Galeria
    WHERE Galeria.id = new.id_galerii;

    IF (new.sala > l_sal) THEN
        raise exception 'W wybranej galerii nie ma takiej sali';
    END IF;
 	RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER t8
BEFORE INSERT OR UPDATE ON Wystawienie FOR EACH ROW
EXECUTE PROCEDURE f6();

"""

DB_SAMPLE = """
    -- Galerie
    INSERT INTO Galeria VALUES (1, 'Galeria Klasyków', 4);
    INSERT INTO Galeria VALUES (2, 'Galeria Sztuki Nowoczesnej', 3);

    -- Artyści
    INSERT INTO Artysta VALUES (1, 'Francesco', 'Ramazotti', '1959-03-09', '2009-10-18');
    INSERT INTO Artysta VALUES (2, 'Vincent', 'Moore', '1982-11-12', NULL);

    -- Eksponaty
    INSERT INTO Eksponat VALUES (1, 'W poszukiwaniu buga', 'Obraz', 150, 100, 3, 1);
    INSERT INTO Eksponat VALUES (2, 'Null o poranku', 'Obraz', 59, 90, 1, 1);
    INSERT INTO Eksponat VALUES (3, 'Złoty Procesor', 'Rzeźba', 120, 90, 12, 2);

    -- Instytucje
    INSERT INTO Instytucja VALUES (1, 'Prywatne Muzeum w Toruniu', 'Toruń');

"""

LIST_TABLES = """
    SELECT tablename
    FROM pg_catalog.pg_tables
    WHERE schemaname = 'scott' AND
    tableowner = 'scott';
"""

GET_EKSPONAT = """
    SELECT * FROM eksponat;
"""

GET_EKSPONAT_WITH_ARTYSTA = """
    SELECT eksponat.*, artysta.imie, artysta.nazwisko FROM eksponat LEFT JOIN artysta ON eksponat.artysta_id =artysta.id;
"""

GET_ARTYSTA = """
    SELECT * FROM artysta;
"""

GET_GALERIA = """
    SELECT * FROM galeria;
"""

GET_INSTYTUCJA = """
    SELECT * FROM instytucja;
"""

GET_WYPOZYCZENIE = """
    SELECT * FROM wypozyczenie;
"""

GET_WYSTAWIENIE = """
    SELECT * FROM wystawienie;
"""

ADD_TO_EKSPONAT = """
    INSERT INTO eksponat
    (id, tytul, typ, wysokosc, szerokosc, waga, artysta_id) 
    VALUES (%s, %s, %s, %s, %s, %s, %s);
"""

ADD_TO_ARTYSTA = """
    INSERT INTO artysta
    (id, imie, nazwisko, rok_urodzenia, rok_smierci) 
    VALUES (%s, %s, %s, %s, %s);
"""

ADD_TO_GALERIA = """
    INSERT INTO galeria
    (id, nazwa, liczba_sal)
    VALUES (%s, %s, %s);
"""

ADD_TO_INSTYTUCJA = """
    INSERT INTO instytucja
    (id, nazwa, miasto)
    VALUES (%s, %s, %s);
"""

ADD_TO_WYSTAWIENIE = """
    INSERT INTO wystawienie
    (id, id_eksponatu, sala, id_galerii, poczatek, koniec)
    VALUES (%s, %s, %s, %s, %s, %s);
"""

ADD_TO_WYPOZYCZENIE = """
    INSERT INTO wypozyczenie
    (id, id_eksponatu, id_instytucji, poczatek, koniec)
    VALUES (%s, %s, %s, %s, %s);
"""