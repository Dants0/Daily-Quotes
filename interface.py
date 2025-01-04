# Importando bibliotecas necessárias
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk  # Adiciona customtkinter
import json
import requests
from datetime import datetime
import random
import schedule
import time
import os

# Configura o tema padrão do customtkinter
ctk.set_appearance_mode("dark")  # Modos: "dark", "light"
ctk.set_default_color_theme("blue")  # Temas: "blue", "dark-blue", "green"


class InterfaceCitacoes:
    def __init__(self, gerenciador):
        self.gerenciador = gerenciador
        self.root = ctk.CTk()
        self.root.title("Daily Quotes")
        self.root.geometry("700x400")

        # Inicializa variáveis importantes
        self.genero_var = tk.StringVar()
        self.citacao_atual = None
        self.history_window = None
        self.is_portuguese = True
        self.tema_escuro = ctk.get_appearance_mode() == "dark"

        # Carrega configurações
        self.carregar_ultimo_estado()
        self.carregar_generos()
        self.criar_widgets()
        self.definir_cores()
        self.root.eval('tk::PlaceWindow . center')

        # Configura o handler para quando a janela for fechada
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)

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
        # Usar CTkFrame em vez de ttk.Frame
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Notebook customizado do CTk
        self.notebook = ctk.CTkTabview(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Adicionar abas usando CTkTabview com texto baseado no idioma
        self.main_frame = self.notebook.add("Quotes")
        self.favorites_frame = self.notebook.add(
            "Favoritos" if self.is_portuguese else "Favorites")

        self.configurar_aba_principal()
        self.configurar_aba_favoritos()

        # Configura os textos iniciais baseados no idioma carregado
        self.atualizar_textos_interface()

    def show_history(self):
        """Mostra o histórico em uma janela separada"""
        if self.history_window is not None:
            self.history_window.lift()
            return

        self.history_window = ctk.CTkToplevel(self.root)
        self.history_window.title(
            "Histórico" if self.is_portuguese else "History")
        self.history_window.geometry("800x400")

        # Criar estilo para o Treeview
        style = ttk.Style()
        if ctk.get_appearance_mode() == "Dark":
            # Configuração para modo escuro
            style.configure(
                "Treeview",
                background="#2b2b2b",
                foreground="white",
                fieldbackground="#2b2b2b",
                bordercolor="#2b2b2b",
                lightcolor="#2b2b2b",
                darkcolor="#2b2b2b",
                selectbackground="#1f538d",
                selectforeground="white"
            )
            style.configure(
                "Treeview.Heading",
                background="#2b2b2b",
                foreground="white",
                bordercolor="#2b2b2b",
                lightcolor="#2b2b2b",
                darkcolor="#2b2b2b"
            )
            # Configurar cores de seleção
            style.map(
                "Treeview",
                background=[("selected", "#1f538d")],
                foreground=[("selected", "white")]
            )
            # Configurar cores da scrollbar
            style.configure(
                "Vertical.TScrollbar",
                background="#2b2b2b",
                bordercolor="#2b2b2b",
                arrowcolor="white",
                troughcolor="#2b2b2b"
            )
        else:
            # Configuração para modo claro
            style.configure(
                "Treeview",
                background="white",
                foreground="black",
                fieldbackground="white"
            )
            style.configure(
                "Treeview.Heading",
                background="white",
                foreground="black"
            )
            style.map(
                "Treeview",
                background=[("selected", "#0078D7")],
                foreground=[("selected", "white")]
            )

        def on_history_close():
            self.history_window.destroy()
            self.history_window = None

        self.history_window.protocol("WM_DELETE_WINDOW", on_history_close)

        # Frame principal
        main_history_frame = ctk.CTkFrame(self.history_window)
        main_history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Frame para botões
        button_frame = ctk.CTkFrame(main_history_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))

        def remover_historico_selecionado():
            selected_items = lista_historico.selection()
            if not selected_items:
                return

            for item_id in selected_items:
                valores = lista_historico.item(item_id)['values']

                # Remove do histórico
                for citacao in self.gerenciador.historico[:]:
                    # Verifica tanto texto_en quanto texto_pt
                    if (citacao['timestamp'] == valores[0] and
                        (citacao.get('texto_en') == valores[1] or
                         citacao.get('texto_pt') == valores[1] or
                         citacao.get('texto') == valores[1]) and
                            citacao['autor'] == valores[2]):
                        self.gerenciador.historico.remove(citacao)

                # Remove da visualização
                lista_historico.delete(item_id)

            # Salva o histórico atualizado
            self.gerenciador.salvar_historico()

        # Botão de remover
        self.remove_history_button = ctk.CTkButton(
            button_frame,
            text="Remover Selecionados" if self.is_portuguese else "Remove Selected",
            command=remover_historico_selecionado
        ).pack(side=tk.LEFT, padx=5)

        # Frame para a lista
        list_frame = ctk.CTkFrame(main_history_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Lista de histórico com cabeçalhos traduzidos
        colunas = {
            "Time": "Data/Hora" if self.is_portuguese else "Time",
            "Quote": "Citação" if self.is_portuguese else "Quote",
            "Author": "Autor" if self.is_portuguese else "Author",
            "Category": "Categoria" if self.is_portuguese else "Category"
        }

        lista_historico = ttk.Treeview(
            list_frame,
            columns=tuple(colunas.keys()),
            show="headings"
        )

        # Configurar colunas com textos traduzidos
        for col_id, header_text in colunas.items():
            lista_historico.heading(col_id, text=header_text)

        # Configurar larguras das colunas
        lista_historico.column("Time", width=150)
        lista_historico.column("Quote", width=400)
        lista_historico.column("Author", width=150)
        lista_historico.column("Category", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=lista_historico.yview
        )
        lista_historico.configure(yscrollcommand=scrollbar.set)

        # Posicionar lista e scrollbar
        lista_historico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Preencher o histórico
        for citacao in self.gerenciador.historico:
            # Usa a versão apropriada do texto baseado no idioma
            if 'texto_en' in citacao and 'texto_pt' in citacao:
                texto_citacao = citacao['texto_pt'] if self.is_portuguese else citacao['texto_en']
            else:
                # Fallback para citações antigas
                texto_citacao = citacao['texto']
                if self.is_portuguese and not any(c in texto_citacao for c in 'áéíóúâêîôûãõàèìòùç'):
                    texto_citacao = self.translate_quotes(texto_citacao)

            lista_historico.insert("", tk.END, values=(
                citacao.get('timestamp', ''),
                texto_citacao,
                citacao.get('autor', ''),
                citacao.get('genero', '')
            ))

        # Centralizar a janela
        self.centralizar_janela(self.history_window)

        # Aplicar estilo do Treeview
        self.aplicar_estilo_treeview()

    def definir_cores(self):
        """Define as cores baseadas no tema atual"""
        if self.tema_escuro:
            self.cores = {
                'bg_principal': '#2c3e50',
                'bg_citacao': '#34495e',
                'texto': '#ecf0f1',
                'destaque': '#3498db',
                'botao': '#2980b9'
            }
        else:
            self.cores = {
                'bg_principal': '#f0f0f0',
                'bg_citacao': '#ffffff',
                'texto': '#2c3e50',
                'destaque': '#3498db',
                'botao': '#2980b9'
            }

        self.aplicar_cores()

    def aplicar_cores(self):
        """Aplica as cores aos elementos da interface"""
        # No customtkinter, as cores são gerenciadas automaticamente
        # baseadas no appearance_mode
        pass

    def toggle_theme(self):
        """Alterna entre tema claro e escuro"""
        # Inverte o tema atual
        novo_tema = "light" if self.tema_escuro else "dark"
        ctk.set_appearance_mode(novo_tema)
        self.tema_escuro = not self.tema_escuro

        # Atualiza o ícone do botão (sol para tema escuro, lua para tema claro)
        self.theme_button.configure(text="☀️" if self.tema_escuro else "🌙")

        # Atualiza as cores e estilos
        self.definir_cores()
        self.aplicar_estilo_treeview()

        # Se a janela de histórico estiver aberta, atualiza seu estilo
        if self.history_window is not None:
            self.history_window.destroy()
            self.history_window = None
            self.show_history()

        # Força atualização da interface
        self.root.update()

    def toggle_language(self):
        """Alterna entre inglês e português"""
        self.is_portuguese = not self.is_portuguese

        # Atualiza o texto do botão para mostrar o idioma para o qual vai mudar
        self.language_button.configure(
            text="English" if self.is_portuguese else "Português"
        )

        # Atualiza o título da janela
        self.root.title(
            "Citações Diárias" if self.is_portuguese else "Daily Quotes")

        # Atualiza os textos dos botões
        self.daily_quote_button.configure(
            text="Citação Diária" if self.is_portuguese else "Daily Quote"
        )
        self.new_quote_button.configure(
            text="Nova Citação" if self.is_portuguese else "New Quote"
        )

        # Atualiza o botão de favoritos
        if self.citacao_atual:
            is_favorito = self.gerenciador.is_favorito(self.citacao_atual)
            if self.is_portuguese:
                texto_botao = "Remover dos Favoritos" if is_favorito else "Adicionar aos Favoritos"
            else:
                texto_botao = "Remove from Favorites" if is_favorito else "Add to Favorites"
            self.favorite_button.configure(text=texto_botao)
        else:
            # Se não houver citação atual, mostra o texto padrão
            self.favorite_button.configure(
                text="Adicionar aos Favoritos" if self.is_portuguese else "Add to Favorites"
            )

        # Atualiza a citação atual se existir
        if self.citacao_atual:
            self.mostrar_citacao(self.citacao_atual)

        # Atualiza a lista de favoritos
        self.atualizar_favoritos()

        # Atualiza o texto do botão de histórico
        self.history_button.configure(
            text="Histórico" if self.is_portuguese else "History"
        )

        # Atualiza a janela de histórico se estiver aberta
        if self.history_window is not None:
            self.history_window.destroy()
            self.history_window = None
            self.show_history()  # Reabre a janela com o novo idioma

        # Atualiza os cabeçalhos da lista de favoritos
        colunas = {
            "Time": "Data/Hora" if self.is_portuguese else "Time",
            "Quote": "Citação" if self.is_portuguese else "Quote",
            "Author": "Autor" if self.is_portuguese else "Author",
            "Category": "Categoria" if self.is_portuguese else "Category"
        }

        for col_id, header_text in colunas.items():
            self.lista_favoritos.heading(col_id, text=header_text)

        # Atualiza a lista de favoritos para mostrar os textos no idioma correto
        self.atualizar_favoritos()

    def on_category_change(self, choice):
        """Chamado quando uma nova categoria é selecionada"""
        self.genero_var.set(choice)
        self.mostrar_citacao_dia()

    def configurar_aba_principal(self):
        """Configura a aba principal com os widgets modernos"""
        # Frame superior com a mesma cor de fundo
        top_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"  # Isso fará o frame usar a cor de fundo do pai
        )
        top_frame.pack(fill=tk.X, pady=5)

        # Frame para categoria também transparente
        category_frame = ctk.CTkFrame(
            top_frame,
            fg_color="transparent"  # Isso fará o frame usar a cor de fundo do pai
        )
        category_frame.pack(side=tk.LEFT, padx=10)

        ctk.CTkLabel(
            category_frame,
            text="Choose quote category:",
            font=("Segoe UI", 12)
        ).pack(side=tk.LEFT, padx=5)

        self.combo_generos = ctk.CTkOptionMenu(
            category_frame,
            values=self.generos,
            command=self.on_category_change,
            width=150,
            font=("Segoe UI", 12)
        )
        self.combo_generos.pack(side=tk.LEFT, padx=5)
        self.combo_generos.set(self.ultima_categoria)
        self.genero_var.set(self.ultima_categoria)

        # Frame para botões à direita
        buttons_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        buttons_frame.pack(side=tk.RIGHT, padx=10)

        # Botão de histórico
        self.history_button = ctk.CTkButton(
            buttons_frame,
            text="Histórico" if self.is_portuguese else "History",
            command=self.show_history
        )
        self.history_button.pack(side=tk.LEFT, padx=5)

        # Botão de tema
        self.theme_button = ctk.CTkButton(
            buttons_frame,
            text="☀️" if self.tema_escuro else "🌙",
            width=40,
            command=self.toggle_theme
        )
        self.theme_button.pack(side=tk.RIGHT, padx=2)

        # Botão de idioma - mostra o idioma para o qual vai mudar
        self.language_button = ctk.CTkButton(
            buttons_frame,
            # Se está em português, mostra "English", se está em inglês, mostra "Português"
            text="English" if self.is_portuguese else "Português",
            width=80,
            command=self.toggle_language
        )
        self.language_button.pack(side=tk.RIGHT, padx=2)

        # Frame para botões de ação
        action_frame = ctk.CTkFrame(self.main_frame)
        action_frame.pack(pady=10)

        # Botões de ação
        self.daily_quote_button = ctk.CTkButton(
            action_frame,
            text="Daily Quote",
            command=self.mostrar_citacao_dia
        )
        self.daily_quote_button.pack(side=tk.LEFT, padx=5)

        self.new_quote_button = ctk.CTkButton(
            action_frame,
            text="New Quote",
            command=self.nova_citacao_aleatoria
        )
        self.new_quote_button.pack(side=tk.LEFT, padx=5)

        self.favorite_button = ctk.CTkButton(
            action_frame,
            text="Add to Favorites",
            command=self.adicionar_favorito_atual
        )
        self.favorite_button.pack(side=tk.LEFT, padx=5)

        # Área de texto
        self.texto_citacao = ctk.CTkTextbox(
            self.main_frame,
            height=200,
            font=("Palatino", 14),
            wrap="word"
        )
        self.texto_citacao.pack(pady=10, fill=tk.BOTH, expand=True)

    def configurar_aba_favoritos(self):
        """Configura a aba de favoritos"""
        # Frame principal
        favorites_main_frame = ctk.CTkFrame(self.favorites_frame)
        favorites_main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Frame para a lista
        list_frame = ctk.CTkFrame(favorites_main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Cabeçalhos traduzidos
        colunas = {
            "Time": "Data/Hora" if self.is_portuguese else "Time",
            "Quote": "Citação" if self.is_portuguese else "Quote",
            "Author": "Autor" if self.is_portuguese else "Author",
            "Category": "Categoria" if self.is_portuguese else "Category"
        }

        # Lista de favoritos
        self.lista_favoritos = ttk.Treeview(
            list_frame,
            columns=tuple(colunas.keys()),
            show="headings"
        )

        # Configurar colunas com textos traduzidos
        for col_id, header_text in colunas.items():
            self.lista_favoritos.heading(col_id, text=header_text)

        # Configurar larguras das colunas
        self.lista_favoritos.column("Time", width=150)
        self.lista_favoritos.column("Quote", width=400)
        self.lista_favoritos.column("Author", width=150)
        self.lista_favoritos.column("Category", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.lista_favoritos.yview
        )
        self.lista_favoritos.configure(yscrollcommand=scrollbar.set)

        # Posicionar lista e scrollbar
        self.lista_favoritos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Aplicar estilo do Treeview
        self.aplicar_estilo_treeview()

        # Preencher a lista de favoritos
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

            # Remove dos favoritos
            for fav in self.gerenciador.favoritos[:]:
                # Verifica tanto texto_en quanto texto_pt
                if (fav['timestamp'] == valores[0] and
                    (fav.get('texto_en') == valores[1] or
                     fav.get('texto_pt') == valores[1] or
                     fav.get('texto') == valores[1]) and
                        fav['autor'] == valores[2]):
                    self.gerenciador.favoritos.remove(fav)

                    # Se a citação atual é a mesma que foi removida, atualizar o botão
                    if self.citacao_atual and (
                            self.citacao_atual.get('texto_en') == fav.get('texto_en') or
                            self.citacao_atual.get('texto_pt') == fav.get('texto_pt')):
                        self.favorite_button.configure(text="Add to Favorites")

        # Salva e atualiza a visualização
        self.gerenciador.salvar_favoritos()
        self.atualizar_favoritos()

    def atualizar_favoritos(self):
        # Limpar lista atual
        for item in self.lista_favoritos.get_children():
            self.lista_favoritos.delete(item)

        # Adicionar citações favoritas
        if self.gerenciador.favoritos:
            for citacao in self.gerenciador.favoritos:
                # Usa a versão apropriada do texto baseado no idioma
                if 'texto_en' in citacao and 'texto_pt' in citacao:
                    texto_citacao = citacao['texto_pt'] if self.is_portuguese else citacao['texto_en']
                else:
                    # Fallback para citações antigas
                    texto_citacao = citacao['texto']
                    if self.is_portuguese and not any(c in texto_citacao for c in 'áéíóúâêîôûãõàèìòùç'):
                        texto_citacao = self.translate_quotes(texto_citacao)

                self.lista_favoritos.insert("", tk.END, values=(
                    citacao['timestamp'],
                    texto_citacao,
                    citacao['autor'],
                    citacao['genero']
                ))

    def adicionar_favorito_atual(self):
        """Adiciona ou remove a citação atual dos favoritos"""
        if self.citacao_atual:
            if self.gerenciador.is_favorito(self.citacao_atual):
                self.gerenciador.remover_favorito(self.citacao_atual)
                self.favorite_button.configure(text="Add to Favorites")
            else:
                # Cria uma cópia da citação atual com ambos os idiomas
                citacao_para_salvar = self.citacao_atual.copy()
                # Versão em inglês
                citacao_para_salvar['texto_en'] = citacao_para_salvar['texto']
                citacao_para_salvar['texto_pt'] = self.translate_quotes(
                    citacao_para_salvar['texto'])  # Versão em português

                # Adiciona aos favoritos
                self.gerenciador.adicionar_favorito(citacao_para_salvar)
                self.favorite_button.configure(text="Remove from Favorites")

            self.atualizar_favoritos()

    def translate_quotes(self, original_text):
        url = "https://text-translator2.p.rapidapi.com/translate"

        payload = {
            "source_language": "en",
            "target_language": "pt",
            "text": f'{original_text}'
        }
        headers = {
            "x-rapidapi-key": "3b98b3197fmsh04ee2115419aaabp1e44d8jsnefa6a1c0f6de",
            "x-rapidapi-host": "text-translator2.p.rapidapi.com",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(url, data=payload, headers=headers)
        responseData = response.json()
        translatedText = responseData.get('data', {}).get('translatedText')

        return translatedText

    def mostrar_citacao(self, citacao):
        """Mostra a citação com formatação melhorada"""
        self.texto_citacao.configure(state="normal")
        self.texto_citacao.delete("1.0", tk.END)

        if citacao:
            if 'texto_en' in citacao and 'texto_pt' in citacao:
                texto_citacao = citacao['texto_pt'] if self.is_portuguese else citacao['texto_en']
            else:
                texto_citacao = self.translate_quotes(
                    citacao["texto"]) if self.is_portuguese else citacao["texto"]
                citacao['texto_en'] = citacao["texto"]
                citacao['texto_pt'] = self.translate_quotes(citacao["texto"])

            self.citacao_atual = citacao
            self.texto_citacao.insert(
                "1.0", f'"{texto_citacao}"\n\n- {citacao["autor"]}')

            # Adiciona a citação ao histórico
            self.gerenciador.adicionar_ao_historico(citacao)

            # Atualiza o texto do botão de favoritos baseado no idioma
            is_favorito = self.gerenciador.is_favorito(citacao)
            if self.is_portuguese:
                texto_botao = "Remover dos Favoritos" if is_favorito else "Adicionar aos Favoritos"
            else:
                texto_botao = "Remove from Favorites" if is_favorito else "Add to Favorites"
            self.favorite_button.configure(text=texto_botao)
        else:
            self.citacao_atual = None
            self.texto_citacao.insert(
                "1.0", "Não foi possível obter uma citação. Tente novamente." if self.is_portuguese
                else "Could not get a quote. Please try again.")

        self.texto_citacao.configure(state="disabled")

    def mostrar_citacao_dia(self):
        """Mostra a citação do dia para o gênero selecionado"""
        genero = self.genero_var.get()
        if not genero or genero.strip() == "":  # Melhora a verificação
            self.texto_citacao.configure(state='normal')
            self.texto_citacao.delete("1.0", tk.END)
            self.texto_citacao.insert("1.0", "Please select a category first")
            self.texto_citacao.configure(state='disabled')
            return

        # Obtém a citação diária (seja nova ou existente)
        citacao = self.gerenciador.obter_citacao_diaria(genero)
        self.mostrar_citacao(citacao)

    def nova_citacao_aleatoria(self):
        """Obtém uma nova citação aleatória para o gênero selecionado"""
        genero = self.genero_var.get()
        if not genero:
            self.texto_citacao.configure(state='normal')
            self.texto_citacao.delete(1.0, tk.END)
            self.texto_citacao.insert(tk.END, "Please select a category first")
            self.texto_citacao.configure(state='disabled')
            return

        # Desabilita o botão imediatamente
        self.new_quote_button.configure(state="disabled", text="Loading...")
        self.root.update()  # Força atualização da interface

        # Atualiza a interface para mostrar que está carregando
        self.texto_citacao.configure(state='normal')
        self.texto_citacao.delete(1.0, tk.END)
        self.texto_citacao.insert(tk.END, "Loading new quote...")
        self.texto_citacao.configure(state='disabled')

        try:
            # Obtém a nova citação
            citacao = self.gerenciador.obter_citacao_por_genero(genero)

            # Adiciona um pequeno delay para evitar cliques acidentais
            self.root.after(1000, lambda: self.finalizar_nova_citacao(citacao))
        except Exception as e:
            # Em caso de erro, mostra a mensagem e reabilita o botão
            self.texto_citacao.configure(state='normal')
            self.texto_citacao.delete(1.0, tk.END)
            self.texto_citacao.insert(tk.END, f"Error: {str(e)}")
            self.texto_citacao.configure(state='disabled')
            self.new_quote_button.configure(state="normal", text="New Quote")

    def finalizar_nova_citacao(self, citacao):
        """Finaliza o processo de obtenção de nova citação"""
        self.mostrar_citacao(citacao)
        self.new_quote_button.configure(state="normal", text="New Quote")

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
        """Carrega a última categoria, citação, tema e idioma selecionados"""
        try:
            with open('ultimo_estado.json', 'r', encoding='utf-8') as f:
                estado = json.load(f)
                self.ultima_categoria = estado.get('categoria', 'Life')
                self.ultima_citacao = estado.get('citacao', None)
                self.is_portuguese = estado.get('is_portuguese', True)
                self.tema_escuro = estado.get('tema_escuro', True)

                # Aplica o tema
                ctk.set_appearance_mode(
                    "dark" if self.tema_escuro else "light")

        except (FileNotFoundError, json.JSONDecodeError):
            self.ultima_categoria = 'Life'
            self.ultima_citacao = None
            self.is_portuguese = True
            self.tema_escuro = True
            ctk.set_appearance_mode("dark")

    def salvar_ultimo_estado(self):
        """Salva o estado atual da interface"""
        estado = {
            'categoria': self.genero_var.get(),
            'citacao': self.citacao_atual,
            'is_portuguese': self.is_portuguese,
            'tema_escuro': self.tema_escuro  # Salva o estado do tema usando nossa variável
        }

        try:
            with open('ultimo_estado.json', 'w', encoding='utf-8') as f:
                json.dump(estado, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar estado: {str(e)}")

    def aplicar_estilo_treeview(self):
        """Aplica o estilo do Treeview baseado no tema atual"""
        style = ttk.Style()

        if ctk.get_appearance_mode() == "Dark":
            # Configuração para modo escuro
            # Usa o tema 'clam' que permite mais personalização
            style.theme_use('clam')

            # Cores para o modo escuro
            dark_colors = {
                'background': '#2b2b2b',
                'foreground': 'white',
                'selected_bg': '#1f538d',
                'selected_fg': 'white',
                'inactive_bg': '#404040',
                'border': '#2b2b2b'
            }

            # Configuração principal do Treeview
            style.configure(
                "Treeview",
                background=dark_colors['background'],
                foreground=dark_colors['foreground'],
                fieldbackground=dark_colors['background'],
                borderwidth=0,
                lightcolor=dark_colors['border'],
                darkcolor=dark_colors['border']
            )

            # Configuração dos cabeçalhos
            style.configure(
                "Treeview.Heading",
                background=dark_colors['inactive_bg'],
                foreground=dark_colors['foreground'],
                borderwidth=1,
                relief="flat"
            )

            # Configuração da seleção
            style.map(
                "Treeview",
                background=[
                    ("selected", dark_colors['selected_bg']),
                    ("!selected", dark_colors['background'])
                ],
                foreground=[
                    ("selected", dark_colors['selected_fg']),
                    ("!selected", dark_colors['foreground'])
                ]
            )

            # Configuração da scrollbar
            style.configure(
                "Vertical.TScrollbar",
                background=dark_colors['background'],
                bordercolor=dark_colors['border'],
                arrowcolor=dark_colors['foreground'],
                troughcolor=dark_colors['background']
            )

            # Configuração do mapa da scrollbar
            style.map(
                "Vertical.TScrollbar",
                background=[("pressed", dark_colors['inactive_bg']),
                            ("active", dark_colors['inactive_bg'])],
                arrowcolor=[("pressed", dark_colors['foreground']),
                            ("active", dark_colors['foreground'])]
            )

        else:
            # Configuração para modo claro
            style.theme_use('default')
            style.configure(
                "Treeview",
                background="white",
                foreground="black",
                fieldbackground="white"
            )
            style.configure(
                "Treeview.Heading",
                background="white",
                foreground="black"
            )
            style.map(
                "Treeview",
                background=[("selected", "#0078D7")],
                foreground=[("selected", "white")]
            )

    def atualizar_textos_interface(self):
        """Atualiza todos os textos da interface baseado no idioma atual"""
        # Título da janela
        self.root.title(
            "Citações Diárias" if self.is_portuguese else "Daily Quotes")

        # Botões principais
        if hasattr(self, 'daily_quote_button'):
            self.daily_quote_button.configure(
                text="Citação Diária" if self.is_portuguese else "Daily Quote"
            )
        if hasattr(self, 'new_quote_button'):
            self.new_quote_button.configure(
                text="Nova Citação" if self.is_portuguese else "New Quote"
            )
        if hasattr(self, 'history_button'):
            self.history_button.configure(
                text="Histórico" if self.is_portuguese else "History"
            )
        if hasattr(self, 'favorite_button'):
            if self.citacao_atual:
                is_favorito = self.gerenciador.is_favorito(self.citacao_atual)
                texto_botao = "Remover dos Favoritos" if is_favorito else "Adicionar aos Favoritos" \
                    if self.is_portuguese else \
                    "Remove from Favorites" if is_favorito else "Add to Favorites"
            else:
                texto_botao = "Adicionar aos Favoritos" if self.is_portuguese else "Add to Favorites"
            self.favorite_button.configure(text=texto_botao)
