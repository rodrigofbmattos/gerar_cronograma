import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilenames

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

# --- Seleção dos arquivos CSV ---

Tk().withdraw()  # Oculta a janela principal do Tkinter
arquivos_selecionados = askopenfilenames(
    title="Selecione os CSVs das matérias",
    filetypes=[("CSV files", "*.csv")]
)

if not arquivos_selecionados:
    raise SystemExit("❌ Nenhum arquivo selecionado.")

# --- Leitura dos CSVs e armazenamento em dicionário ---

dataframes_materias = {}
lista_nomes_materias = []

for caminho_arquivo in arquivos_selecionados:
    nome_materia = caminho_arquivo.split('/')[-1].replace('.csv', '')
    dataframe_materia = pd.read_csv(caminho_arquivo, sep=';')
    dataframe_materia['Matéria'] = nome_materia  # Adiciona coluna para identificar a matéria
    dataframes_materias[nome_materia] = dataframe_materia
    lista_nomes_materias.append(nome_materia)

# --- Mostrar as matérias selecionadas numeradas para o usuário ---

print("\nArquivos selecionados:")
for indice, nome_materia in enumerate(lista_nomes_materias):
    print(f"{indice+1}: {nome_materia}")

# --- Solicitar ordem desejada para os arquivos (reordenação) ---

while True:
    ordem_entrada = input("\nDigite a ordem dos arquivos separada por vírgula (ex: 2,1,3): ")
    try:
        ordem_indices = [int(x.strip()) - 1 for x in ordem_entrada.split(',')]

        # Validação da entrada: índices únicos, dentro do intervalo, quantidade correta e que não se repetem
        if (len(ordem_indices) == len(lista_nomes_materias) and
            all(0 <= x < len(lista_nomes_materias) for x in ordem_indices) and
            len(set(ordem_indices)) == len(lista_nomes_materias)):
            break  # Entrada válida, sai do loop
        else:
            print("❌ Por favor, insira todos os números uma única vez e dentro da faixa mostrada.")
    except ValueError:
        print("❌ Entrada inválida. Use apenas números separados por vírgula.")

# --- Reordenar as matérias conforme a ordem fornecida pelo usuário ---
lista_nomes_materias = [lista_nomes_materias[i] for i in ordem_indices]

# --- Inicializações para o processamento dos blocos de aula ---

posicao_atual_por_materia = {materia: 0 for materia in lista_nomes_materias}  # índice da próxima aula
materia_terminada = {materia: False for materia in lista_nomes_materias}   # flag se terminou matéria
contador_blocos_semanais = {materia: 0 for materia in lista_nomes_materias}  # contagem de blocos semanais feitos
dias_ultimos_blocos_semanais = {materia: [] for materia in lista_nomes_materias}   # dias para revisão semanal
dias_acumulados_para_revisao_mensal = {materia: [] for materia in lista_nomes_materias}  # dias acumulados para revisão mensal
contador_revisoes_semanais_para_revisao_mensal = {materia: 0 for materia in lista_nomes_materias}  # controle para disparar revisão mensal

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
    # Acumula esses dias para a revisão mensal
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
    for materia in lista_nomes_materias:
        if materia_terminada[materia]:
            continue  # pula se já terminou essa matéria

        dataframe_materia = dataframes_materias[materia]
        posicao_atual = posicao_atual_por_materia[materia]

        bloco_atual = {'Matéria': [], 'Aula': [], 'Subtítulo': [], 'Vídeo': [], 'Videoaula': [], 'Duração': []}
        tempo_total_bloco = 0

        # Agrupa aulas até atingir limite de tempo ou fim da matéria
        while posicao_atual < len(dataframe_materia):
            linha = dataframe_materia.iloc[posicao_atual]
            duracao_segundos = duracao_str_para_segundos(linha['Duração'])

            # Verifica se adicionar essa aula ultrapassa o limite de tempo do bloco
            if tempo_total_bloco + duracao_segundos > limite_tempo_bloco_segundos and bloco_atual['Aula']:
                break

            # Adiciona dados da aula no bloco
            for coluna in ['Matéria', 'Aula', 'Subtítulo', 'Vídeo', 'Duração']:
                bloco_atual[coluna].append(linha[coluna])
            bloco_atual['Videoaula'].append(f"{linha['Videoaula']} ({linha['Duração']})")
            tempo_total_bloco += duracao_segundos
            posicao_atual += 1

        # Se algum conteúdo foi adicionado ao bloco, inclui no cronograma final
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

    # --- Inserção de blocos de revisões semanais ---
    for materia in lista_nomes_materias:
        if contador_blocos_semanais[materia] >= 7 or (materia_terminada[materia] and contador_blocos_semanais[materia] > 0):
            inserir_revisao_semanal(materia)

    # --- Inserção de blocos de revisões mensais ---
    # Só dispara se todas as matérias tiverem pelo menos 4 revisões semanais feitas ou estiverem finalizadas
    if all(contador_revisoes_semanais_para_revisao_mensal[materia] >= 4 or materia_terminada[materia] for materia in lista_nomes_materias):
        inserir_revisao_mensal(lista_nomes_materias)

# --- Montagem e exportação do DataFrame final ---

dataframe_cronograma_final = pd.DataFrame(lista_final_blocos)
dataframe_cronograma_final.insert(0, 'Dia', range(1, len(dataframe_cronograma_final) + 1))

# Define a ordem das colunas para o arquivo final
colunas_ordenadas = ['Dia', 'Matéria', 'Aula', 'Subtítulo', 'Vídeo', 'Videoaula', 'Duração']
dataframe_cronograma_final = dataframe_cronograma_final[colunas_ordenadas]

# Salva o cronograma final em arquivo Excel
dataframe_cronograma_final.to_excel("Cronograma Final Intercalado Com Revisões.xlsx", index=False)
print("✅ Cronograma completo com revisões semanais e mensais finalizado!")
