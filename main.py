import re
import time
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Ler carteiras do arquivo CSV
carteiras_df = pd.read_csv("carteiras_recomendadas.csv", sep=';')
carteiras = carteiras_df["Num_Carteiras"].dropna().astype(str).tolist()

# Função para calcular a data final
def calcular_data_final():
    hoje = datetime.date.today()
    if hoje.weekday() in [1, 2, 3, 4]:  # Terça a sexta-feira
        data_final = hoje - datetime.timedelta(days=1)
    else:  # Sábado, Domingo ou Segunda-feira
        dias_para_sexta = (hoje.weekday() - 4) % 7  # Distância até a última sexta-feira
        data_final = hoje - datetime.timedelta(days=dias_para_sexta)
    return data_final.strftime("%Y%m%d")

# Configurações do navegador
chrome_options = Options()
chrome_options.add_argument("--headless")  # Roda sem interface gráfica
service = Service(ChromeDriverManager().install())
navegador = webdriver.Chrome(service=service, options=chrome_options)
#navegador = webdriver.Chrome(service=service)

dados_gerais = []

for carteira in carteiras:
    url = f"https://tradergrafico.com.br/carteiras/?Simu={carteira}"
    navegador.get(url)
    time.sleep(15)  # Aguarda o carregamento da página

    # Fecha o pop-up, se existir
    try:
        navegador.find_element(By.XPATH, '//*[@id="myModal2"]/div/div/div[3]/button').click()
        time.sleep(3)
    except:
        pass

    def get_element_text(xpath, default="NaN"):
        try:
            return navegador.find_element(By.XPATH, xpath).text.strip()
        except:
            return default

    numero_carteira = get_element_text('/html/body/div[3]/div/div[3]/div[1]/div/div[1]/h6/span')
    data_inicial_texto = get_element_text('/html/body/div[3]/div/div[2]/div[2]/div/h6')
    data_formatada = "0"
    match = re.search(r'(\d{2}/\d{2}/\d{2})', data_inicial_texto)
    if match:
        data = match.group(1)
        data_formatada = f"20{data[6:8]}{data[3:5]}{data[0:2]}"

    data_final_formatada = calcular_data_final()
    valor_inv_inicial = re.sub(r'R\$\s*', '', get_element_text('/html/body/div[3]/div/div[3]/div[4]/div/div/h3'))
    valor_saque = re.sub(r'R\$\s*', '', get_element_text('/html/body/div[3]/div/div[3]/div[9]/div/div/h3').replace("/mês", ""))
    valor_reais_por_contrato = get_element_text('/html/body/div[3]/div/div[3]/div[6]/div/div/h3')
    numero_sqn = re.search(r"[\d,]+", get_element_text('/html/body/div[3]/div/h3', "NaN"))
    numero_sqn = numero_sqn.group() if numero_sqn else "NaN"

    # Usa regex para extrair os valores (incluindo negativos)
    valor_texto = get_element_text('/html/body/div[3]/div/div[3]/div[4]/div/div/p')
    match = re.search(r'-?R\$\s*([-?\d,.]+)', valor_texto)  # captura números, incluindo negativos
    percentual_match = re.search(r'-?\d+%', valor_texto)  # Captura também percentuais negativos
    if match:
        raw_value = match.group(1).replace('.', '').replace(',', '.')
        valor_inv_atual = f"{int(float(raw_value)):,}".replace(',', '.')
    else:
        valor_inv_atual = None
    percentual_inv_atual = percentual_match.group(0).replace('%', '') if percentual_match else None

    
    #Acessar as informações Detalhadas da Carteira
    navegador.find_element(By.XPATH, '//*[@id="btn-mais1"]/i').click()
    time.sleep(3)

    dados_dd = get_element_text('//*[@id="mais1"]/div[2]/div/div')
    percentual_dd, data_dd_formatada = "0", "0"
        
    match = re.search(r"(-?\d+)%.*?(\d{2})/(\d{2})/(\d{2})", dados_dd)
    if match:
        percentual_dd = match.group(1)  # Agora captura corretamente valores negativos também
        dia, mes, ano = match.group(2), match.group(3), match.group(4)
        data_dd_formatada = f"20{ano}{mes}{dia}"

        if int(percentual_dd) < 0:
            percentual_restante = 100 + abs(int(percentual_dd))
        else:
            percentual_restante = 100 - int(percentual_dd)
    else:
        percentual_dd = "0"
        percentual_restante = "0"


    valor_melhor_dia = re.search(r'R\$\s([\d\.]+)', get_element_text('//*[@id="mais1"]/div[8]/div/div/h5/span'))
    valor_melhor_dia = valor_melhor_dia.group(1) if valor_melhor_dia else "0"
    valor_pior_dia = re.search(r"R\$\s(-?\d+[.,]?\d*)", get_element_text('//*[@id="mais1"]/div[9]/div/div/h6/span'))
    valor_pior_dia = valor_pior_dia.group(1) if valor_pior_dia else "0"
    melhor_mes = re.sub(r'R\$ \+?', '', get_element_text('//*[@id="mais1"]/div[10]/div/div/h3/span'))
    pior_mes = re.sub(r'R\$ ', '', get_element_text('//*[@id="mais1"]/div[11]/div/div/h3/span'))
    melhor_media_10_dias = re.sub(r'R\$ \+|/dia', '', get_element_text('//*[@id="mais1"]/div[16]/div/div/h3/span'))
    valor_r_quadrado_geral = get_element_text('//*[@id="mais1"]/div[18]/table/tbody/tr[2]/td[4]')
    valor_acerto_geral = get_element_text('//*[@id="mais1"]/div[18]/table/tbody/tr[1]/td[4]').replace('%', '').strip()


    # Pegar a quantidade de Robôs da Carteira

    botao = navegador.find_element(By.XPATH, '//*[@id="btn-mais2"]')
    navegador.execute_script("arguments[0].click();", botao)
    time.sleep(3)

    # Captura a tabela
    tabela = navegador.find_element(By.XPATH, '//*[@id="mais2"]/div[1]/div/div')

    # Extrai o texto da tabela
    tabela_texto = tabela.text

    # Expressão regular para encontrar a última linha com um robô
    padrao = r"^(\d+)\s+(Top Hedger|Fornecedor).*"

    # Encontrar todas as ocorrências
    matches = re.findall(padrao, tabela_texto, re.MULTILINE)

    if matches:
        quantidade_robos = int(matches[-1][0])  # Pega o número da última correspondência
    else:
        quantidade_robos = 0
    

    dados_gerais.append({
        "Simu": numero_carteira,
        "DataInicio": data_formatada,
        "DataFinal": data_final_formatada,
        "InvIni": valor_inv_inicial,
        "InvAtual": valor_inv_atual,
        "PercInvAtual": percentual_inv_atual,
        "Saque": valor_saque,
        "DrawdownPerct": percentual_restante,
        "DrawdownDate": data_dd_formatada,
        "RScontrato": valor_reais_por_contrato,
        "MelhorDia": valor_melhor_dia,
        "PiorDia": valor_pior_dia,
        "MelhorMes": melhor_mes,
        "PiorMes": pior_mes,
        "MelhorMed10Dia": melhor_media_10_dias,
        "SQN": numero_sqn,
        "R2geral": valor_r_quadrado_geral,
        "AcertoGeral": valor_acerto_geral,
        "MargemMin": percentual_dd,
        "QdteRobos": quantidade_robos
    })

navegador.quit()

# Criar DataFrame e salvar
if dados_gerais:
    df = pd.DataFrame(dados_gerais)
    df.to_csv("dados_trader.csv", index=False, sep=';', mode='a', header=not pd.io.common.file_exists("dados_trader.csv"))
    df.to_excel("dados_trader.xlsx", index=False)

print("Processo concluído com sucesso!")
