from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import json
import re

class Crawler:
    #CONFIGURAÇÕES DO DRIVER
    def __init__(self):
        self.URL = 'https://www.voegol.com.br'
        options = Options()
        options.headless = True
        self.driver = webdriver.Firefox(options = options)
        self.driver.maximize_window()
    
    #FUNÇÃO CIDADE
    def input_cidade(self, id, cidade):
        div = self.driver.find_element(By.ID, id)
        time.sleep(1)
        div.click()
        field = self.driver.find_element(By.XPATH, "//input[@class='select2-search__field focus']")
        time.sleep(1)
        field.send_keys(cidade, Keys.ENTER)
    
    #FUNÇÃO DATA
    def input_data(self, id, data):
        data = datetime.strptime(data, "%Y-%m-%d").date()
        new_data = data.strftime('%d/%m/%Y')
        new_data = str(new_data)
        new_data = new_data.replace('/','')

        field = self.driver.find_element(By.ID, id)
        time.sleep(1)
        field.send_keys(new_data, Keys.ENTER)

    #TRATANDO DADOS
    def get_tabela(self, html_text):
        soup = BeautifulSoup(html_text, 'html.parser')
        lista = []
        for span in soup.find_all(class_= 'a-desc__value'):
            lista.append(span.get_text())

        df = pd.DataFrame(lista)
        df = df.rename(columns = {0 : 'valores'})
        columns = 5
        qtde = int(len(df) / columns)
        df_pass = pd.DataFrame()

        for i in range(qtde):
            voo = df.iloc[: columns]
            df_pass['coluna ' + str(i)] = voo
            df = df.drop(df.index[: columns])
            df.reset_index(inplace = True, drop = True)

        df_pass = df_pass.transpose()
        df_pass.reset_index(inplace = True, drop = True)
        df_pass = df_pass.rename(columns={0 : 'origem'})
        df_pass = df_pass.rename(columns={1 : 'destino'})
        df_pass = df_pass.rename(columns={2 : 'duracao'})
        df_pass = df_pass.rename(columns={3 : 'conexao'})
        df_pass = df_pass.rename(columns={4: 'preco'})

        df_pass['preco'] = df_pass['preco'].map(lambda x: re.sub('[^0-9-,]', '', x))
        df_pass['preco'] = df_pass['preco'].map(lambda x: re.sub(',', '.', x))
        df_pass['duracao'] = df_pass['duracao'].map(lambda x: re.sub('[^0-9-:]', '', x))

        return df_pass
    
    #INPUT DADOS
    def send_dados(self, origem, destino, passageiros, data_ida, data_volta):
        self.driver.get(self.URL)
        time.sleep(2)
        
        #COOKIES
        cookies = self.driver.find_element(By.ID, "onetrust-accept-btn-handler")
        time.sleep(1)
        cookies.click()

        #CIDADE
        self.input_cidade('edit-fieldset-origin', origem) #ORIGEM
        self.input_cidade('edit-fieldset-destiny', destino) #DESTINO      

        #INPUT PASSAGEIRO
        div_passageiro = self.driver.find_element(By.ID, "edit-fieldset-passengers")
        time.sleep(1)
        div_passageiro.click()
        btn_passageiro = self.driver.find_element(By.NAME, "add_pass")
        time.sleep(1)
        for i in range(int(passageiros) - 1): #PASSAGEIRO
            btn_passageiro.click()
            time.sleep(1)

        submit_passageiro = self.driver.find_element(By.ID, "passengers-apply")
        time.sleep(1)
        submit_passageiro.click()

        #INPUT DATA
        self.input_data("edit-departure-date", data_ida) #DATA IDA
        self.input_data("edit-back-date", data_volta) #DATA VOLTA

        #SUBMIT IDA
        submit_ida = self.driver.find_element(By.ID, "search-flights")
        time.sleep(1)
        submit_ida.click()
        time.sleep(10)

        #PEGANDO PASSAGENS IDA
        section_ida = self.driver.find_element(By.XPATH, "//div[@class='p-select-flight ng-tns-c156-0']//section")
        time.sleep(1)
        section_ida = section_ida.get_attribute('outerHTML')

        #SUBMIT VOLTA
        div_pass = self.driver.find_element(By.XPATH, "//div[@class='m-bar-product m-bar-product--border-bottom']")
        time.sleep(1)
        div_pass.click()
        submit_volta = self.driver.find_element(By.XPATH, "//button[@class='m-button m-button--isEnabled']")
        time.sleep(1)
        submit_volta.click()
        time.sleep(10)

        #PEGANDO PASSAGENS VOLTA
        section_volta = self.driver.find_element(By.XPATH, "//div[@class='p-select-flight ng-tns-c156-0']//section")
        time.sleep(1)
        section_volta = section_volta.get_attribute('outerHTML')
        list_html = [section_ida, section_volta]
        
        self.driver.quit()
        return list_html

    #RETORNANDO DADOS
    def get_dados(self, lista_html):
        lista_pass = []
        for html in lista_html:
            df = self.get_tabela(html)
            passagem = df.to_json(orient = 'records')
            passagem = json.loads(passagem)
            lista_pass.append(passagem)

        passagens = {
        "idas" : lista_pass[0],
        "voltas" : lista_pass[1]
        }

        return(passagens)