#!/usr/bin/env python3

import test.constants as cnst

from os import path, remove
import sqlite3
from feedgram.lib.database import MyDatabase


def myquery(db_path, query, *args, foreign=False, fetch=1):
    con = None
    data = None
    rowcount = 0

    print('Executing: {} with args {} with foreign_keys={}.'.format(query, args, foreign))
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        if foreign:
            cur.execute("PRAGMA foreign_keys = ON")
        cur.execute(query, tuple(args))

        if fetch > 1:
            data = cur.fetchmany(fetch)
        elif fetch == 0:
            data = cur.fetchall()
        else:
            data = cur.fetchone()

        rowcount = cur.rowcount

        if not data:
            con.commit()
    except sqlite3.Error as err:
        print("Database error: {}".format(err))
    except sqlite3.Warning as err:
        print("Exception in query: {}".format(err))
    finally:
        if con:
            con.close()
    return data, rowcount


DATABASE_PATH = "./test/databaseTest.sqlite3"


def test_table_error():

    # Nome del file per il test
    database_path = "./test/database_table_error.sqlite3"

    # Verifico se il file esiste. Nel caso eista lo elimino
    if path.exists(database_path):
        try:
            remove(database_path)
        except OSError as err:  # if failed, report it back to the user ##
            print("Error: {} - {}.".format(err.filename, err.strerror))

    # Mi assicuro che il file non esista/ sia stato cancellato
    assert not path.exists(database_path)

    # Eseguo la chiamata al costruttore della classe di configurazione
    # che mi genererà il file di configurazione con i valori base
    # e tenterà di caricarla
    MyDatabase(database_path)

    # Mi assicuro che il file sia stato creato
    assert path.exists(database_path)

    # Rimuovo una tabella
    myquery(database_path, 'DROP TABLE admins')

    # Rieseguo il costruttore che antrà ad aprire il database precedentemnte
    # creato ma senza una tabella
    database = MyDatabase(database_path)

    assert database.status == -1


def test_creation():

    # Verifico se il file esiste. Nel caso eista lo elimino
    if path.exists(DATABASE_PATH):
        try:
            remove(DATABASE_PATH)
        except OSError as err:  # if failed, report it back to the user ##
            print("Error: {} - {}.".format(err.filename, err.strerror))
    assert not path.exists(DATABASE_PATH)

    database = MyDatabase(DATABASE_PATH)
    # state = database.status

    assert path.exists(DATABASE_PATH)
    assert database.status == 1


def test_alredy_exist():

    assert path.exists(DATABASE_PATH)

    database = MyDatabase(DATABASE_PATH)

    assert database.status == 1


def test_user_id_not_exist():

    assert path.exists(DATABASE_PATH)
    database = MyDatabase(DATABASE_PATH)
    us_exist = database.check_utente(6551474276)

    assert not us_exist


def test_subscribe():

    database = MyDatabase(DATABASE_PATH)
    database.subscribe_user(6551474276, "username", 75692378, 1, 10)
    us_exist, _ = myquery(DATABASE_PATH, "SELECT 1 FROM users WHERE user_id = ?;", 6551474276)
    assert bool(us_exist)
    database.subscribe_user(1597534565, "foo", 456789132, 1, 10)
    us_exist, _ = myquery(DATABASE_PATH, "SELECT 1 FROM users WHERE user_id = ?;", 6551474276)
    assert bool(us_exist)
    database.subscribe_user(9638527416, "bar", 456789132, 1, 10)
    us_exist, _ = myquery(DATABASE_PATH, "SELECT 1 FROM users WHERE user_id = ?;", 6551474276)
    assert bool(us_exist)


def test_user_id_exist():

    assert path.exists(DATABASE_PATH)

    database = MyDatabase(DATABASE_PATH)
    us_exist = database.check_utente(6551474276)

    assert us_exist


def test_check_number_subscribtions():

    assert path.exists(DATABASE_PATH)

    database = MyDatabase(DATABASE_PATH)
    num_sub = database.check_number_subscribtions(6551474276)

    assert num_sub["user_id"] == 6551474276
    assert num_sub["actual_registrations"] == 0


def test_get_first_social_id_from_internal_user_social_and_if_present_subscribe1():
    '''
        Tentativo di iscrizione ad un social tramite link senza forzarne
        l'inserimento nel database del social e relazione con l'utente
            => manca il social nel database
            ==> non possiamo inserire la relazione (non forzato)
            ===> dovremo forzare l'inserimento di entrambi
    '''
    assert path.exists(DATABASE_PATH)
    database = MyDatabase(DATABASE_PATH)

    mresult = database.get_first_social_id_from_internal_user_social_and_if_present_subscribe(6551474276, cnst.SUB_BY_POST_LINK, False)

    assert mresult['subStatus'] == 'notInDatabase'


def test_get_first_social_id_from_internal_user_social_and_if_present_subscribe2():
    '''
        tentativo di inscrizione ad un social tramite link forzando
        l'inserimento del social e aggungengo la relazione con l'utente
            => manca il social nel database
            ==> forziamo nel database il social e la relazione con l'utente
    '''
    assert path.exists(DATABASE_PATH)
    database = MyDatabase(DATABASE_PATH)

    mresult = database.get_first_social_id_from_internal_user_social_and_if_present_subscribe(6551474276, cnst.SUB_BY_POST_LINK2, True)
    assert mresult['social_id'] == 1
    assert mresult['subStatus'] == 'CreatedSocialAccAndSubscribed'


def test_get_first_social_id_from_internal_user_social_and_if_present_subscribe22():
    '''
        tentativo di inscrizione ad un social tramite link forzando
        l'inserimento del social e aggungengo la relazione con l'utente
            => manca il social nel database
            ==> forziamo nel database il social e la relazione con l'utente
    '''
    assert path.exists(DATABASE_PATH)
    database = MyDatabase(DATABASE_PATH)

    mresult = database.get_first_social_id_from_internal_user_social_and_if_present_subscribe(1597534565, cnst.SUB_BY_POST_LINK22, True)
    assert mresult['social_id'] == 2
    assert mresult['subStatus'] == 'CreatedSocialAccAndSubscribed'


def test_get_first_social_id_from_internal_user_social_and_if_present_subscribe3():
    '''
        Tentativo di inscrizione ad un social tramite link senza forzarne
        l'inserimento nel database del social e relazione con l'utente
            => il social è presente nel database
            ==> estraggo le informazioni del social dal database
            ===> aggungiamo la relazione tra l'utente e il social
    '''
    assert path.exists(DATABASE_PATH)
    database = MyDatabase(DATABASE_PATH)

    mresult = database.get_first_social_id_from_internal_user_social_and_if_present_subscribe(57356765765, cnst.SUB_BY_POST_LINK, False)
    assert mresult['internal_id'] == '1769583068'
    assert mresult['social_id'] == 1
    assert mresult['subStatus'] == 'JustSubscribed'


def test_get_first_social_id_from_internal_user_social_and_if_present_subscribe4():
    '''
        Tentativo di ri-inscrizione ad un social
    '''
    database = MyDatabase(DATABASE_PATH)
    mresult = database.get_first_social_id_from_internal_user_social_and_if_present_subscribe(6551474276, cnst.SUB_BY_POST_LINK, False)

    assert mresult['subStatus'] == 'AlreadySubscribed'


def test_check_if_subscribed():

    database = MyDatabase(DATABASE_PATH)

    # If subscribed and given only internal_id
    is_sub, internal_id = database.check_if_subscribed(1597534565, "instagram", internal_id=12345929)
    assert is_sub and internal_id == "12345929"

    # If subscribed and given only username
    is_sub, internal_id = database.check_if_subscribed(1597534565, "instagram", username="testsocialuser")
    assert is_sub and internal_id == "12345929"

    # If not subscribed and given only internal_id
    is_sub, internal_id = database.check_if_subscribed(1597534565, "instagram", internal_id=78945123)
    assert (not is_sub) and internal_id is None

    # If not given enough data
    is_sub, internal_id = database.check_if_subscribed(1597534565, "instagram")
    assert is_sub is None and internal_id is None


def test_unfollow_social_account():

    database = MyDatabase(DATABASE_PATH)

    assert not database.unfollow_social_account(1597534565, "instagram", 1234)
    assert database.unfollow_social_account(1597534565, "instagram", 12345929)


def test_create_dict_of_user_ids_and_socials():

    database = MyDatabase(DATABASE_PATH)

    res = database.create_dict_of_user_ids_and_socials

    il_post = {"internal_id": "1769583068",
               "username": "il_post",
               "title": "il_post",
               "retreive_time": "1587222607",
               "status": "public"
               }

    # Il retreive_time cambia ogni volta che si lanciano i test,
    # dato che ad ogni lancio dei test il database viene resettato

    assert res['social_accounts']['instagram'][0]['internal_id'] == il_post['internal_id']
    assert res['social_accounts']['instagram'][0]['username'] == il_post['username']
    assert res['social_accounts']['instagram'][0]['title'] == il_post['title']
    assert res['social_accounts']['instagram'][0]['status'] == il_post['status']
    assert res['subscriptions']['instagram'][il_post['internal_id']] == [{'user_id': 6551474276, 'social_id': 1, 'state': 0, 'expire': -1}, {'user_id': 57356765765, 'social_id': 1, 'state': 0, 'expire': -1}]


def test_user_subscriptions():
    '''
        Verifica le sottoscrizioni dell'utente
    '''
    assert path.exists(DATABASE_PATH)
    database = MyDatabase(DATABASE_PATH)

    res = database.user_subscriptions(6551474276)

    assert res[0][0] == "instagram"
    assert res[0][1] == "il_post"
    assert res[0][2] == "1769583068"
    assert res[0][3] == 0
    assert res[0][4] == -1


def test_set_state_of_social_account():
    '''
        Vado a modificare lo stato di una sottoscrizione
        verifico che la modifica sia avvenuta corettamente
    '''
    database = MyDatabase(DATABASE_PATH)

    result = database.set_state_of_social_account(6551474276, 'instagram', 1769583068, 1, 1589753073)

    assert result

    res = database.user_subscriptions(6551474276)

    assert res[0][0] == "instagram"
    assert res[0][1] == "il_post"
    assert res[0][2] == "1769583068"
    assert res[0][3] == 1
    assert res[0][4] == 1589753073


def test_clean_expired_state():
    '''
        Vado a verificare la variazione nel numero di registrazioni
    '''
    assert path.exists(DATABASE_PATH)
    database = MyDatabase(DATABASE_PATH)

    res_before, _ = myquery(DATABASE_PATH, "SELECT count() FROM registrations WHERE registrations.expire_date > -1")

    database.clean_expired_state()

    res_afther, _ = myquery(DATABASE_PATH, "SELECT count() FROM registrations WHERE registrations.expire_date > -1")

    assert res_before > res_afther


def test_process_messages_queries1():

    database = MyDatabase(DATABASE_PATH)
    database.process_messages_queries(cnst.QUERY_TODO_UPDATE)
    res, _ = myquery(DATABASE_PATH,
                     "SELECT retreive_time, status FROM socials WHERE social = ? AND internal_id = ?",
                     'instagram', 1769583068)

    assert res[0] == 999999999
    assert res[1] == 'private'


QUERY_TODO_DELETE = {"delete": [{"type": "socialAccount",
                                 "social": "instagram",
                                 "internal_id": "1769583068"
                                 }
                                ],
                     "update": []
                     }


def test_process_messages_queries2():

    database = MyDatabase(DATABASE_PATH)

    social_id, _ = myquery(DATABASE_PATH, "SELECT socials.social_id FROM socials WHERE socials.social = ? AND socials.internal_id = ?", QUERY_TODO_DELETE['delete'][0]['social'], QUERY_TODO_DELETE['delete'][0]['internal_id'])

    database.process_messages_queries(QUERY_TODO_DELETE)

    res, _ = myquery(DATABASE_PATH, "SELECT count() FROM registrations WHERE registrations.social_id = ?", social_id[0])

    assert res[0] == 0

    res, _ = myquery(DATABASE_PATH, "SELECT count() FROM socials WHERE socials.internal_id = ?", QUERY_TODO_DELETE['delete'][0]['internal_id'])

    assert res[0] == 0


def test_clean_dead_subscriptions():

    database = MyDatabase(DATABASE_PATH)

    # creo una sottoscrizione ad un profilo social di un utente fittizio
    _ = database.get_first_social_id_from_internal_user_social_and_if_present_subscribe(1234567890, cnst.SUB_BY_POST_LINK2, True)

    # verifico quante registrazioni ci sono
    res_before, _ = myquery(DATABASE_PATH, "SELECT count() FROM registrations")

    # rimuovo la relazione tra l'utente e il profilo social
    myquery(DATABASE_PATH, "DELETE FROM registrations WHERE user_id = ?", 1234567890)

    # verifico quante registrazioni ci sono ora
    res_after, _ = myquery(DATABASE_PATH, "SELECT count() FROM registrations")

    # verifico che sia avvenuta realmente la rimozione confrontando i 2 count
    assert res_after[0] == res_before[0] - 1

    # verifico che il profilo social sia ancora presente nel database
    res, _ = myquery(DATABASE_PATH, "SELECT count() FROM socials WHERE socials.internal_id = ?", cnst.SUB_BY_POST_LINK2["internal_id"])
    assert res[0] == 1

    database.clean_dead_subscriptions()

    # verifico che il profilo social sia stato rimosso dal database perchè nessuno è iscritto
    res, _ = myquery(DATABASE_PATH, "SELECT count() FROM socials WHERE socials.internal_id = ?", cnst.SUB_BY_POST_LINK2["internal_id"])
    assert res[0] == 0


def test_unsubscribe():

    database = MyDatabase(DATABASE_PATH)
    database.unsubscribe_user(6551474276)
    us_exist, _ = myquery(DATABASE_PATH, "SELECT 1 FROM users WHERE user_id = ?;", 6551474276)

    assert not bool(us_exist)
