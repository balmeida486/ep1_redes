# Estrutura, decisões e bibliotecas utilizadas – Projeto PeerAre

## 📁 Estrutura do Projeto

O projeto está organizado de forma modular para facilitar a leitura, manutenção e evolução do código. A estrutura segue a separação entre responsabilidades:

```
peerare/
├── src/
│   ├── main.py                # Funções auxiliares, carregamento de peers, menu e interação do usuário
│   ├── models/
│   │   ├── server.py          # Classe responsável por escutar conexões e enviar mensagens entre peers
│   │   ├── clock.py           # Relógio lógico Lamport simples para ordenação de eventos
│   │   ├── peer.py            # Representação do peer remoto e enumeração de status (Online/Offline)
│   │   ├── buffer.py          # Responsável por fazer leitura das mensagens com caracter delimitador
│   │   └── message.py         # Parsing e estrutura de mensagens trocadas entre peers
│   └── exceptions.py          # Definição de exceções customizadas como diretório inválido
├── peers.txt                  # Arquivo com a lista de peers conhecidos no formato host:port
└── __main__.py                # Ponto de entrada principal da aplicação
```

Essa estrutura permite a extensão futura para funcionalidades como transferência de arquivos, cache de metadados, gerenciamento de chunks, etc.

---

## 💡 Decisões de Projeto

- **Sockets TCP com threading**: O servidor utiliza `socket` da biblioteca padrão Python para comunicação entre peers via TCP. Cada nova conexão é tratada em uma `Thread` separada para permitir múltiplas conexões simultâneas.
- **Formato de mensagem simples e legível**: As mensagens seguem o padrão `<host>:<port> <clock> <comando> [args...]`, facilitando o parsing e leitura durante debug.
- **Relógio lógico Lamport simplificado**: Cada peer possui um contador local incrementado a cada envio ou recebimento de mensagem, permitindo rastrear a ordem dos eventos.
- **Desacoplamento de responsabilidades**: Cada entidade principal do sistema (`Server`, `Peer`, `Message`, `Clock`, `Buffer`) foi encapsulada em sua própria classe, promovendo reuso e organização.
- **Evita loops de resposta**: O sistema identifica e ignora a si mesmo na hora de responder a comandos como `GET_PEERS`, evitando envio desnecessário.

---

## 📚 Bibliotecas utilizadas

- **socket (built-in)**: Comunicação TCP entre peers.
- **threading (built-in)**: Permite tratar múltiplas conexões simultâneas sem bloquear o servidor.
- **os (built-in)**: Verificação de diretório compartilhado.
- **typing (built-in)**: Tipagem estática para facilitar leitura e prevenir erros em tempo de desenvolvimento.
- **enum (built-in)**: Representação clara dos status dos peers.

Nenhuma biblioteca externa foi utilizada, reforçando o foco didático e o entendimento de baixo nível da comunicação entre processos em rede.

---

## Como as escolhas feitas na implementação das partes anteriores influenciaram as alterações necessárias para a parte 3?

Nas partes anteriores, a implementação estabelecia uma nova conexão para cada mensagem enviada, fechando-a logo em seguida. Esse modelo, porém, se mostrou inviável no envio de arquivos em chunks, pois para arquivos grandes — combinados com chunks pequenos — isso resultava na abertura e fechamento de um grande número de conexões em um curto espaço de tempo. Como consequência, o sistema operacional acabava bloqueando ou limitando o fluxo devido ao uso excessivo de sockets em estados `TIME_WAIT`.

Para resolver isso na parte 3, foi necessário revisar a arquitetura de comunicação, passando a manter conexões persistentes entre os peers. Isso exigiu também uma alteração na forma de interpretar os dados recebidos, já que uma conexão agora poderia transportar múltiplas mensagens e até mensagens parciais. Para isso, introduzimos o uso de um marcador de fim de mensagem, permitindo identificar corretamente os limites entre as mensagens e reconstruí-las mesmo em streams contínuos.

## Quais testes foram feitos?

| Tam. chunk | N peers | Tam. arquivo | N   | Tempo[s]                                                                          | Desvio                 |
| ---------- | ------- | ------------ | --- | --------------------------------------------------------------------------------- | ---------------------- |
| 128        | 2       | 10724027     | 3   | 6.811985015869141, 6.734224796295166, 6.727044105529785                           | 0.03846090701729802    |
| 128        | 3       | 10724027     | 3   | 5.652906894683838, 5.601557731628418, 5.578650236129761                           | 0.03104752850448254    |
| 256        | 2       | 10724027     | 3   | 3.403973340988159, 3.378394842147827, 3.3563661575317383                          | 0.019453552847440072   |
| 256        | 3       | 10724027     | 3   | 2.8958590030670166, 2.901582956314087, 2.9138782024383545                         | 0.00751759612889791    |
| 512        | 2       | 10724027     | 3   | 1.7461919784545898, 1.7444000244140625, 1.741852045059204                         | 0.0017807089709354939  |
| 512        | 3       | 10724027     | 3   | 1.5717191696166992, 1.5461339950561523, 1.5304450988769531                        | 0.017010753252787263   |
| 1024       | 2       | 10724027     | 3   | 0.9488351345062256, 0.9647998809814453, 0.9662559032440186                        | 0.007891460322982154   |
| 1024       | 3       | 10724027     | 4   | 0.9568688869476318, 0.9607670307159424, 0.961806058883667, 0.9575700759887695     | 0.0020812632549515593  |
| 2048       | 2       | 10724027     | 3   | 0.6071569919586182, 0.6107649803161621, 0.6122238636016846                        | 0.0021296611278756148  |
| 2048       | 3       | 10724027     | 3   | 0.5929937362670898, 0.605597734451294, 0.6021828651428223                         | 0.005322511856008731   |
| 5096       | 2       | 10724027     | 3   | 0.4542109966278076, 0.4534778594970703, 0.44942378997802734                       | 0.0021052927277433017  |
| 5096       | 3       | 10724027     | 3   | 0.45288681983947754, 0.4529259204864502, 0.4520759582519531                       | 0.00039178525506647783 |
| 128        | 2       | 95565        | 3   | 0.06217813491821289, 0.06168079376220703, 0.061650991439819336                    | 0.00024177966339665558 |
| 128        | 3       | 95565        | 3   | 0.05117392539978027, 0.051867008209228516, 0.052095890045166016                   | 0.0003919707306130631  |
| 256        | 2       | 95565        | 3   | 0.031116962432861328, 0.030819177627563477, 0.030633926391601562                  | 0.00019897448966795333 |
| 256        | 3       | 95565        | 3   | 0.026628971099853516, 0.02734827995300293, 0.025639772415161133                   | 0.0007003901508666044  |
| 512        | 2       | 95565        | 3   | 0.01694178581237793, 0.0161130428314209, 0.015139102935791016                     | 0.0007367375080813129  |
| 512        | 3       | 95565        | 3   | 0.014165878295898438, 0.013740062713623047, 0.013847112655639648                  | 0.00018085910218973203 |
| 1024       | 3       | 95565        | 3   | 0.008209943771362305, 0.008748054504394531, 0.008774042129516602                  | 0.0002600097167706406  |
| 1024       | 2       | 95565        | 3   | 0.007860183715820312, 0.008744239807128906, 0.008752107620239258                  | 0.00041861482247167186 |
| 2048       | 2       | 95565        | 4   | 0.005054950714111328, 0.005124092102050781, 0.0052490234375, 0.005089998245239258 | 7.320020677516432e-05  |
| 5096       | 2       | 95565        | 3   | 0.0030431747436523438, 0.0030279159545898438, 0.003074169158935547                | 1.9243594416633223e-05 |
| 5096       | 3       | 95565        | 3   | 0.00485992431640625, 0.0030241012573242188, 0.0031549930572509766                 | 0.0008362727868338815  |

## Como foi feita a distribuição de chunks entre os peers disponíveis?

A distribuição dos chunks entre os peers disponíveis foi implementada utilizando a estratégia de `round-robin` (fila circular). Para cada chunk a ser baixado, o sistema selecionava sequencialmente o próximo peer da lista de peers que possuíam o arquivo. Ao atingir o final da lista, o processo reiniciava a partir do primeiro peer, garantindo assim uma distribuição equilibrada e uniforme dos chunks entre todos os peers disponíveis.

Essa abordagem, apesar de simples, mostrou-se eficaz para o cenário da aplicação, pois:

- Permite um balanceamento natural da carga entre os peers.
- Evita que um único peer seja sobrecarregado.
- Reduz o tempo total de download ao explorar o paralelismo da rede.

## Como foi medido o tempo de download?

O tempo de download foi medido da seguinte forma:

- No momento em que foi iniciada a solicitação de download do arquivo (ou seja, quando os chunks começaram a ser requisitados aos peers), foi salvo no estado do servidor um timestamp de início, obtido com a função time.time() da biblioteca padrão do Python.
- Quando foi detectado que todos os chunks haviam sido recebidos (ou seja, o download estava completo), foi feita a subtração entre o timestamp atual `(time.time())` e o timestamp salvo no início da requisição.
- O resultado dessa subtração corresponde ao tempo total de download do arquivo, em segundos, com precisão de casas decimais.

## Resultados de experimentos

Os testes realizados buscaram avaliar o impacto de diferentes escolhas de implementação na performance do sistema de envio de arquivos em chunks. A partir dos resultados obtidos, foi possível perceber os seguintes comportamentos:

#### Chunks pequenos (128, 256):

- Aumentaram significativamente o tempo total de download, devido ao maior overhead de controle e número de mensagens trocadas.
- Apresentaram maior desvio padrão, com tempos mais instáveis e sujeitos à variação do sistema operacional.

#### Chunks maiores (1024, 2048, 5096):

- Reduziram substancialmente o tempo de download.
- Proporcionaram transmissões mais estáveis, com desvios padrão menores.
- A partir de um certo tamanho (~2048), o ganho adicional se estabilizou, indicando um “ponto ótimo”.

#### Número de peers:

- O uso de 3 peers foi mais vantajoso em arquivos grandes, pois permitiu maior paralelismo na transferência dos chunks.
- Em arquivos pequenos, o benefício de adicionar mais peers foi menos perceptível, pois o tempo de coordenação passa a ser relevante em relação ao tempo de transmissão.

#### Estabilidade do protocolo:

- A arquitetura com conexões persistentes e uso de marcador de fim de mensagem permitiu transmitir múltiplos chunks por conexão de forma confiável.
- Não foram observados problemas de perda ou corrompimento de mensagens, mesmo com variação no tamanho do chunk e no número de peers.

Em resumo, os testes demonstraram que a escolha do tamanho de chunk tem grande impacto na performance do sistema. Também ficou claro que o uso de conexões persistentes foi essencial para garantir a estabilidade e a viabilidade da transmissão em chunks, evitando problemas que seriam causados por excesso de aberturas/fechamentos de conexões. O sistema se comportou de forma robusta, escalando bem com o número de peers e com diferentes tamanhos de arquivos.

## Como rodar o projeto

O repositório inclui arquivos de exemplo para facilitar a execução e os testes do projeto. São eles:

- `9001.txt`
- `9002.txt`
- `9003.txt`
- `9004.txt`

Cada um desses arquivos contém a lista de peers conhecidos para cada instância do peer.

### Regras para execução

- **Porta e arquivo de peers:**  
  É recomendado que a porta utilizada para cada peer corresponda ao número no nome do arquivo.  
  Por exemplo:

  - Arquivo `9001.txt` → usar porta `9001`
  - Arquivo `9002.txt` → usar porta `9002`
  - E assim por diante.

- **Pasta compartilhada:**  
  O último parâmetro na execução é o caminho da pasta que será compartilhada com os outros peers.  
  Este caminho pode ser:
  - **Relativo:** por exemplo `./shared_folder`
  - **Absoluto:** por exemplo `/home/user/shared_folder`

### Exemplo de execução

Para iniciar um peer na porta `9001`, utilizando o arquivo `9001.txt` e compartilhando a pasta `../`, o comando seria:

```bash
python3 __main__.py 127.0.0.1:9001 9001.txt ../
```

### Observações

- Você pode criar **novos arquivos `.txt`** com a lista de peers desejada, caso queira rodar mais instâncias do cliente (mais peers).
- É recomendado que **ao menos um dos peers utilize uma pasta compartilhada diferente dos demais**.  
  Isso facilita a visualização das diferenças ao listar os arquivos disponíveis na rede e também durante os testes de download.
