# Importando bibliotecas necessárias
import tkinter as tk
from tkinter import ttk
import json
import requests
from datetime import datetime
import random
import schedule
import time
import os

# Classe principal que gerencia as citações e interface


class GerenciadorCitacoes:
    def __init__(self):
        # Inicializa estruturas de dados
        self.citacoes = {}
        self.tema_atual = None
        self.citacao_do_dia = None
        self.ultima_atualizacao = None
        self.historico = []
        self.favoritos = []  # Lista para armazenar citações favoritas
        self.citacoes_diarias = {}  # Dicionário para armazenar citações diárias por categoria

        # URLs base das APIs
        self.quote_garden_api = "https://quote-garden.onrender.com/api/v3"
        self.forismatic_api = "http://api.forismatic.com/api/1.0/"

        # Obtém o diretório do arquivo atual
        self.diretorio_base = os.path.dirname(os.path.abspath(__file__))

        # Carrega dados
        self.generos = self.carregar_generos()
        self.carregar_historico()
        self.carregar_favoritos()
        self.carregar_citacoes_diarias()

    def get_arquivo_path(self, nome_arquivo):
        """Retorna o caminho completo para um arquivo no diretório base"""
        return os.path.join(self.diretorio_base, nome_arquivo)

    def carregar_generos(self):
        # Lista de gêneros em inglês
        return [
            "Life",
            "Wisdom",
            "Success",
            "Love",
            "Happiness",
            "Motivation",
            "Leadership",
            "Knowledge",
            "Hope",
            "Faith"
        ]

    def obter_citacao_por_genero(self, genero):
        # Lista de APIs em inglês
        apis = [
            {
                'nome': 'Forismatic',
                'url': 'http://api.forismatic.com/api/1.0/',
                'metodo': 'post',
                'params': {
                    'method': 'getQuote',
                    'format': 'json',
                    'lang': 'en'
                },
                'parser': lambda data: {
                    'texto': data['quoteText'],
                    'autor': data['quoteAuthor'] or 'Unknown',
                    'genero': genero
                }
            },
            {
                'nome': 'ZenQuotes',
                'url': 'https://zenquotes.io/api/random',
                'metodo': 'get',
                'parser': lambda data: {
                    'texto': data[0]['q'],
                    'autor': data[0]['a'],
                    'genero': genero
                }
            },
            {
                'nome': 'QuoteGarden',
                'url': f'{self.quote_garden_api}/quotes/random',
                'metodo': 'get',
                'parser': lambda data: {
                    'texto': data['data'][0]['quoteText'],
                    'autor': data['data'][0]['quoteAuthor'],
                    'genero': genero
                }
            }
        ]

        # Tenta cada API em ordem aleatória
        random.shuffle(apis)
        for api in apis:
            try:
                print(f"Tentando API: {api['nome']}")

                if api['metodo'] == 'get':
                    response = requests.get(api['url'], timeout=10)
                else:
                    response = requests.post(
                        api['url'], data=api.get('params', {}), timeout=10)

                print(f"Status code: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    citacao = api['parser'](data)

                    # Verifica se a citação é válida
                    if citacao and citacao['texto'] and citacao['autor']:
                        print(f"Citação obtida com sucesso da API {
                              api['nome']}")
                        return citacao
                    else:
                        print(f"API {api['nome']} retornou dados inválidos")
                        continue
                else:
                    print(f"API {api['nome']} retornou status code {
                          response.status_code}")
                    continue

            except Exception as e:
                print(f"Erro ao tentar API {api['nome']}: {str(e)}")
                continue

        print("Todas as APIs falharam")
        return None

    def carregar_historico(self):
        """Carrega o histórico do arquivo JSON"""
        try:
            arquivo_historico = self.get_arquivo_path(
                'historico_citacoes.json')
            with open(arquivo_historico, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.historico = data.get('historico', [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.historico = []
            self.salvar_historico()

    def salvar_historico(self):
        """Salva o histórico no arquivo JSON"""
        try:
            arquivo_historico = self.get_arquivo_path(
                'historico_citacoes.json')
            with open(arquivo_historico, 'w', encoding='utf-8') as f:
                json.dump({'historico': self.historico},
                          f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar histórico: {str(e)}")

    def obter_citacao_api(self, tema):
        # Obtém citação da API correspondente ao tema
        try:
            response = requests.get(self.apis[tema])
            if response.status_code == 200:
                # Aqui você precisará adaptar o parsing dependendo da API
                citacao = self.parse_resposta_api(response.json(), tema)

                # Adiciona ao histórico
                if citacao not in self.citacoes[tema]:
                    self.citacoes[tema].append(citacao)
                    self.salvar_historico()

                return citacao
        except:
            return None

    def parse_resposta_api(self, dados, tema):
        # Adapte este método de acordo com o formato de resposta de cada API
        if tema == 'filosofia':
            return {
                'texto': dados.get('quoteText', ''),
                'autor': dados.get('quoteAuthor', 'Desconhecido')
            }
        elif tema == 'filmes':
            return {
                'texto': dados.get('quote', ''),
                'filme': dados.get('movie', 'Desconhecido')
            }
        # Adicione mais parsers conforme necessário
        return dados

    def obter_citacao_aleatoria(self, tema):
        # Primeiro tenta obter da API
        citacao = self.obter_citacao_api(tema)
        if citacao:
            return citacao

        # Se falhar, usa o histórico como fallback
        if tema in self.citacoes and self.citacoes[tema]:
            return random.choice(self.citacoes[tema])
        return None

    def atualizar_citacao_diaria(self):
        # Atualiza citação diária à meia-noite
        hoje = datetime.now().date()
        if self.ultima_atualizacao != hoje:
            self.citacao_do_dia = self.obter_citacao_aleatoria(self.tema_atual)
            self.ultima_atualizacao = hoje

    def buscar_citacao_especifica(self, filtros):
        # Busca citação com base nos filtros (autor, tema etc)
        resultados = []
        for citacao in self.citacoes[self.tema_atual]:
            match = True
            for chave, valor in filtros.items():
                if citacao.get(chave) != valor:
                    match = False
                    break
            if match:
                resultados.append(citacao)
        return resultados

    def carregar_citacoes_diarias(self):
        """Carrega as citações diárias do arquivo JSON"""
        try:
            arquivo_diarias = self.get_arquivo_path('citacoes_diarias.json')
            with open(arquivo_diarias, 'r') as f:
                data = json.load(f)
                hoje = datetime.now().strftime("%Y-%m-%d")
                if data.get('data') == hoje:
                    self.citacoes_diarias = data.get('citacoes', {})
                else:
                    self.citacoes_diarias = {}
                    self.salvar_citacoes_diarias()
        except FileNotFoundError:
            self.citacoes_diarias = {}
            self.salvar_citacoes_diarias()

    def salvar_citacoes_diarias(self):
        """Salva as citações diárias no arquivo JSON"""
        try:
            arquivo_diarias = self.get_arquivo_path('citacoes_diarias.json')
            with open(arquivo_diarias, 'w') as f:
                data = {
                    'data': datetime.now().strftime("%Y-%m-%d"),
                    'citacoes': self.citacoes_diarias
                }
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar citações diárias: {str(e)}")

    def obter_citacao_diaria(self, genero):
        # Se já existe uma citação diária para este gênero, retorna ela
        if genero in self.citacoes_diarias:
            return self.citacoes_diarias[genero]

        # Se não existe, obtém uma nova citação
        citacao = self.obter_citacao_por_genero(genero)
        if citacao:
            self.citacoes_diarias[genero] = citacao
            self.salvar_citacoes_diarias()
        return citacao

    def carregar_favoritos(self):
        """Carrega os favoritos do arquivo JSON"""
        try:
            arquivo_favoritos = self.get_arquivo_path(
                'favoritos_citacoes.json')
            with open(arquivo_favoritos, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.favoritos = data.get('favoritos', [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.favoritos = []
            self.salvar_favoritos()

    def salvar_favoritos(self):
        """Salva os favoritos no arquivo JSON"""
        try:
            arquivo_favoritos = self.get_arquivo_path(
                'favoritos_citacoes.json')
            with open(arquivo_favoritos, 'w', encoding='utf-8') as f:
                json.dump({'favoritos': self.favoritos},
                          f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar favoritos: {str(e)}")

    def adicionar_favorito(self, citacao):
        """Adiciona uma citação aos favoritos"""
        # Verifica se a citação já está nos favoritos
        for fav in self.favoritos:
            if fav['texto'] == citacao['texto'] and fav['autor'] == citacao['autor']:
                return False
        # Adiciona timestamp aos favoritos
        citacao_com_timestamp = citacao.copy()
        if 'timestamp' not in citacao_com_timestamp:
            citacao_com_timestamp['timestamp'] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")
        self.favoritos.append(citacao_com_timestamp)
        self.salvar_favoritos()
        return True

    def remover_favorito(self, citacao):
        """Remove uma citação dos favoritos"""
        for i, fav in enumerate(self.favoritos):
            if fav['texto'] == citacao['texto'] and fav['autor'] == citacao['autor']:
                self.favoritos.pop(i)
                self.salvar_favoritos()
                return True
        return False

    def is_favorito(self, citacao):
        """Verifica se uma citação está nos favoritos"""
        for fav in self.favoritos:
            if fav['texto'] == citacao['texto'] and fav['autor'] == citacao['autor']:
                return True
        return False

    def toggle_tema(self):
        self.tema_escuro = not getattr(self, 'tema_escuro', False)
        cores_escuras = {
            'bg_principal': '#2c3e50',
            'bg_citacao': '#34495e',
            'texto': '#ecf0f1',
            'destaque': '#3498db',
            'botao': '#2980b9'
        }
        cores_claras = {
            'bg_principal': '#f0f0f0',
            'bg_citacao': '#ffffff',
            'texto': '#2c3e50',
            'destaque': '#3498db',
            'botao': '#2980b9'
        }

        self.cores = cores_escuras if self.tema_escuro else cores_claras
        self.atualizar_cores()

# Interface gráfica


class InterfaceCitacoes:
    def __init__(self, gerenciador):
        self.gerenciador = gerenciador
        self.root = tk.Tk()
        self.root.title("Daily Quotes")
        self.root.geometry("600x400")

        # Inicializar variável para o combobox
        self.genero_var = tk.StringVar()

        # Carregar última categoria, citação e tema
        self.carregar_ultimo_estado()

        # Configuração de fontes
        self.citacao_font = ('Palatino', 14, 'italic')
        self.autor_font = ('Palatino', 12, 'bold')

        # Configura o fechamento normal da janela
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)

        # Configura o estilo inicial
        style = ttk.Style()
        style.theme_use('clam')

        # Carrega os gêneros antes de criar os widgets
        self.carregar_generos()
        self.criar_widgets()

        # Aplica o tema carregado
        self.definir_cores()

        # Centraliza a janela após criar todos os widgets
        self.root.eval('tk::PlaceWindow . center')

    def ao_fechar(self):
        """Salva o estado atual e fecha o programa"""
        self.salvar_ultimo_estado()
        self.root.destroy()

    def carregar_generos(self):
        # Lista de gêneros em inglês
        self.generos = [
            "Life",
            "Wisdom",
            "Success",
            "Love",
            "Happiness",
            "Motivation",
            "Leadership",
            "Knowledge",
            "Hope",
            "Faith"
        ]

    def criar_widgets(self):
        # Frame principal
        self.root.configure(bg='#f0f0f0')

        # Inicializar variável para o combobox
        self.genero_var = tk.StringVar()

        # Configurar estilo para elementos da interface
        style = ttk.Style()

        # Estilo para as abas
        style.configure('Custom.TNotebook.Tab',
                        font=('Segoe UI', 9))  # Fonte para as abas

        # Frame para organizar notebook e botão de histórico lado a lado
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Frame para as abas
        tabs_frame = ttk.Frame(main_container)
        tabs_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Notebook para abas
        self.notebook = ttk.Notebook(tabs_frame, style='Custom.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=(10, 0), pady=5)

        # Aba principal
        self.main_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.main_frame, text="Quotes")

        # Aba de favoritos
        self.favorites_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.favorites_frame, text="Favorites")

        # Frame para o botão de histórico
        history_frame = ttk.Frame(main_container)
        history_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        # Botão de histórico
        self.history_button = ttk.Button(history_frame,
                                         text="≡",  # Símbolo de menu
                                         width=2,
                                         command=self.show_history,
                                         style='Small.Icon.TButton')
        # Ajustado o padding superior
        self.history_button.pack(side=tk.TOP, pady=(7, 0))

        # Configurar estilo do botão de histórico
        style = ttk.Style()
        style.configure('Small.Icon.TButton',
                        font=('Segoe UI', 10),  # Fonte um pouco maior
                        padding=1)

        # Configurar abas
        self.configurar_aba_principal()
        self.configurar_aba_favoritos()

    def show_history(self):
        """Mostra o histórico em uma janela separada"""
        # Criar janela de histórico
        history_window = tk.Toplevel(self.root)
        history_window.title("History")
        history_window.geometry("800x400")

        # Centraliza a janela de histórico
        history_window.withdraw()
        history_window.update_idletasks()

        # Calcula posição
        x = (history_window.winfo_screenwidth() -
             history_window.winfo_width()) // 2
        y = (history_window.winfo_screenheight() -
             history_window.winfo_height()) // 2
        history_window.geometry(f"+{x}+{y}")
        history_window.deiconify()

        # Frame principal
        main_history_frame = ttk.Frame(history_window)
        main_history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Frame para o botão de remover
        button_frame = ttk.Frame(main_history_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))

        # Botão para remover do histórico
        ttk.Button(button_frame,
                   text="Remove Selected",
                   command=lambda: remover_historico_selecionado()).pack(side=tk.LEFT)

        # Lista de citações do histórico com scrollbar
        lista_historico = ttk.Treeview(main_history_frame,
                                       columns=("timestamp", "quote",
                                                "author", "category"),
                                       show="headings",
                                       selectmode="extended",  # Permite seleção múltipla
                                       style='Custom.Treeview')

        # Configurar estilo do Treeview
        style = ttk.Style()
        if self.tema_escuro:
            style.configure('Custom.Treeview',
                            background='#1b2838',
                            foreground='white',
                            fieldbackground='#1b2838',
                            font=('Segoe UI', 10))
            style.configure('Custom.Treeview.Heading',
                            background='#2a475e',
                            foreground='white',
                            font=('Segoe UI', 10, 'bold'))
        else:
            style.configure('Custom.Treeview',
                            background='white',
                            foreground='black',
                            fieldbackground='white',
                            font=('Segoe UI', 10))
            style.configure('Custom.Treeview.Heading',
                            background='#f0f0f0',
                            foreground='black',
                            font=('Segoe UI', 10, 'bold'))

        # Configurar colunas
        lista_historico.heading("timestamp", text="Date/Time")
        lista_historico.heading("quote", text="Quote")
        lista_historico.heading("author", text="Author")
        lista_historico.heading("category", text="Category")

        # Ajustar largura das colunas
        lista_historico.column("timestamp", width=150, minwidth=150)
        lista_historico.column("quote", width=400, minwidth=300)
        lista_historico.column("author", width=150, minwidth=150)
        lista_historico.column("category", width=100, minwidth=100)

        # Adicionar scrollbar
        scrollbar = ttk.Scrollbar(
            main_history_frame, orient=tk.VERTICAL, command=lista_historico.yview)
        lista_historico.configure(yscrollcommand=scrollbar.set)

        # Posicionar lista e scrollbar
        lista_historico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Função para remover itens selecionados do histórico
        def remover_historico_selecionado():
            selected_items = lista_historico.selection()
            if not selected_items:
                return

            for item_id in selected_items:
                item = lista_historico.item(item_id)
                valores = item['values']

                # Remove do histórico
                for citacao in self.gerenciador.historico[:]:
                    if (citacao['timestamp'] == valores[0] and
                        citacao['texto'] == valores[1] and
                            citacao['autor'] == valores[2]):
                        self.gerenciador.historico.remove(citacao)

                # Remove da visualização
                lista_historico.delete(item_id)

            # Salva o histórico atualizado
            self.gerenciador.salvar_historico()

        # Preencher o histórico
        for citacao in self.gerenciador.historico:
            lista_historico.insert("", tk.END, values=(
                citacao.get('timestamp', ''),
                citacao.get('texto', ''),
                citacao.get('autor', ''),
                citacao.get('genero', '')
            ))

        # Configurar seleção de linha
        def on_select(event):
            selected = lista_historico.selection()
            if selected:
                item = lista_historico.item(selected[0])
                # Você pode fazer algo com o item selecionado
                print(item['values'])

        lista_historico.bind('<<TreeviewSelect>>', on_select)

    def definir_cores(self):
        """Define as cores do tema atual"""
        if self.tema_escuro:
            # Cores para o tema escuro (Steam style)
            self.cores = {
                'bg': '#171a21',  # Fundo principal Steam
                'fg': '#ffffff',
                'text_bg': '#1b2838',  # Área de texto Steam
                'text_fg': '#ffffff',
                'button_bg': '#2a475e',  # Botões Steam
                'button_fg': '#ffffff',
                'treeview_bg': '#1b2838',
                'treeview_fg': '#ffffff',
                'treeview_selected_bg': '#66c0f4',  # Azul claro Steam
                'tab_selected': '#66c0f4',  # Azul claro Steam
                'tab_bg': '#2a475e',  # Azul escuro Steam
                'tab_fg': '#ffffff'
            }
        else:
            # Cores para o tema claro
            self.cores = {
                'bg': '#f3f3f3',
                'fg': '#000000',
                'text_bg': '#ffffff',
                'text_fg': '#000000',
                'button_bg': '#ffffff',
                'button_fg': '#000000',
                'treeview_bg': '#ffffff',
                'treeview_fg': '#000000',
                'treeview_selected_bg': '#66c0f4',  # Mantém o azul Steam
                'tab_selected': '#66c0f4',  # Mantém o azul Steam
                'tab_bg': '#f0f0f0',
                'tab_fg': '#000000'
            }

        self.aplicar_cores()

    def aplicar_cores(self):
        """Aplica as cores do tema atual aos widgets"""
        style = ttk.Style()

        # Configuração do tema principal
        self.root.configure(bg=self.cores['bg'])

        # Configuração dos frames
        style.configure('TFrame', background=self.cores['bg'])

        # Configuração dos botões
        style.configure('TButton',
                        background=self.cores['button_bg'],
                        foreground=self.cores['button_fg'])

        # Configuração do Notebook (abas)
        style.configure('TNotebook', background=self.cores['bg'])
        style.configure('TNotebook.Tab',
                        background=self.cores['tab_bg'],
                        foreground=self.cores['tab_fg'],
                        padding=[10, 2])

        # Configuração da aba selecionada
        style.map('TNotebook.Tab',
                  background=[('selected', self.cores['tab_selected'])],
                  foreground=[('selected', '#ffffff')])

        # Configuração das áreas de texto
        self.texto_citacao.configure(
            bg=self.cores['text_bg'],
            fg=self.cores['text_fg'],
            insertbackground=self.cores['text_fg']
        )

        # Configuração do Treeview
        style.configure('Treeview',
                        background=self.cores['treeview_bg'],
                        foreground=self.cores['treeview_fg'],
                        fieldbackground=self.cores['treeview_bg'])

        style.map('Treeview',
                  background=[
                      ('selected', self.cores['treeview_selected_bg'])],
                  foreground=[('selected', '#ffffff')])

    def toggle_theme(self):
        """Alterna entre tema claro e escuro"""
        self.tema_escuro = not self.tema_escuro
        self.definir_cores()

    def configurar_aba_principal(self):
        # Frame superior para o dropdown e botões
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, pady=5)

        # Label e Dropdown à esquerda
        label_frame = ttk.Frame(top_frame)
        label_frame.pack(side=tk.LEFT)

        # Label com fonte Segoe UI
        ttk.Label(label_frame,
                  text="Choose quote category:",
                  style='TLabel').pack(side=tk.LEFT, padx=(0, 5))

        # Combobox com fonte Segoe UI
        self.combo_generos = ttk.Combobox(label_frame,
                                          textvariable=self.genero_var,
                                          values=self.generos,
                                          width=15,
                                          font=('Segoe UI', 9),
                                          state="readonly")
        self.combo_generos.pack(side=tk.LEFT)

        # Frame para botões à direita
        right_buttons_frame = ttk.Frame(top_frame)
        right_buttons_frame.pack(side=tk.RIGHT)

        # Configurar estilo comum para os botões
        style = ttk.Style()
        style.configure('Small.Icon.TButton',
                        font=('Segoe UI', 10),
                        padding=1)

        # Botão de histórico à direita
        self.history_button = ttk.Button(right_buttons_frame,
                                         text="≡",
                                         width=3,
                                         command=self.show_history,
                                         style='Small.Icon.TButton')
        self.history_button.pack(side=tk.RIGHT, padx=5)

        # Botão de tema à direita (usando o mesmo estilo)
        self.theme_button = ttk.Button(right_buttons_frame,
                                       text="🌓",
                                       width=3,
                                       command=self.toggle_theme,
                                       style='Small.Icon.TButton')  # Usando o mesmo estilo
        self.theme_button.pack(side=tk.RIGHT)

        # Seleciona o primeiro gênero por padrão
        if self.generos:
            self.combo_generos.set(self.generos[0])

        # Botões
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.pack(pady=10)

        ttk.Button(buttons_frame,
                   text="Daily Quote",
                   command=self.mostrar_citacao_dia).pack(side=tk.LEFT, padx=5)

        ttk.Button(buttons_frame,
                   text="New Quote",
                   command=self.nova_citacao_aleatoria).pack(side=tk.LEFT, padx=5)

        # Botão de favorito
        self.favorite_button = ttk.Button(buttons_frame,
                                          text="Add to Favorites",
                                          command=self.adicionar_favorito_atual)
        self.favorite_button.pack(side=tk.LEFT, padx=5)

        # Área de exibição da citação (somente leitura)
        self.texto_citacao = tk.Text(self.main_frame,
                                     height=10,
                                     width=50,
                                     wrap=tk.WORD,
                                     font=self.citacao_font,
                                     state='disabled')
        self.texto_citacao.pack(pady=10, fill=tk.BOTH, expand=True)

        # Variável para armazenar a citação atual
        self.citacao_atual = None

        # Seleciona a última categoria usada
        self.combo_generos.set(self.ultima_categoria)

        # Se houver uma última citação, mostra ela
        if self.ultima_citacao:
            self.mostrar_citacao(self.ultima_citacao)

    def configurar_aba_favoritos(self):
        # Frame principal para organizar os elementos
        main_favorites_frame = ttk.Frame(self.favorites_frame)
        main_favorites_frame.pack(fill=tk.BOTH, expand=True)

        # Frame para o botão no topo
        buttons_frame = ttk.Frame(main_favorites_frame)
        buttons_frame.pack(pady=5, fill=tk.X)

        # Botão para remover dos favoritos
        ttk.Button(buttons_frame,
                   text="Remove Selected Favorites",
                   command=self.remover_favoritos_selecionados).pack(pady=5)

        # Lista de citações favoritas com seleção múltipla
        self.lista_favoritos = ttk.Treeview(main_favorites_frame,
                                            columns=("timestamp", "quote",
                                                     "author", "category"),
                                            show="headings",
                                            selectmode="extended")  # Permite seleção múltipla

        # Configurar colunas
        self.lista_favoritos.heading("timestamp", text="Date/Time")
        self.lista_favoritos.heading("quote", text="Quote")
        self.lista_favoritos.heading("author", text="Author")
        self.lista_favoritos.heading("category", text="Category")

        # Ajustar largura das colunas
        self.lista_favoritos.column("timestamp", width=130, minwidth=130)
        self.lista_favoritos.column("quote", width=300, minwidth=200)
        self.lista_favoritos.column("author", width=100, minwidth=100)
        self.lista_favoritos.column("category", width=70, minwidth=70)

        # Adicionar scrollbar
        scrollbar = ttk.Scrollbar(
            main_favorites_frame, orient=tk.VERTICAL, command=self.lista_favoritos.yview)
        self.lista_favoritos.configure(yscrollcommand=scrollbar.set)

        # Posicionar lista e scrollbar
        self.lista_favoritos.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # Carrega os favoritos iniciais
        self.atualizar_favoritos()

    def remover_favoritos_selecionados(self):
        """Remove todas as citações selecionadas dos favoritos"""
        # Obter todos os itens selecionados
        selected_items = self.lista_favoritos.selection()
        if not selected_items:
            return

        # Para cada item selecionado
        for item_id in selected_items:
            # Obter dados da citação selecionada
            item = self.lista_favoritos.item(item_id)
            valores = item['values']

            citacao = {
                'timestamp': valores[0],
                'texto': valores[1],
                'autor': valores[2],
                'genero': valores[3]
            }

            # Remover dos favoritos
            self.gerenciador.remover_favorito(citacao)

            # Se a citação atual é a mesma que foi removida, atualizar o botão
            if (self.citacao_atual and
                self.citacao_atual['texto'] == citacao['texto'] and
                    self.citacao_atual['autor'] == citacao['autor']):
                self.favorite_button.config(text="Add to Favorites")

        # Atualizar a visualização
        self.atualizar_favoritos()

    def atualizar_favoritos(self):
        # Limpar lista atual
        for item in self.lista_favoritos.get_children():
            self.lista_favoritos.delete(item)

        # Adicionar citações favoritas
        if self.gerenciador.favoritos:
            for citacao in self.gerenciador.favoritos:
                self.lista_favoritos.insert("", tk.END, values=(
                    citacao['timestamp'],
                    citacao['texto'],
                    citacao['autor'],
                    citacao['genero']
                ))

    def adicionar_favorito_atual(self):
        """Adiciona ou remove a citação atual dos favoritos"""
        if self.citacao_atual:
            if self.gerenciador.is_favorito(self.citacao_atual):
                self.gerenciador.remover_favorito(self.citacao_atual)
                self.favorite_button.config(text="Add to Favorites")
            else:
                self.gerenciador.adicionar_favorito(self.citacao_atual)
                self.favorite_button.config(text="Remove from Favorites")
            self.atualizar_favoritos()

    def mostrar_citacao(self, citacao):
        """Mostra a citação com formatação melhorada"""
        self.texto_citacao.config(state='normal')
        self.texto_citacao.delete(1.0, tk.END)
        if citacao:
            self.citacao_atual = citacao
            # Insere citação com fonte estilizada
            self.texto_citacao.tag_configure('citacao', font=self.citacao_font)
            self.texto_citacao.tag_configure('autor', font=self.autor_font)

            self.texto_citacao.insert(
                tk.END, f'"{citacao["texto"]}"\n\n', 'citacao')
            self.texto_citacao.insert(tk.END, f'- {citacao["autor"]}', 'autor')

            # Atualiza o texto do botão de favorito
            if self.gerenciador.is_favorito(citacao):
                self.favorite_button.config(text="Remove from Favorites")
            else:
                self.favorite_button.config(text="Add to Favorites")

            # Verifica se a citação já existe no histórico
            citacao_existe = False
            for hist_citacao in self.gerenciador.historico:
                if (hist_citacao['texto'] == citacao['texto'] and
                        hist_citacao['autor'] == citacao['autor']):
                    citacao_existe = True
                    break

            # Só adiciona ao histórico se for uma citação nova
            if not citacao_existe:
                citacao_com_timestamp = citacao.copy()
                citacao_com_timestamp['timestamp'] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S")
                self.gerenciador.historico.insert(0, citacao_com_timestamp)
                self.gerenciador.historico = self.gerenciador.historico[:50]
                self.gerenciador.salvar_historico()
        else:
            self.citacao_atual = None
            self.texto_citacao.insert(
                tk.END, "Could not get a quote. Please try again.")
        self.texto_citacao.config(state='disabled')

    def mostrar_citacao_dia(self):
        """Mostra a citação do dia para o gênero selecionado"""
        genero = self.genero_var.get()
        if not genero:
            # Temporariamente habilita para mostrar mensagem
            self.texto_citacao.config(state='normal')
            self.texto_citacao.delete(1.0, tk.END)
            self.texto_citacao.insert(tk.END, "Please select a category first")
            self.texto_citacao.config(state='disabled')
            return

        # Obtém a citação diária (seja nova ou existente)
        citacao = self.gerenciador.obter_citacao_diaria(genero)
        self.mostrar_citacao(citacao)

    def nova_citacao_aleatoria(self):
        """Obtém uma nova citação aleatória para o gênero selecionado"""
        genero = self.genero_var.get()
        if not genero:
            # Temporariamente habilita para mostrar mensagem
            self.texto_citacao.config(state='normal')
            self.texto_citacao.delete(1.0, tk.END)
            self.texto_citacao.insert(tk.END, "Please select a category first")
            self.texto_citacao.config(state='disabled')
            return

        citacao = self.gerenciador.obter_citacao_por_genero(genero)
        self.mostrar_citacao(citacao)

    def iniciar(self):
        # Inicia a interface
        self.root.mainloop()

    def centralizar_janela(self, janela):
        """Centraliza uma janela na tela"""
        # Pega as dimensões da tela
        largura_tela = janela.winfo_screenwidth()
        altura_tela = janela.winfo_screenheight()

        # Pega as dimensões da janela
        largura = janela.winfo_width()
        altura = janela.winfo_height()

        # Calcula a posição para centralizar
        pos_x = (largura_tela - largura) // 2
        pos_y = (altura_tela - altura) // 2

        # Atualiza a geometria da janela
        janela.geometry(f"+{pos_x}+{pos_y}")

        # Força a atualização da janela para garantir o posicionamento correto
        janela.update_idletasks()

        # Recalcula após a atualização
        largura = janela.winfo_width()
        altura = janela.winfo_height()
        pos_x = (largura_tela - largura) // 2
        pos_y = (altura_tela - altura) // 2
        janela.geometry(f"+{pos_x}+{pos_y}")

    def carregar_ultimo_estado(self):
        """Carrega a última categoria, citação e tema selecionados"""
        try:
            with open('ultimo_estado.json', 'r') as f:
                estado = json.load(f)
                self.ultima_categoria = estado.get('categoria', 'Life')
                self.ultima_citacao = estado.get('citacao', None)
                # Carrega o tema salvo (False = claro, True = escuro)
                self.tema_escuro = estado.get('tema_escuro', False)
        except FileNotFoundError:
            self.ultima_categoria = 'Life'
            self.ultima_citacao = None
            self.tema_escuro = False

    def salvar_ultimo_estado(self):
        """Salva a categoria, citação e tema atual"""
        estado = {
            'categoria': self.genero_var.get(),
            'citacao': self.citacao_atual,
            'tema_escuro': self.tema_escuro  # Salva o estado do tema
        }
        with open('ultimo_estado.json', 'w') as f:
            json.dump(estado, f)


# Ponto de entrada do programa
if __name__ == "__main__":
    gerenciador = GerenciadorCitacoes()
    interface = InterfaceCitacoes(gerenciador)

    # Agenda atualização diária
    schedule.every().day.at("00:00").do(gerenciador.atualizar_citacao_diaria)

    # Inicia interface
    interface.iniciar()
