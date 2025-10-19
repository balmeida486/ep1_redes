import os
import sys

from threading import Thread

from src.exceptions.InvalidDirectoryException import InvalidDirectoryException
from src.main import init_server, menu, handle_list_peers, load_peers, handle_show_stats

if __name__ == "__main__":
    try:
        address, txt, shared_dir = (
            sys.argv[1], sys.argv[2], sys.argv[3])

        server = init_server(
            address=address, shared_dir=shared_dir, peers=load_peers(path=txt))

        t = Thread(target=server.listen)
        t.start()

        running = True
        while running:
            opt = menu()
            if opt == 1:
                handle_list_peers(server=server)
            elif opt == 2:
                server.find_peers()
            elif opt == 3:
                files = os.listdir(shared_dir)
                print("\n".join(files))
            elif opt == 4:
                server.search_files()
            elif opt == 5:
                handle_show_stats(server=server)
            elif opt == 6:
                print("Digite o novo tamanho do chunk")
                new_chunk_size = int(input("> "))
                server.chunk_size = new_chunk_size
                print(f"Tamanho de chunk alterado: {new_chunk_size}")
            elif opt == 9:
                running = False
                server.shutdown()

    except InvalidDirectoryException:
        print("=> Diretório inválido")
    except KeyboardInterrupt:
        print("=> Programa finalizado")
    except Exception as err:
        print(f"Ocorreu um erro inesperado: {err}")
