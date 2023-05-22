import argparse
import os
import shutil
import sys
from datetime import datetime


class AllocationChain:
    def __init__(self):
        self.cluster_indices = []  # Indicii clusterelor în lanțul de alocare


class FileEntry:
    def __init__(self, name, extension, size, created_time, modified_time, start_cluster):
        self.name = name  # Numele fișierului
        self.extension = extension  # Extensia fișierului
        self.size = size  # Mărimea fișierului
        self.created_time = created_time  # Timpul de creare al fișierului
        self.modified_time = modified_time  # Timpul de modificare al fișierului
        self.start_cluster = start_cluster  # Clusterul de start al fișierului


class FAT:
    def __init__(self, num_clusters):
        self.num_clusters = num_clusters  # Numărul de clustere
        self.entries = [0] * num_clusters  # Intrările din tabelul FAT


class Root:
    def __init__(self):
        self.entries = {}  # Intrările din directorul rădăcină


class StorageMedium:
    def __init__(self, size_in_bytes):
        self.data = bytearray(size_in_bytes)  # Datele stocate în mediul de stocare


def update_fat(fat, start_cluster, num_clusters):
    for i in range(num_clusters):
        fat.entries[start_cluster + i] = start_cluster + i + 1  # Actualizează intrările tabelului FAT pentru clusterele allocate
    fat.entries[start_cluster + num_clusters - 1] = 0  # Ultimul cluster allocate va avea următorul cluster setat la 0 (semnificație de sfârșit de fișier)


def add_to_root(root, name, is_directory, size, created_time, modified_time, start_cluster):
    entry = FileEntry(name, "", size, created_time, modified_time, start_cluster)  # Creează o intrare pentru fișierul nou
    root.entries[name] = entry  # Adaugă intrarea în directorul rădăcină


def read_data(storage_medium, start_offset, num_bytes):
    return storage_medium.data[start_offset:start_offset + num_bytes]  # Citește datele de la offset-ul specificat


def write_data(storage_medium, start_offset, data):
    storage_medium.data[start_offset:start_offset + len(data)] = data  # Scrie datele la offset-ul specificat


def print_menu():
    print("File System CLI Menu:")  # Meniul interactiv al sistemului de fișiere
    print("1. Creează director")
    print("2. Șterge fișier sau director")
    print("3. Redenumește fișier")
    print("4. Muta fișier")
    print("5. Ieșire")


def create_directory(path):
    try:
        os.mkdir(path)  # Creează un director cu calea specificată
        print(f"Director creat: {path}")
    except FileExistsError:
        print(f"Directorul există deja: {path}")
    except OSError as e:
        print(f"A apărut o eroare la crearea directorului: {e}")


def delete_file(path):
    try:
        if os.path.isfile(path):
            os.remove(path)  # Șterge fișierul specificat
            print(f"Fișier șters: {path}")
        elif os.path.isdir(path):
            shutil.rmtree(path)  # Șterge directorul specificat și conținutul său
            print(f"Director șters: {path}")
        else:
            print(f"Fișierul sau directorul nu a fost găsit: {path}")
    except OSError as e:
        print(f"A apărut o eroare la ștergerea fișierului sau directorului: {e}")


def rename_file(old_path, new_path):
    try:
        if os.path.isfile(old_path) or os.path.isdir(old_path):
            os.rename(old_path, new_path)  # Redenumește fișierul sau directorul specificat
            print(f"Redenumit: {old_path} -> {new_path}")
        else:
            print(f"Fișierul sau directorul nu a fost găsit: {old_path}")
    except OSError as e:
        print(f"A apărut o eroare la redenumirea fișierului sau directorului: {e}")


def move_file(old_path, new_path):
    try:
        if os.path.isfile(old_path) or os.path.isdir(old_path):
            shutil.move(old_path, new_path)  # Muta fișierul sau directorul specificat
            print(f"Mutat: {old_path} -> {new_path}")
        else:
            print(f"Fișierul sau directorul nu a fost găsit: {old_path}")
    except shutil.Error as e:
        print(f"A apărut o eroare la mutarea fișierului sau directorului: {e}")


def handle_menu_choice(choice):
    if choice == "1":
        path = input("Introduceți calea directorului de creat: ")
        create_directory(path)
    elif choice == "2":
        path = input("Introduceți calea fișierului sau directorului de șters: ")
        delete_file(path)
    elif choice == "3":
        old_path = input("Introduceți calea fișierului de redenumit: ")
        new_path = input("Introduceți noul nume sau cale pentru fișier: ")
        rename_file(old_path, new_path)
    elif choice == "4":
        old_path = input("Introduceți calea fișierului de mutat: ")
        new_path = input("Introduceți noua cale pentru fișier: ")
        move_file(old_path, new_path)
    elif choice == "5":
        print("Ieșire...")
        return True
    else:
        print("Opțiune invalidă. Vă rugăm să încercați din nou.")

    print()  # Adaugă o linie goală pentru o mai bună lizibilitate


# define a structure for the FAT
class FATEntry:
    def __init__(self, used, next):
        self.used = used  # Indicator dacă clusterul este utilizat
        self.next = next  # Clusterul următor în lanțul de alocare


class RootDirectoryEntry:
    def __init__(self, filename, extension, attributes, time_created, date_created, time_last_modified,
                 date_last_modified, start_block):
        self.filename = filename  # Numele fișierului
        self.extension = extension  # Extensia fișierului
        self.attributes = attributes  # Atributele fișierului
        self.time_created = time_created  # Timpul de creare al fișierului
        self.date_created = date_created  # Data de creare a fișierului
        self.time_last_modified = time_last_modified  # Timpul ultimei modificări a fișierului
        self.date_last_modified = date_last_modified  # Data ultimei modificări a fișierului
        self.start_block = start_block  # Clusterul de start al fișierului


class StorageMedium:
    def __init__(self, total_blocks, used_blocks, free_blocks, fat, root_directory):
        self.total_blocks = total_blocks  # Numărul total de clustere
        self.used_blocks = used_blocks  # Numărul de clustere utilizate
        self.free_blocks = free_blocks  # Numărul de clustere libere
        self.fat = fat  # Tabelul FAT
        self.root_directory = root_directory  # Directorul rădăcină


def create_storage_medium(total_blocks):
    fat = [FATEntry(False, i + 1) for i in range(total_blocks - 1)]  # Inițializează tabelul FAT cu intrări inițiale
    fat.append(FATEntry(False, None))

    root_directory = []

    storage_medium = StorageMedium(total_blocks, 0, total_blocks, fat, root_directory)
    return storage_medium


def create_file(storage_medium, filename, extension):
    free_block = -1
    for i, fat_entry in enumerate(storage_medium.fat):
        if not fat_entry.used:
            free_block = i
            storage_medium.fat[i].used = True
            storage_medium.free_blocks -= 1
            storage_medium.used_blocks += 1
            break

    if free_block == -1:
        print("Nu există clustere libere disponibile. Nu se poate crea fișierul.")
        return

    file_entry = RootDirectoryEntry(
        filename,
        extension,
        attributes=None,
        time_created=None,
        date_created=None,
        time_last_modified=None,
        date_last_modified=None,
        start_block=free_block
    )
    storage_medium.root_directory.append(file_entry)

    print(f"Fișierul '{filename}.{extension}' a fost creat cu succes.")
    print(f"Clusterul de start: {free_block}")


def main():
    while True:
        print_menu()
        choice = input("Introduceți opțiunea (1-5): ")
        exit_requested = handle_menu_choice(choice)
        if exit_requested:
            break


if __name__ == "__main__":
    main()
