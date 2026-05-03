def merge_files(file_list, output_filename):
    separator = "\n" + "_" * 20 + "\n"
    try:
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            for i, filename in enumerate(file_list):
                try:
                    with open(filename, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        
                        if i < len(file_list) - 1:
                            outfile.write(separator)
                            
                    print(f"Dodano: {filename}")
                except FileNotFoundError:
                    print(f"Błąd: Plik {filename} nie istnieje. Pomijam.")
                except Exception as e:
                    print(f"Błąd przy pliku {filename}: {e}")
                    
        print(f"\nSukces! Wszystko połączone w pliku: {output_filename}")

    except Exception as e:
        print(f"Błąd krytyczny: {e}")


pliki_do_polaczenia = [
    'app/__init__.py',
    'app/__main__.py',
    'app/db.py',
    'app/main.py',
    'app/schemas.py',
    'app/services.py',

    'tests/test_api.py',

    'Dockerfile',
    'docker-compose.yml',
    'requirements.txt',
    'README.md'
    ]
nazwa_wynikowa = 'merge.txt'

if __name__ == "__main__":
    merge_files(pliki_do_polaczenia, nazwa_wynikowa)