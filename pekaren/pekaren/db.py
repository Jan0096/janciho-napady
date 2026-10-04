"""Databáza aplikácie (SQLite) – schéma a pripojenie."""

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS dodavatel (
    id          INTEGER PRIMARY KEY,
    nazov       TEXT NOT NULL UNIQUE,
    ico         TEXT,
    kontakt     TEXT
);

CREATE TABLE IF NOT EXISTS surovina (
    id          INTEGER PRIMARY KEY,
    nazov       TEXT NOT NULL UNIQUE,
    jednotka    TEXT NOT NULL DEFAULT 'kg',
    min_zasoba  REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS faktura (
    id               INTEGER PRIMARY KEY,
    cislo            TEXT NOT NULL,
    dodavatel_id     INTEGER NOT NULL REFERENCES dodavatel(id),
    datum_vystavenia TEXT NOT NULL,
    datum_splatnosti TEXT NOT NULL,
    suma_bez_dph     REAL NOT NULL,
    dph              REAL NOT NULL DEFAULT 0,
    datum_uhrady     TEXT,
    UNIQUE (dodavatel_id, cislo)
);

CREATE TABLE IF NOT EXISTS prijem (
    id            INTEGER PRIMARY KEY,
    datum         TEXT NOT NULL,
    dodavatel_id  INTEGER NOT NULL REFERENCES dodavatel(id),
    faktura_id    INTEGER REFERENCES faktura(id) ON DELETE SET NULL,
    poznamka      TEXT
);

CREATE TABLE IF NOT EXISTS prijem_polozka (
    id               INTEGER PRIMARY KEY,
    prijem_id        INTEGER NOT NULL REFERENCES prijem(id) ON DELETE CASCADE,
    surovina_id      INTEGER NOT NULL REFERENCES surovina(id),
    mnozstvo         REAL NOT NULL CHECK (mnozstvo > 0),
    jednotkova_cena  REAL NOT NULL CHECK (jednotkova_cena >= 0),
    sadzba_dph       REAL NOT NULL DEFAULT 20
);

CREATE TABLE IF NOT EXISTS spotreba (
    id           INTEGER PRIMARY KEY,
    datum        TEXT NOT NULL,
    surovina_id  INTEGER NOT NULL REFERENCES surovina(id),
    mnozstvo     REAL NOT NULL CHECK (mnozstvo > 0),
    poznamka     TEXT
);

CREATE TABLE IF NOT EXISTS naklad_pravidelny (
    id            INTEGER PRIMARY KEY,
    nazov         TEXT NOT NULL,
    kategoria     TEXT NOT NULL,
    typ           TEXT NOT NULL CHECK (typ IN ('fixny', 'variabilny')),
    mesacna_suma  REAL NOT NULL CHECK (mesacna_suma >= 0),
    platny_od     TEXT NOT NULL,
    platny_do     TEXT
);

CREATE TABLE IF NOT EXISTS naklad (
    id         INTEGER PRIMARY KEY,
    datum      TEXT NOT NULL,
    nazov      TEXT NOT NULL,
    kategoria  TEXT NOT NULL,
    typ        TEXT NOT NULL CHECK (typ IN ('fixny', 'variabilny')),
    suma       REAL NOT NULL CHECK (suma >= 0)
);

CREATE TABLE IF NOT EXISTS trzba (
    id            INTEGER PRIMARY KEY,
    datum         TEXT NOT NULL,
    suma_bez_dph  REAL NOT NULL CHECK (suma_bez_dph >= 0),
    kanal         TEXT NOT NULL DEFAULT 'predajňa'
);
"""


def pripoj(cesta: str = "pekaren.db") -> sqlite3.Connection:
    """Otvorí (a v prípade potreby vytvorí) databázu."""
    conn = sqlite3.connect(cesta)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
