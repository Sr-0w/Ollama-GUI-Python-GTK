import gi
import requests
import json
import threading
from gi.repository import GLib
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

class OllamaChatWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Chat avec Ollama")
        self.set_border_width(10)
        self.set_default_size(1200, 800)
        
        self.models = []  # Liste pour stocker les modèles disponibles
        self.selected_model = None  # Modèle actuellement sélectionné
        self.chat_history = []  # Historique de chat pour conservation des messages envoyés et reçus

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
        
        self.list_models_button = Gtk.Button(label="Sélectionner un modèle")
        self.list_models_button.connect("clicked", self.on_list_models_clicked)
        vbox.pack_start(self.list_models_button, False, True, 0)
        
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.textview)
        vbox.pack_start(scrolled_window, True, True, 0)
        
        textbuffer = self.textview.get_buffer()
        self.user_tag = textbuffer.create_tag("user_style", foreground="#ff7575", weight=Pango.Weight.BOLD)
        self.ollama_tag = textbuffer.create_tag("ollama_style", foreground="#ADD8E6", weight=Pango.Weight.BOLD)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.pack_start(hbox, False, True, 0)
        
        self.entry = Gtk.Entry()
        self.entry.connect("activate", self.on_send_clicked)
        hbox.pack_start(self.entry, True, True, 0)
        
        self.send_button = Gtk.Button()
        self.send_button.set_sensitive(False)
        send_icon = Gtk.Image.new_from_icon_name("mail-send-symbolic", Gtk.IconSize.BUTTON)
        self.send_button.set_image(send_icon)
        self.send_button.connect("clicked", self.on_send_clicked)
        hbox.pack_start(self.send_button, False, True, 0)
        
        self.save_button = Gtk.Button(label="Sauvegarder")
        self.save_button.connect("clicked", self.on_save_clicked)
        self.save_button.set_sensitive(False)
        vbox.pack_start(self.save_button, False, True, 0)

    def on_send_clicked(self, widget):
        message = self.entry.get_text().strip()
        if not message or not self.selected_model:
            print("Aucun message à envoyer ou modèle non sélectionné.")
            return

        # Ajouter le message actuel à l'historique avant d'envoyer
        self.chat_history.append({"role": "user", "content": message})
        GLib.idle_add(self.append_text, "User : ", message + "\n", "user")
        self.entry.set_text("")
        threading.Thread(target=self.send_message, args=(message,), daemon=True).start()

    def send_message(self, message):
        url = "http://localhost:11434/api/chat"
        data = {
            "model": self.selected_model,
            "messages": self.chat_history,
            "prompt": message,  # Ajout du prompt actuel en plus de l'historique
            "stream": True
        }
        headers = {'Content-Type': 'application/json'}
        self.prefix_added = False  # Réinitialisé pour chaque nouveau message

        try:
            with requests.post(url, data=json.dumps(data), headers=headers, stream=True) as r:
                if r.status_code == 200:
                    for line in r.iter_lines():
                        if line:
                            decoded_line = json.loads(line.decode('utf-8'))
                            response_text = decoded_line.get("message", {}).get("content", "")
                            if response_text and not self.prefix_added:
                                # Insérer "Ollama : " au début de la première partie de la réponse
                                GLib.idle_add(self.append_text, "", "\n", "normal")
                                GLib.idle_add(self.append_text, "Ollama : ", response_text, "ollama")
                                self.prefix_added = True
                            elif response_text:
                                # Insérer le reste de la réponse mot par mot sans préfixe
                                GLib.idle_add(self.append_text, "", response_text, "normal")
                            
                            if decoded_line.get("done", False):
                                # Une fois la réponse complète, ajoutez une ligne vide pour séparer
                                GLib.idle_add(self.append_text, "", "\n\n", "normal")  # Insérer une ligne vide après la réponse complète
                                print("Génération terminée")
                                break  # Sortie de la boucle si la réponse est terminée
                else:
                    print(f"Erreur: Réponse du serveur {r.status_code}")
        except Exception as e:
            print(f"Erreur lors de l'envoi du message: {e}")

    def append_text(self, prefix, message, sender):
        buffer = self.textview.get_buffer()
        end_iter = buffer.get_end_iter()
    
        # Insérer le préfixe avec style si nécessaire
        if prefix:
            if sender == "user":
                buffer.insert_with_tags(end_iter, prefix, self.user_tag)
            elif sender == "ollama":
                buffer.insert_with_tags(end_iter, prefix, self.ollama_tag)
        
        # Insérer le message normal sans style spécifique
        buffer.insert(end_iter, message)
        
        # Faire défiler automatiquement vers le bas
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
                
                # Ouvre une boîte de dialogue pour permettre à l'utilisateur de sélectionner un modèle
                dialog = Gtk.Dialog(title="Sélectionner un modèle", parent=self,
                                    flags=Gtk.DialogFlags.MODAL,
                                    buttons=("Annuler", Gtk.ResponseType.CANCEL,
                                             "Sélectionner", Gtk.ResponseType.OK))
                dialog.set_default_size(200, 100)
                
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
                    self.list_models_button.set_label(f"Modèle : {self.selected_model}")
                    self.send_button.set_sensitive(True)
                    self.save_button.set_sensitive(True)
                dialog.destroy()
            else:
                print(f"Erreur: Réponse du serveur {response.status_code}")
        except Exception as e:
            print(f"Erreur lors de la récupération des modèles: {e}")

    def show_models_dialog(self, models_names):
        dialog = Gtk.Dialog("Sélectionner un modèle", self, 0,
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
            print(f"Modèle sélectionné : {self.selected_model}")  # Pour vérification
        dialog.destroy()
        
    def on_save_clicked(self, widget):
        # Créer un dialogue de sélection de fichier pour la sauvegarde
        dialog = Gtk.FileChooserDialog("Choisir un fichier pour sauvegarder", self,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        dialog.set_do_overwrite_confirmation(True)  # Confirmer si le fichier existe déjà
    
        # Ajouter des filtres pour le type de fichier (optionnel)
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Fichiers texte")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        # Montrer le dialogue et attendre une réponse
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()  # Obtenir le nom du fichier choisi
            self.save_discussion(filename)  # Appeler la méthode pour sauvegarder la discussion
        dialog.destroy()
    
    def save_discussion(self, filename):
        buffer = self.textview.get_buffer()
        start_iter, end_iter = buffer.get_bounds()
        text = buffer.get_text(start_iter, end_iter, True)  # Récupérer le texte du buffer
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)  # Écrire le texte dans le fichier


if __name__ == "__main__":
    win = OllamaChatWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

