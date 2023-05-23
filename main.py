import argparse
import os
import shutil
import send2trash
import sys
import platform
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
    # Dam display la meniul CLI-ului
    print("File System CLI Menu:")
    print("1. Create Directory")
    print("2. Create File")
    print("3. Delete File or Directory")
    print("4. Rename File")
    print("5. Move File")
    print("6. Print Current Directory")
    print("7. Exit")



def move_file(old_path, new_path):
    # Mută un fișier sau director dintr-un loc în altul
    try:
        if os.path.isfile(old_path) or os.path.isdir(old_path):
            shutil.move(old_path, new_path)
            print(f"Moved: {old_path} -> {new_path}")
        else:
            print(f"File or directory not found: {old_path}")
    except shutil.Error as e:
        print(f"Error occurred while moving file or directory: {e}")

def rename_file(old_path, new_path):
   # Redenumește un fișier sau director
    try:
        if os.path.isfile(old_path) or os.path.isdir(old_path):
            os.rename(old_path, new_path)
            print(f"Renamed: {old_path} -> {new_path}")
        else:
            print(f"File or directory not found: {old_path}")
    except OSError as e:
        print(f"Error occurred while renaming file or directory: {e}")

def create_directory(path):
    # Creează un director nou
    try:
        os.mkdir(path)
        print(f"Created directory: {path}")
    except FileExistsError:
        print(f"Directory already exists: {path}")
    except OSError as e:
        print(f"Error occurred while creating directory: {e}")



def delete_file(path):
    # Șterge un fișier sau un director și îl mută în coșul de gunoi corespunzător
    try:
        if os.path.isfile(path):
            if platform.system() == "Darwin":  # macOS
                send2trash.send2trash(path)
                print(f"File moved to Trash: {path}")
            elif platform.system() == "Windows":  # Windows
                # Se da send to Recycle bin folosing send2trash module
                send2trash.send2trash(path)
                print(f"File moved to Recycle Bin: {path}")
            else:
                # Pentru alte platforme, se da permanenet delete
                os.remove(path)
                print(f"File permanently deleted: {path}")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Directory deleted: {path}")
        else:
            print(f"File or directory not found: {path}")
    except OSError as e:
        print(f"Error occurred while deleting file or directory: {e}")


def handle_menu_choice(choice):
    # Alegerea meniului CLI
    if choice == "1":
        path = input("Enter the directory path to create: ")
        create_directory(path)
    elif choice == "2":
        path = input("Enter the file path to create: ")
        create_file(path)
    elif choice == "3":
        path = input("Enter the file or directory path to delete: ")
        delete_file(path)
    elif choice == "4":
        old_path = input("Enter the path of the file to rename: ")
        new_path = input("Enter the new name or path for the file: ")
        rename_file(old_path, new_path)
    elif choice == "5":
        old_path = input("Enter the path of the file to move: ")
        new_path = input("Enter the new path for the file: ")
        move_file(old_path, new_path)
    elif choice == "6":
        print(f"Current Directory: {os.getcwd()}")
    elif choice == "7":
        print("Exiting...")
        return True
    else:
        print("Invalid choice. Please try again.")

    print()  # Lasam o linie pt vizibilitate


# definim o structura FAT
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


def create_file2(storage_medium, filename, extension):
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


def create_file(path):
    # Create a new file
    try:
        with open(path, "w") as file:
            print(f"Created file: {path}")
    except FileExistsError:
        print(f"File already exists: {path}")
    except OSError as e:
        print(f"Error occurred while creating file: {e}")



def main():
    while True:
        print_menu()
        choice = input("Enter your choice (1-6): ")
        exit_requested = handle_menu_choice(choice)
        if exit_requested:
            break

if __name__ == "__main__":
    main()
