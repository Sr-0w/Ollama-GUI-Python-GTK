import gi
import requests
import json
import threading
from gi.repository import GLib
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

class OllamaChatWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Ollama GUI Python GTK")
        self.set_border_width(10)
        self.set_default_size(1200, 800)
        
        self.models = []  
        self.selected_model = None  
        self.chat_history = []  

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
        
        self.list_models_button = Gtk.Button(label="Select a model")
        self.list_models_button.connect("clicked", self.on_list_models_clicked)
        vbox.pack_start(self.list_models_button, False, True, 0)
        
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.textview)
        self.scrolled_window.set_sensitive(False)
        vbox.pack_start(scrolled_window, True, True, 0)
        
        textbuffer = self.textview.get_buffer()
        self.user_tag = textbuffer.create_tag("user_style", foreground="#ff7575", weight=Pango.Weight.BOLD)
        self.ollama_tag = textbuffer.create_tag("ollama_style", foreground="#ADD8E6", weight=Pango.Weight.BOLD)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.pack_start(hbox, False, True, 0)
        
        self.entry = Gtk.Entry()
        self.entry.connect("activate", self.on_send_clicked)
        self.entry.set_sensitive(False)
        hbox.pack_start(self.entry, True, True, 0)
        
        self.send_button = Gtk.Button()
        self.send_button.set_sensitive(False)
        send_icon = Gtk.Image.new_from_icon_name("mail-send-symbolic", Gtk.IconSize.BUTTON)
        self.send_button.set_image(send_icon)
        self.send_button.connect("clicked", self.on_send_clicked)
        hbox.pack_start(self.send_button, False, True, 0)
        
        self.save_button = Gtk.Button(label="Save history")
        self.save_button.connect("clicked", self.on_save_clicked)
        self.save_button.set_sensitive(False)
        vbox.pack_start(self.save_button, False, True, 0)

    def on_send_clicked(self, widget):
        message = self.entry.get_text().strip()
        if not message or not self.selected_model:
            print("Nothing to send or model not defined")
            return

        self.chat_history.append({"role": "user", "content": message})
        GLib.idle_add(self.append_text, "User : ", message + "\n", "user")
        self.entry.set_text("")
        threading.Thread(target=self.send_message, args=(message,), daemon=True).start()

    def send_message(self, message):
        url = "http://localhost:11434/api/chat"
        data = {
            "model": self.selected_model,
            "messages": self.chat_history,
            "prompt": message, 
            "stream": True
        }
        headers = {'Content-Type': 'application/json'}
        self.prefix_added = False  

        try:
            with requests.post(url, data=json.dumps(data), headers=headers, stream=True) as r:
                if r.status_code == 200:
                    for line in r.iter_lines():
                        if line:
                            decoded_line = json.loads(line.decode('utf-8'))
                            response_text = decoded_line.get("message", {}).get("content", "")
                            if response_text and not self.prefix_added:
                                
                                GLib.idle_add(self.append_text, "", "\n", "normal")
                                GLib.idle_add(self.append_text, "Ollama : ", response_text, "ollama")
                                self.prefix_added = True
                            elif response_text:
                                
                                GLib.idle_add(self.append_text, "", response_text, "normal")
                            
                            if decoded_line.get("done", False):
                                
                                GLib.idle_add(self.append_text, "", "\n\n", "normal") 
                                print("Génération terminée")
                                break 
                else:
                    print(f"Error - Server answer : {r.status_code}")
        except Exception as e:
            print(f"Error while sending the message: {e}")

    def append_text(self, prefix, message, sender):
        buffer = self.textview.get_buffer()
        end_iter = buffer.get_end_iter()
    
       
        if prefix:
            if sender == "user":
                buffer.insert_with_tags(end_iter, prefix, self.user_tag)
            elif sender == "ollama":
                buffer.insert_with_tags(end_iter, prefix, self.ollama_tag)
        
        
        buffer.insert(end_iter, message)
        
        
        adj = self.textview.get_parent().get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
    
    def on_list_models_clicked(self, widget):
        url = "http://localhost:11434/api/tags"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                models_data = response.json()
                self.models = models_data.get('models', [])
                models_names = [model['name'] for model in self.models]
                
                
                dialog = Gtk.Dialog(title="Select a model", parent=self,
                                    flags=Gtk.DialogFlags.MODAL,
                                    buttons=("Cancel", Gtk.ResponseType.CANCEL,
                                             "Select", Gtk.ResponseType.OK))
                dialog.set_default_size(400, 100)
                
                combo = Gtk.ComboBoxText()
                for name in models_names:
                    combo.append_text(name)
                combo.set_active(0)
                box = dialog.get_content_area()
                box.add(combo)
                dialog.show_all()
                
                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    self.selected_model = combo.get_active_text()
                    self.list_models_button.set_label(f"Model : {self.selected_model}")
                    self.send_button.set_sensitive(True)
                    self.save_button.set_sensitive(True)
                    self.entry.set_sensitive(True)
                    self.scrolled_window.set_sensitive(True)
                dialog.destroy()
            else:
                print(f"Error - Server answer : {response.status_code}")
        except Exception as e:
            print(f"Error while fetching models: {e}")

    def show_models_dialog(self, models_names):
        dialog = Gtk.Dialog("Select a model", self, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        combo = Gtk.ComboBoxText()
        for name in models_names:
            combo.append_text(name)
        combo.set_active(0)
        box = dialog.get_content_area()
        box.add(combo)
        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.selected_model = combo.get_active_text()
            print(f"Selected model : {self.selected_model}")  
        dialog.destroy()
        
    def on_save_clicked(self, widget):
        
        dialog = Gtk.FileChooserDialog("Select a file to save history to", self,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        dialog.set_do_overwrite_confirmation(True)  
    
       
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()  
            self.save_discussion(filename)  
        dialog.destroy()
    
    def save_discussion(self, filename):
        buffer = self.textview.get_buffer()
        start_iter, end_iter = buffer.get_bounds()
        text = buffer.get_text(start_iter, end_iter, True)  
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)  


if __name__ == "__main__":
    win = OllamaChatWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

