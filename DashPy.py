from json import loads
from urllib.request import urlopen
import urllib.request
import tkinter as tk
from tkinter import ttk
import socket, xml.etree.ElementTree, queue, threading, datetime, sys
from configparser import ConfigParser

#The dash_win class starts the tkinter window
class dash_win(object):
    def __init__(self):
        self.master = tk.Tk()
        self.master.wm_title("PyDash")
        #self.master.iconbitmap("location")

        window = tk.Frame()
        window.pack(side="top", fill="both", expand = True)
        frame = dash(window, self.master).pack()
        self.master.mainloop()

#The class dash is the main menu of the application showing the stats
class dash(tk.Frame):
    def __init__(self, parent, master):
        self.queue_viewers = queue.Queue()
        self.queue_desc = queue.Queue()
        self.queue_game = queue.Queue()
        self.queue_views = queue.Queue()
        self.queue_status = queue.Queue()

        self.parent = tk.Frame.__init__(self, parent)
        self.master = master

        self.menubar = tk.Menu()
        self.cascade = tk.Menu()
        self.menubar.add_cascade(label="File", menu=self.cascade)
        self.cascade.add_command(label="Add user", command = lambda: user_or_auth(self.master, "Channel name", "user_name"))
        self.cascade.add_command(label="Add oauth", command = lambda: user_or_auth(self.master, "oauth", "oauth"))
        self.cascade.add_command(label="Refresh", command = lambda: self.refresh())
        self.cascade.add_command(label="Quit", command = lambda: self.master.destroy())
        self.master.config(menu= self.menubar)

        cfg = ConfigParser()
        cfg.read("config.ini")

        try:
            user_name = cfg.get("user", "user_name")
            user_lwr = user_name.lower()
            client_id = cfg.get("user", "oauth").split(":")[1]
            user_id = "https://api.twitch.tv/kraken/search/channels?query=" + user_name + "&type=suggest"
            res = urllib.request.Request(user_id)
            res.add_header("Client-ID", client_id)
            res.add_header("Accept", "application/vnd.twitchtv.v5+json")
            respp = urllib.request.urlopen(res)
            stuff = respp.read()
            stuff1 = stuff.decode("utf-8")
            name1 = loads(stuff1)
            for i in name1["channels"]:
                if i["name"] == user_name:
                    user_id = i["_id"]

            url = "https://api.twitch.tv/kraken/channels/" + str(user_id)
            req = urllib.request.Request(url)
            req.add_header("Client-ID", client_id)
            req.add_header("Accept", "application/vnd.twitchtv.v5+json")
            resp = urllib.request.urlopen(req)
            data = resp.read()
            data_chl = loads(data.decode("utf-8"))
            name = "Channel name: " + data_chl["display_name"]

        except:
            url = ""
            name = ""

        try:
            auth = cfg.get("user", "oauth")
        except:
            auth = ""

        self.disp_name = tk.Label(self.parent, text= name)
        self.strm_status = tk.Label(self.parent, text = "The stream is currently borked!")
        self.disp_views = tk.Label(self.parent, text = "Views: Not working")
        self.disp_game = tk.Label(self.parent, text = "Game: Not working")
        self.disp_desc = tk.Label(self.parent, text = "Status: Not working")
        self.disp_viewers = tk.Label(self.parent, text = "Viewers: Not working")

        self.disp_name.pack()
        self.strm_status.pack()
        self.disp_views.pack()
        self.disp_game.pack()
        self.disp_desc.pack()
        self.disp_viewers.pack()

        chat_btn = ttk.Button(self.parent, text= "Chat", command= lambda: chat()).pack()

        if len(url) > 38 and len(auth) > 0:
            self.update_thread()
            self.update(parent)
        else:
            self.check_user(self.master)


    #This class will destory and start the main tkinter window to update stats
    def refresh(self):
        self.master.destroy()
        dash_win()

    #This class will update the stats automatically
    def update(self, parent):
        #fix the except don't let it just pass thats not how it works
        self.disp_viewers
        cfg = ConfigParser()
        cfg.read("config.ini")
        user_name = cfg.get("user", "user_name")

        while self.queue_viewers.qsize():
            try:
                viewers = self.queue_viewers.get()
                self.disp_viewers["text"] = viewers

                desc = self.queue_desc.get()
                if self.disp_desc["text"] != desc:
                    if lambda: self.master.config(cursor="wait"):
                        self.master.config(cursor="")
                        self.disp_name["text"] = "Channel name: " + user_name
                    else:
                        pass
                self.disp_desc["text"] = desc

                game = self.queue_game.get()
                self.disp_game["text"] = game

                views = self.queue_views.get()
                self.disp_views["text"] = views

                status = self.queue_status.get()
                self.strm_status["text"] = status
            except:
                pass
        #after 1 minute the function will run again updating the viewer count
        #It is also in another thread to prevent the window from freezing
        self.thread = threading.Thread(target= self.update_thread)
        self.thread.start()
        parent.after(15000, self.update, parent)

    #This is the class used to start a new thread so the tkinter window doesn't freeze
    def update_thread(self):
        cfg = ConfigParser()
        cfg.read("config.ini")
        user_name = cfg.get("user", "user_name")
        client_id = cfg.get("user", "oauth").split(":")[1]
        url_strm = "https://api.twitch.tv/kraken/streams/" + user_name
        req = urllib.request.Request(url_strm)
        req.add_header("Client-ID", client_id)
        resp = urllib.request.urlopen(req)
        data = resp.read()

        #response_stm = urlopen(url_strm).read()
        data_stm = loads(data.decode())

        if data_stm["stream"]:
            viewers = "Viewers: " + str(data_stm["stream"]["viewers"])
            self.queue_viewers.put(viewers)

            desc = "Description: " + str(data_stm["stream"]["channel"]["status"])
            self.queue_desc.put(desc)

            game = "Game: " + str(data_stm["stream"]["channel"]["game"])
            self.queue_game.put(game)

            views = "Views: " + str(data_stm["stream"]["channel"]["views"])
            self.queue_views.put(views)

            strm_status_on = ("The stream is currently online")
            self.queue_status.put(strm_status_on)

        else:
            offline_viewers = "Viewers: "
            self.queue_viewers.put(offline_viewers)

            offline_status = "Description: "
            self.queue_desc.put(offline_status)

            offline_game = "Game: "
            self.queue_game.put(offline_game)

            offline_views = "Views: "
            self.queue_views.put(offline_views)

            strm_status_off = ("The stream is currently offline")
            self.queue_status.put(strm_status_off)

    def check_user(self, master):
        self.master = master
        cfg = ConfigParser()
        cfg.read("config.ini")
        try:
            if cfg["user"]["user_name"] == "" and cfg["user"]["oauth"] == "":
                user_oauth(self, self.master)
                print("boop")
            else:
                if cfg["user"]["user_name"] == "":
                    user_or_auth(self.master, "Channel name", "user_name")

                if cfg["user"]["oauth"] == "":
                    user_or_auth(self.master, "oauth", "oauth")

        except:
            user_oauth(self.master)

class user_oauth(object):
    def __init__(self, master):
        self.top = tk.Toplevel()
        cnl_name = tk.Label(self.top, text="Channel name").pack()
        entry_user = tk.Entry(self.top, width="30")
        cnl_auth = tk.Label(self.top, text="oauth").pack()
        entry_auth = tk.Entry(self.top, width="30")

        entry_user.pack()
        entry_auth.pack()
        sudmit = tk.Button(self.top, text="Submit", command= lambda: user_oauth.add_to_file(self, entry_user, entry_auth)).pack()

    def add_to_file(self, entry_user, entry_auth, top):
        self.entry_user = entry_user
        self.entry_auth = entry_auth
        entry = self.entry_user.get()
        auth = self.entry_auth.get()
        wrt_user = str(entry)

        cfg = ConfigParser()
        cfg.read("config.ini")

        open_file = open("config.ini", "w")
        cfg["user"] = {}
        cfg["user"]["user_name"] = wrt_user
        cfg["user"]["oauth"] = auth
        with open_file as configfile:
            cfg.write(configfile)
        open_file.close()
        self.top.destroy()

class user_or_auth(object):
    def __init__(self, master, text, mode):
        self.top = tk.Toplevel()
        cnl_name = tk.Label(self.top, text=text).pack()

        entry_user = tk.Entry(self.top, width="30")

        entry_user.pack()
        sudmit = tk.Button(self.top, text="Submit", command= lambda: add_to_file(master, entry_user, mode, self.top)).pack()

class add_to_file(object):
    def __init__(self, master, entry, mode, top):
        entry_get = entry.get()
        cfg = ConfigParser()
        cfg.read("config.ini")
        cfg.set("user", mode, entry_get)
        with open("config.ini", "w") as config:
            cfg.write(config)
        top.destroy()
        master.config(cursor="wait")
        #start the loading circle here and try and wipe the variables

#This class shows the chat
#Add a scrollbar to the chat box
class chat(object):
    def __init__(self):
        self.top = tk.Toplevel()
        self.queue = queue.Queue()
        self.queue_view = queue.Queue()
        self.queue_mods = queue.Queue()

        self.text_box = tk.Text(self.top, height = 30, width = 30)
        self.view_box = tk.Text(self.top, height = 30, width = 30)
        self.submit = ttk.Button(self.top, text= "send", command= lambda: chat.send_message(self))
        self.talk = tk.Entry(self.top)

        self.text_box.grid(row = 0, column = 1)
        self.view_box.grid(row = 0, column = 2)
        self.talk.grid(row = 1, column = 1)
        self.submit.grid(row = 2, column = 1)

        self.talk.bind("<Return>", lambda _: chat.send_message(self))

        self.list_wrk(self.top)

        self.thread2 = threading.Thread(target= self.chat_wrk())
        self.thread2.start()

        self.thread3 = threading.Thread(target= self.chat_irc)
        self.thread3.start()

    def chat_wrk(self):
        while self.queue.qsize():
            try:
                msg = self.queue.get()
                self.text_box.insert("end", msg+"\n")
            except:
                pass
        self.top.after(15000, self.chat_wrk)
        
    def chat_irc(self):
        cfg = ConfigParser()
        cfg.read("config.ini")
        user_name = cfg.get("user", "user_name")
        self.user_lwr = user_name.lower()
        user_auth = cfg.get("user", "oauth")

        host = "irc.twitch.tv"
        port = 6667
        auth = user_auth.lower()

        self.s = socket.socket()
        self.s.connect((host, port))
        self.s.send(bytes("PASS " + auth + "\r\n", "UTF-8"))
        self.s.send(bytes("NICK " + self.user_lwr + "\r\n", "UTF-8"))
        self.s.send(bytes("JOIN #" + self.user_lwr + "\r\n", "UTF-8"))

        while True:
            line = str(self.s.recv(1024))
            if "End of /NAMES list" in line:
                break

        while True:
            for line in str(self.s.recv(1024)).split('\\r\\n'):
                parts = line.split(':')
                if len(parts) < 3:
                    continue

                if "QUIT" not in parts[1] and "JOIN" not in parts[1] and "PART" not in parts[1]:
                    message = parts[2][:len(parts[2])]

                date = str(datetime.datetime.now().strftime("%I:%M"))
                usernamesplit = parts[1].split("!")
                username = usernamesplit[0]
                self.queue.put(date + " - " + username + ": " + message)
        self.top.after(15000, self.chat_irc)

    def send_message(self):
        entry_txt = self.talk.get()
        self.talk.delete("0", "end")
        date = str(datetime.datetime.now().strftime("%I:%M"))

        self.s.send(bytes("PRIVMSG #" + self.user_lwr + " :" + entry_txt + "\r\n", "UTF-8"))
        self.text_box.insert("end", date+" - " + self.user_lwr + ": "+entry_txt+"\n")

    def list_wrk(self, top):
        #think of a better way to do the viewer list not just delete the text
        self.view_box.delete("1.0", "end")
        self.top = top
        while self.queue_mods.qsize():
            try:
                msg = self.queue_mods.get()
                self.view_box.insert("end", "Mods: \n"+msg+"\n")

                msg1 = self.queue_view.get()
                self.view_box.insert("end", "\nViewers: \n"+msg1)
            except:
                pass
        self.thread1 = threading.Thread(target= self.viewer_list)
        self.thread1.start()
        top.after(15000, self.list_wrk, top)

    def viewer_list(self):
        cfg = ConfigParser()
        cfg.read("config.ini")
        user_name = cfg.get("user", "user_name")
        user_lwr = user_name.lower()
        url_strm = "https://tmi.twitch.tv/group/user/" + user_lwr + "/chatters"
        response_stm = urlopen(url_strm).read()
        data_stm = loads(response_stm.decode())

        if data_stm["chatters"]:
            mods = str(data_stm["chatters"]["moderators"]).strip("[]").replace("'", "").replace(" ", "\n").replace(",", "")
            viewers = str(data_stm["chatters"]["viewers"]).strip("[]").replace("'", "").replace(" ", "\n").replace(",", "")
        else:
            pass

        self.queue_mods.put(mods)
        self.queue_view.put(viewers)

app = dash_win()

