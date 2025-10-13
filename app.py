import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import time
import openpyxl
from pathlib import Path

def run_automation(caminho_arquivo, total_repeticoes):
    """
    Executa o processo de automação web e retorna o caminho do arquivo de progresso.
    """
    caminho_salva = str(caminho_arquivo).replace('.xlsx', '_PROGRESSO.xlsx')

    # Carregar a planilha do Excel
    try:
        wb = openpyxl.load_workbook(caminho_arquivo)
        ws = wb.active
        if ws['C1'].value != 'Status':
            ws['C1'] = 'Status'
            wb.save(caminho_salva)
    except Exception as e:
        st.error(f"Não foi possível abrir o arquivo Excel: {e}")
        return None

    # Configuração do Driver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=720,480")
    # Adiciona um user-agent para parecer um navegador real
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = None
    try:
        # Usa o webdriver-manager para instalar e configurar o driver automaticamente
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(720, 480)
    except Exception as e:
        st.error(f"Ocorreu um erro ao iniciar o driver: {e}")
        st.info("Dica: Certifique-se de que o Google Chrome está instalado em seu sistema.")
        return None
        
    log_placeholder = st.empty()
    log_text = ""

    # Loop Principal de Automação
    for i in range(total_repeticoes):
        log_text += f"--- INICIANDO REPETIÇÃO {i+1} DE {total_repeticoes} ---\n"
        log_placeholder.code(log_text)
        
        for row_index, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
            link_cell, nome_pagina_cell, status_cell = row[0], row[1], row[2]
            
            link = link_cell.value
            nome_pagina = nome_pagina_cell.value

            if not link:
                continue

            log_text += f"\n[Linha {row_index}, Rep {i+1}] Processando: '{nome_pagina}'\n"
            log_placeholder.code(log_text)

            try:
                wait = WebDriverWait(driver, 20)

                # PRIMEIRA PARTE
                log_text += "  - Acessando o link (1ª vez)...\n"
                log_placeholder.code(log_text)
                driver.get(link)
                driver.get(link)
                
                XPATH_BOTAO_1 = '//*[@id="thumbs_up"]/i'
                primeiro_botao = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_BOTAO_1)))
                primeiro_botao.click()
                log_text += "  - Primeiro botão clicado.\n"
                log_placeholder.code(log_text)
                time.sleep(2)

                # SEGUNDA PARTE
                log_text += "  - Acessando o link (2ª vez)...\n"
                log_placeholder.code(log_text)
                driver.get(link)
                driver.get(link)

                XPATH_BOTAO_2 = '//*[@id="add_fap_btn"]'
                segundo_botao = wait.until(EC.element_to_be_clickable((By.XPATH, XPATH_BOTAO_2)))
                segundo_botao.click()
                log_text += "  - Segundo botão clicado.\n"
                log_placeholder.code(log_text)
                time.sleep(2)
                
                status_cell.value = f"Sucesso na repetição {i+1}"
                log_text += f"  -> SUCESSO para '{nome_pagina}'\n"
                log_placeholder.code(log_text)

            except TimeoutException:
                erro_msg = f"Erro (Timeout) na repetição {i+1}"
                status_cell.value = erro_msg
                log_text += f"  -> ERRO: {erro_msg}\n"
                log_placeholder.code(log_text)
            except NoSuchElementException:
                erro_msg = f"Erro (Não encontrado) na repetição {i+1}"
                status_cell.value = erro_msg
                log_text += f"  -> ERRO: {erro_msg}\n"
                log_placeholder.code(log_text)
            except Exception as e:
                erro_msg = f"Erro inesperado na repetição {i+1}: {str(e).splitlines()[0]}"
                status_cell.value = erro_msg
                log_text += f"  -> ERRO: {erro_msg}\n"
                log_placeholder.code(log_text)
            
            finally:
                try:
                    wb.save(caminho_salva)
                except Exception as e:
                    log_text += f"  !!! AVISO: Não foi possível salvar o progresso: {e}\n"
                    log_placeholder.code(log_text)

    log_text += "\n--- Processo concluído ---\n"
    log_placeholder.code(log_text)

    if driver:
        driver.quit()

    return caminho_salva

# --- Interface do Streamlit ---
st.title("Automatizador de Cliques")
st.write("Faça o upload de uma planilha .xlsx com os links na primeira coluna e os nomes na segunda.")

uploaded_file = st.file_uploader("Escolha a planilha Excel", type="xlsx")
total_repeticoes = st.number_input("Digite o número de repetições", min_value=1, value=1, step=1)

if st.button("Iniciar Automação"):
    if uploaded_file is not None:
        # Salva o arquivo temporariamente
        path = Path.cwd() / uploaded_file.name
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.info("Iniciando o processo de automação... Por favor, aguarde.")
        
        caminho_resultado = run_automation(path, total_repeticoes)

        if caminho_resultado and os.path.exists(caminho_resultado):
            st.success("Automação concluída com sucesso!")
            with open(caminho_resultado, "rb") as file:
                st.download_button(
                    label="Baixar Planilha com Resultados",
                    data=file,
                    file_name=os.path.basename(caminho_resultado),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            # Limpa os arquivos temporários
            os.remove(path)
            os.remove(caminho_resultado)
        else:
            st.error("Ocorreu um erro durante a automação e o arquivo de resultado não foi gerado.")
            # Limpa o arquivo de upload se existir
            if os.path.exists(path):
                os.remove(path)
            
    else:
        st.warning("Por favor, faça o upload de um arquivo .xlsx para iniciar.")
