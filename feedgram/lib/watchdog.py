#!/usr/bin/env python3
import threading
import queue
import logging
# Libs
from feedgram.lib.process_input import Processinput
from feedgram.lib.database import MyDatabase
from feedgram.lib.telegram import Telegram
from feedgram.social.instagram import Instagram

CODA = queue.Queue()
CODA_TEMP = queue.Queue()
SUBSCRIPTIONS_DICT = {}
DATAS_SOCIAL = []


class Watchdog(threading.Thread):

    def news_retreiver_subthread(self, social_type, subscriptions, coda_social):
        if social_type == "instagram":
            datas = self.__instagram_interface.get_feed(subscriptions)
        else:
            datas = []
        if datas:
            coda_social.put(datas)

    def __init__(self, thread_id, name, mode, delay, condizione, conf_dict, still_run):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.name = name
        self.mode = mode
        self.delay = delay
        self.condizione = condizione
        self.still_run = still_run
        self.__conf_dict = conf_dict

        self.__logger = logging.getLogger("telegram_bot.WD.{}".format(self.name))

        # Inizializazione dei social da fare solo ne caso del news_retreiver e del telegram_user_interface
        if self.mode == "telegram_user_interface" or self.mode == "news_retreiver":
            self.__instagram_interface = Instagram()
            self.__db = MyDatabase(self.__conf_dict["BOT"]["databasefilepath"])

        if self.mode == "telegram_user_interface" or self.mode == "sender":
            self.__tel_interface = Telegram(self.__conf_dict["API"]["telegramkey"])  # <- cambiare config_dict

        if self.mode == "telegram_user_interface":
            self.__process_input = Processinput(self.__db, [self.__instagram_interface])  # da dare in input i social

    def run(self):
        global CODA
        global CODA_TEMP
        global SUBSCRIPTIONS_DICT
        global DATAS_SOCIAL

        if self.mode == "telegram_user_interface":
            last_update_id = None
            while self.still_run:
                updates = self.__tel_interface.get_updates(last_update_id)
                if len(updates["result"]) > 0:
                    last_update_id = self.__tel_interface.get_last_update_id(updates) + 1
                    CODA_TEMP.put(self.__process_input.process(updates))

        if self.mode == "elaborazione_code":
            delivering_list = []
            message_list = []
            # TODO: dare un'occhiata alla logica di questa roba qua sotto, c'è qualquadra che non cosa... :/
            while self.still_run:
                if CODA_TEMP.empty() and len(delivering_list) == 0:  # Se la coda è vuota aspetto che non diventi più vuota per aggiungere i messaggi in ddelivering_list
                    message_list = CODA_TEMP.get()
                    delivering_list = delivering_list + message_list
                    # print("Ho appena ricevuto dei messaggini nuovi da spedirez! ^_^")
                else:
                    if not CODA_TEMP.empty():  # Se mentre la coda non è vuota (ergo, mentre sis ta svuotando) si aggiunge
                        message_list = CODA_TEMP.get()
                        delivering_list = delivering_list + message_list
                        # print("Ho appena ricevuto dei messaggini nuovi da spedire! ^_^")
                    if len(delivering_list) > 0:
                        message = delivering_list.pop(0)
                        CODA.put(message)

        if self.mode == "sender":
            while self.still_run:
                self.__tel_interface.send_messages(CODA)
        if self.mode == "news_compiler":
            while self.still_run:
                with self.condizione:
                    self.condizione.wait()

                # TODO: Migliorare questa parte mettendo un tipo di messaggio a seconda del social
                messages_socials = []
                if SUBSCRIPTIONS_DICT:
                    for data_social in DATAS_SOCIAL:
                        if data_social["social"] in SUBSCRIPTIONS_DICT["subscriptions"]:
                            if data_social["internal_id"] in SUBSCRIPTIONS_DICT["subscriptions"][data_social["social"]]:
                                for chat_id in SUBSCRIPTIONS_DICT["subscriptions"][data_social["social"]][data_social["internal_id"]]:
                                    message_title = data_social["title"]
                                    if data_social["type"] == "new_post":
                                        messages_socials.append({'type': 'sendMessage',
                                                                 'text': "<b>[" + data_social["social"].upper() + "]</b>\nUser: <i>" + message_title + "</i>\nLink: " + data_social["post_url"],
                                                                 'chat_id': str(chat_id),
                                                                 'markdown': 'HTML'})
                                    elif data_social["type"] == "now_private":
                                        messages_socials.append({'type': 'sendMessage',
                                                                 'text': "<b>⚠️ALERT⚠️</b>\n<b>[" + data_social["social"].upper() + "]</b>\nThis account now is <b>private</b>, that means that you'll no longer receive updates until its owner decides to change it back to <i>public</i>.\nUser: <i>" + message_title + "</i>\nLink: " + data_social["post_url"],
                                                                 'chat_id': str(chat_id),
                                                                 'markdown': 'HTML'})
                                    elif data_social["type"] == "deleted_account":
                                        messages_socials.append({'type': 'sendMessage',
                                                                 'text': "<b>⚠️ALERT⚠️</b>\n<b>[" + data_social["social"].upper() + "]</b>\nThis account has been <b>deleted</b> and also automatically removed from your <i>Follow List</i>.\nUser: <i>" + message_title + "</i>\nLink: " + data_social["post_url"],
                                                                 'chat_id': str(chat_id),
                                                                 'markdown': 'HTML'})
                                    else:
                                        messages_socials.append({'type': 'sendMessage',
                                                                 'text': "<b>⚠️UNKNOWN MESSAGE⚠️</b>\nPlease report it to the creator of this bot.",
                                                                 'chat_id': str(chat_id),
                                                                 'markdown': 'HTML'})
                self.__logger.info("Messaggi da inviare: %s ", len(messages_socials))
                if len(messages_socials) > 0:
                    CODA_TEMP.put(messages_socials)
                    self.__logger.info("Messaggi messi in coda di spedizione.")

        if self.mode == "news_retreiver":
            # global condizione_compiler
            while self.still_run:

                self.__db.clean_dead_subscriptions()  # Pulisco al tabella "socials" rimuovendo gli account ai quali nessuno è più iscritto
                SUBSCRIPTIONS_DICT = self.__db.create_dict_of_user_ids_and_socials  # Creo un dizionario di tutte le iscrizioni degli utenti

                # Creo un dizionario con tutti gli account a cui gli utenti sono iscritti
                # socials_accounts_dict = {}
                # for social_key in SUBSCRIPTIONS_DICT.keys():
                #    socials_accounts_dict[social_key] = list(SUBSCRIPTIONS_DICT[social_key].keys())
                # ### ##
                # print(SUBSCRIPTIONS_DICT["instagram"])

                if SUBSCRIPTIONS_DICT:  # se il dizionario non è vuoto (la tabella "socials" non è vuota, ergo, almeno un utente è iscritto a qualcosa)

                    # In caso nessuno sia iscritto al social aggiungo un array ed un dizionario vuoti
                    num_subs_threads = {"subscriptions": {"total": 0}, "threads": {"total": 0}}
                    for element in ["instagram"]:  # TODO: Portare fuori questa lista, che indica i servizi che sono abilitati per il retrieving delle informazioni
                        if element not in SUBSCRIPTIONS_DICT["subscriptions"]:
                            SUBSCRIPTIONS_DICT["subscriptions"][element] = {}
                        if element not in SUBSCRIPTIONS_DICT["social_accounts"]:
                            SUBSCRIPTIONS_DICT["social_accounts"][element] = []
                        num_subs_threads["subscriptions"][element] = len(SUBSCRIPTIONS_DICT["social_accounts"][element])
                        num_subs_threads["subscriptions"]["total"] = num_subs_threads["subscriptions"]["total"] + num_subs_threads["subscriptions"][element]
                        num_subs_threads["threads"][element] = 0

                    max_subscriptions_per_thread = 10  # Ricorda, deve essere assolutamente > 0
                    self.__logger.info("Account massimi per thread: %s ", str(max_subscriptions_per_thread))
                    for element in num_subs_threads["threads"]:
                        if element != "total":
                            num_subs_threads["threads"][element] = num_subs_threads["subscriptions"][element] // max_subscriptions_per_thread
                            if num_subs_threads["subscriptions"][element] % max_subscriptions_per_thread:
                                num_subs_threads["threads"][element] += 1
                            num_subs_threads["threads"]["total"] = num_subs_threads["threads"]["total"] + num_subs_threads["threads"][element]
                    self.__logger.info(num_subs_threads)

                    # Crea nuovi thread
                    coda_social = queue.Queue()
                    threads = []
                    thread_id = 0
                    for social_name, value in num_subs_threads["threads"].items():
                        if social_name != "total":
                            head = 0
                            if max_subscriptions_per_thread > num_subs_threads["subscriptions"][social_name]:
                                tail = num_subs_threads["subscriptions"][social_name]
                            else:
                                tail = max_subscriptions_per_thread
                            for _ in range(0, value):

                                thread = threading.Thread(target=Watchdog.news_retreiver_subthread,
                                                          name="{}-{}".format(social_name, thread_id),
                                                          args=(self, social_name, SUBSCRIPTIONS_DICT["social_accounts"][social_name][head:tail], coda_social))
                                thread.start()
                                threads.append(thread)
                                thread_id += 1
                                head = tail
                                tail = tail + max_subscriptions_per_thread
                                if tail > num_subs_threads["subscriptions"][social_name]:
                                    tail = num_subs_threads["subscriptions"][social_name]

                    # Aspetta che tutti i thread finiscano
                    for tred in threads:
                        tred.join()

                    # Unisce i dati ricevuti dai thread
                    DATAS_SOCIAL = []
                    datas_queries = {'update': [], 'delete': []}
                    while not coda_social.empty():
                        messaggio = coda_social.get()
                        DATAS_SOCIAL = DATAS_SOCIAL + messaggio["messages"]
                        datas_queries["update"] = datas_queries["update"] + messaggio["queries"]["update"]
                        datas_queries["delete"] = datas_queries["delete"] + messaggio["queries"]["delete"]

                    # Ordina i messaggi in ordine cronologico
                    if len(DATAS_SOCIAL) > 1:
                        DATAS_SOCIAL = sorted(DATAS_SOCIAL, key=lambda k: k['post_date'], reverse=False)

                    # Credo che sarebbe meglio spostare questo coso qua sotto dopo la riga: print("Controllerò di nuovo tra 10 minuti.") o nel thread "News_compiler"
                    # Investigare a riguardo
                    self.__db.process_messages_queries(datas_queries)

                self.condizione.acquire()
                self.condizione.notify_all()
                self.condizione.release()
                self.__logger.info("Controllerò di nuovo tra 10 minuti.")

                with self.condizione:
                    self.condizione.wait(self.delay)