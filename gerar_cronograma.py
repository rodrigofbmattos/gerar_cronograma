"""
Script: Cronograma de Estudos Intercalado com Revisões Semanais e Mensais
Observação: Versão com intefaçe gráfica
Versão: 4.0.0
Data: 2025-09-26
Autor: Rodrigo Francisquini
Descrição: Script para gerar cronograma intercalado de matérias, com revisões semanais e mensais, lendo múltiplos CSVs.
Última modificação: 2025-09-26 - Ajuste para colocação de uma barra de rolagem e de um botão de remover CSV.
"""
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

# --- Funções de conversão de duração ---

def duracao_str_para_segundos(duracao_str):
    """
    Converte uma string de duração no formato mm:ss ou hh:mm:ss para segundos inteiros.
    """
    partes = duracao_str.split(':')
    if len(partes) == 2:  # mm:ss
        minutos, segundos = int(partes[0]), int(partes[1])
        return minutos*60 + segundos
    elif len(partes) == 3:  # hh:mm:ss
        horas, minutos, segundos = int(partes[0]), int(partes[1]), int(partes[2])
        return horas*3600 + minutos*60 + segundos
    return 0

def segundos_para_str_hhmmss(segundos):
    """
    Converte um valor inteiro de segundos para string no formato hh:mm:ss.
    """
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segundos_restantes = segundos % 60
    return f"{horas:02d}:{minutos:02d}:{segundos_restantes:02d}"

# --- Classe com Interface Gráfica ---

class CronogramaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Cronograma com Revisões")
        self.root.geometry("600x480")

        self.dataframes_materias = {}
        self.lista_nomes_materias = []

        self.botao_selecionar = tk.Button(root, text="Selecionar arquivos CSV", command=self.selecionar_csvs)
        self.botao_selecionar.pack(pady=10)

        # Frame para Listbox + Scrollbar
        frame_lista = tk.Frame(root)
        frame_lista.pack()

        self.listbox = tk.Listbox(frame_lista, width=60, height=12, selectmode=tk.EXTENDED)  # permite múltiplas seleções
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH)

        self.scrollbar = tk.Scrollbar(frame_lista, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Conecta scrollbar à listbox
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)

        self.frame_botoes = tk.Frame(root)
        self.frame_botoes.pack(pady=5)

        self.btn_subir = tk.Button(self.frame_botoes, text="↑ Subir", command=self.mover_para_cima)
        self.btn_subir.grid(row=0, column=0, padx=5)

        self.btn_descer = tk.Button(self.frame_botoes, text="↓ Descer", command=self.mover_para_baixo)
        self.btn_descer.grid(row=0, column=1, padx=5)

        self.btn_remover = tk.Button(self.frame_botoes, text="Remover arquivo selecionado", command=self.remover_selecionados)
        self.btn_remover.grid(row=0, column=2, padx=5)

        self.botao_gerar = tk.Button(root, text="Gerar Cronograma", command=self.gerar_cronograma)
        self.botao_gerar.pack(pady=10)

    def selecionar_csvs(self):
        arquivos_selecionados = filedialog.askopenfilenames(
            title="Selecione os CSVs das matérias",
            filetypes=[("CSV files", "*.csv")]
        )

        if not arquivos_selecionados:
            messagebox.showerror("Erro", "❌ Nenhum arquivo selecionado.")
            return

        for caminho_arquivo in arquivos_selecionados:
            nome_materia = caminho_arquivo.split('/')[-1].replace('.csv', '')
            if nome_materia in self.lista_nomes_materias:
                continue  # evita duplicar nomes na lista e dicionário

            dataframe_materia = pd.read_csv(caminho_arquivo, sep=';')
            dataframe_materia['Matéria'] = nome_materia  # Adiciona coluna para identificar a matéria
            self.dataframes_materias[nome_materia] = dataframe_materia
            self.lista_nomes_materias.append(nome_materia)
            self.listbox.insert(tk.END, nome_materia)

    def mover_para_cima(self):
        selecionado = self.listbox.curselection()
        if not selecionado or selecionado[0] == 0:
            return
        idx = selecionado[0]
        nome = self.lista_nomes_materias.pop(idx)
        self.lista_nomes_materias.insert(idx-1, nome)
        self.atualizar_listbox()
        self.listbox.select_set(idx-1)

    def mover_para_baixo(self):
        selecionado = self.listbox.curselection()
        if not selecionado or selecionado[0] == len(self.lista_nomes_materias) - 1:
            return
        idx = selecionado[0]
        nome = self.lista_nomes_materias.pop(idx)
        self.lista_nomes_materias.insert(idx+1, nome)
        self.atualizar_listbox()
        self.listbox.select_set(idx+1)

    def remover_selecionados(self):
        selecionados = list(self.listbox.curselection())
        if not selecionados:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado para remover.")
            return

        # Remove do fim para o começo para não desalinhar índices
        for idx in reversed(selecionados):
            nome = self.lista_nomes_materias.pop(idx)
            self.dataframes_materias.pop(nome, None)  # remove do dicionário se existir

        self.atualizar_listbox()

    def atualizar_listbox(self):
        self.listbox.delete(0, tk.END)
        for nome in self.lista_nomes_materias:
            self.listbox.insert(tk.END, nome)

    def gerar_cronograma(self):
        if not self.lista_nomes_materias:
            messagebox.showerror("Erro", "Nenhuma matéria carregada.")
            return

        # --- Inicializações para o processamento dos blocos de aula ---

        posicao_atual_por_materia = {materia: 0 for materia in self.lista_nomes_materias}  # índice da próxima aula
        materia_terminada = {materia: False for materia in self.lista_nomes_materias}   # flag se terminou matéria
        contador_blocos_semanais = {materia: 0 for materia in self.lista_nomes_materias}  # contagem de blocos semanais feitos
        dias_ultimos_blocos_semanais = {materia: [] for materia in self.lista_nomes_materias}   # dias para revisão semanal
        dias_acumulados_para_revisao_mensal = {materia: [] for materia in self.lista_nomes_materias}  # dias acumulados para revisão mensal
        contador_revisoes_semanais_para_revisao_mensal = {materia: 0 for materia in self.lista_nomes_materias}  # controle para disparar revisão mensal

        limite_tempo_bloco_segundos = 1*3600 + 45*60  # limite de 1h45min por bloco (em segundos)

        lista_final_blocos = []  # armazenará o cronograma final com os blocos e revisões

        # --- Funções para inserir blocos de revisões ---

        def inserir_revisao_semanal(materia):
            """
            Insere um bloco de revisão semanal para a matéria especificada,
            utilizando os dias acumulados dos últimos blocos semanais.
            """
            dias_para_revisar = ', '.join(map(str, dias_ultimos_blocos_semanais[materia]))
            lista_final_blocos.append({
                'Matéria': f"Revisão Semanal - {materia}",
                'Aula': '',
                'Subtítulo': '',
                'Vídeo': '',
                'Videoaula': f"Revisar dias: {dias_para_revisar}",
                'Duração': ''
            })
            dias_acumulados_para_revisao_mensal[materia].extend(dias_ultimos_blocos_semanais[materia])
            contador_blocos_semanais[materia] = 0  # reseta contador semanal
            dias_ultimos_blocos_semanais[materia] = []  # limpa dias semanais
            contador_revisoes_semanais_para_revisao_mensal[materia] += 1  # incrementa revisão semanal feita para disparar mensal

        def inserir_revisao_mensal(lista_materias):
            """
            Insere blocos de revisão mensal para todas as matérias listadas,
            com base nos dias acumulados para revisão mensal.
            """
            for materia in lista_materias:
                dias_para_revisar = ', '.join(map(str, dias_acumulados_para_revisao_mensal[materia]))
                if dias_para_revisar:  # só insere se houver dias acumulados
                    lista_final_blocos.append({
                        'Matéria': f"Revisão Mensal - {materia}",
                        'Aula': '',
                        'Subtítulo': '',
                        'Vídeo': '',
                        'Videoaula': f"Revisar dias: {dias_para_revisar}",
                        'Duração': ''
                    })
                dias_acumulados_para_revisao_mensal[materia] = []  # limpa os dias acumulados
                contador_revisoes_semanais_para_revisao_mensal[materia] = 0  # reseta contador de revisões semanais para mensal

        # --- Loop principal que cria os blocos intercalados e insere revisões ---

        while not all(materia_terminada.values()):
            for materia in self.lista_nomes_materias:
                if materia_terminada[materia]:
                    continue  # pula se já terminou essa matéria

                dataframe_materia = self.dataframes_materias[materia]
                posicao_atual = posicao_atual_por_materia[materia]

                bloco_atual = {'Matéria': [], 'Aula': [], 'Subtítulo': [], 'Vídeo': [], 'Videoaula': [], 'Duração': []}
                tempo_total_bloco = 0

                while posicao_atual < len(dataframe_materia):
                    linha = dataframe_materia.iloc[posicao_atual]
                    duracao_segundos = duracao_str_para_segundos(linha['Duração'])

                    if tempo_total_bloco + duracao_segundos > limite_tempo_bloco_segundos and bloco_atual['Aula']:
                        break

                    for coluna in ['Matéria', 'Aula', 'Subtítulo', 'Vídeo', 'Duração']:
                        bloco_atual[coluna].append(linha[coluna])
                    bloco_atual['Videoaula'].append(f"{linha['Videoaula']} ({linha['Duração']})")
                    tempo_total_bloco += duracao_segundos
                    posicao_atual += 1

                if bloco_atual['Aula']:
                    duracao_bloco_total = sum(duracao_str_para_segundos(d) for d in bloco_atual['Duração'])
                    lista_final_blocos.append({
                        'Matéria': materia,
                        'Aula': '\n'.join(bloco_atual['Aula']),
                        'Subtítulo': '\n'.join(bloco_atual['Subtítulo']),
                        'Vídeo': ', '.join(str(v) for v in bloco_atual['Vídeo']),
                        'Videoaula': '\n'.join(bloco_atual['Videoaula']),
                        'Duração': segundos_para_str_hhmmss(duracao_bloco_total)
                    })

                    contador_blocos_semanais[materia] += 1
                    dias_ultimos_blocos_semanais[materia].append(len(lista_final_blocos))  # registra o dia (posição) do bloco criado

                posicao_atual_por_materia[materia] = posicao_atual
                if posicao_atual >= len(dataframe_materia):
                    materia_terminada[materia] = True  # sinaliza que terminou essa matéria

            for materia in self.lista_nomes_materias:
                if contador_blocos_semanais[materia] >= 7 or (materia_terminada[materia] and contador_blocos_semanais[materia] > 0):
                    inserir_revisao_semanal(materia)

            if all(contador_revisoes_semanais_para_revisao_mensal[materia] >= 4 or materia_terminada[materia] for materia in self.lista_nomes_materias):
                inserir_revisao_mensal(self.lista_nomes_materias)

        dataframe_cronograma_final = pd.DataFrame(lista_final_blocos)
        dataframe_cronograma_final.insert(0, 'Dia', range(1, len(dataframe_cronograma_final) + 1))

        colunas_ordenadas = ['Dia', 'Matéria', 'Aula', 'Subtítulo', 'Vídeo', 'Videoaula', 'Duração']
        dataframe_cronograma_final = dataframe_cronograma_final[colunas_ordenadas]

        dataframe_cronograma_final.to_excel("Cronograma De Estudos Intercalado Com Revisões Semanais e Mensais.xlsx", index=False)
        messagebox.showinfo("Sucesso", "✅ Cronograma completo com revisões semanais e mensais finalizado!")

# --- Execução do app ---

if __name__ == "__main__":
    root = tk.Tk()
    app = CronogramaApp(root)
    root.mainloop()
