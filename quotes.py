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
from interface import *

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




# Ponto de entrada do programa
if __name__ == "__main__":
    gerenciador = GerenciadorCitacoes()
    interface = InterfaceCitacoes(gerenciador)

    # Agenda atualização diária
    schedule.every().day.at("00:00").do(gerenciador.atualizar_citacao_diaria)

    # Inicia interface
    interface.iniciar()
