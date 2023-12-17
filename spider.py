# -*- coding: utf-8 -*-
import json
from datetime import datetime
from typing import Any

import pytz
import requests
import scrapy

list_month = "janeiro fevereiro março abril maio junho julho agosto \
                      setembro outubro novembro dezembro".split()


class FipeSpider(scrapy.Spider):
    name = 'Fipe'
    start_urls = ['https://veiculos.fipe.org.br']
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'DNT': '1',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'DEFAULT_REQUEST_HEADERS': headers,
        #'DOWNLOAD_DELAY': 0.1
    }

    def __init__(self, year: str, month: str, **kwargs: Any):
        super().__init__(**kwargs)
        self.year = int(year)
        self.month = int(month)
        month_name = list_month[int(month)]
        self.reference = f"{month_name}/{year} "

    def parse(self, response):
        yield scrapy.Request(url="https://veiculos.fipe.org.br/api/veiculos//ConsultarTabelaDeReferencia",
                             callback=self.ref_tables, method="POST")

    def ref_tables(self, response):
        ref_tables = json.loads(response.text)
        ref_tables = [ref for ref in ref_tables if
                      ref["Mes"] == self.reference]
        for table in ref_tables:
            formdata = {"codigoTabelaReferencia": table["Codigo"],
                        "codigoTipoVeiculo": "1"}

            yield scrapy.Request(url="https://veiculos.fipe.org.br/api/veiculos/ConsultarMarcas",
                                 callback=self.brands,
                                 method="POST", body=json.dumps(formdata),
                                 meta={"formdata": formdata.copy()})

    def brands(self, response):
        brands_table = json.loads(response.text)
        formdata = response.meta["formdata"]
        for brand in brands_table:
            formdata["codigoMarca"] = brand["Value"]
            yield scrapy.Request(url="https://veiculos.fipe.org.br/api/veiculos//ConsultarModelos",
                                 callback=self.models,
                                 method="POST",
                                 body=json.dumps(formdata),
                                 meta={"formdata": formdata.copy()})

    def models(self, response):
        models_table = json.loads(response.text)
        formdata = response.meta["formdata"]
        for model in models_table["Modelos"]:
            formdata["codigoModelo"] = model["Value"]
            yield scrapy.Request(url="https://veiculos.fipe.org.br/api/veiculos//ConsultarAnoModelo",
                                 callback=self.years,
                                 method="POST",
                                 body=json.dumps(formdata),
                                 meta={"formdata": formdata.copy()})

    def years(self, response):
        years_table = json.loads(response.text)
        formdata = response.meta["formdata"]
        for ano in years_table:
            formdata["anoModelo"], formdata["codigoTipoCombustivel"] = ano["Value"].split("-")
            formdata["tipoVeiculo"] = "carro"
            formdata["tipoConsulta"] = "tradicional"
            formdata['data_consulta'] = datetime.now(pytz.timezone('UTC')).strftime("%Y-%m-%d %H:%M:%S")
            yield scrapy.Request(url="https://veiculos.fipe.org.br/api/veiculos//ConsultarValorComTodosParametros",
                                 callback=self.get_data,
                                 method="POST",
                                 body=json.dumps(formdata.copy()),
                                 meta={"formdata": formdata})

    @staticmethod
    def parse_reference_month(reference_month: str) -> int:
        month, _, year = reference_month.split()
        month = list_month.index(month) + 1
        reference_month = int(f"{year}{month}")
        return reference_month

    @staticmethod
    def parse_data(self, response) -> dict:
        response_data = json.loads(response.text)
        data = dict()
        data["ano"] = self.year
        data["mes"] = self.month
        data["valor"] = float(response_data["Valor"].replace("R$ ", "").replace(".", "").replace(",", "."))
        data["marca"] = response_data["Marca"]
        data["modelo"] = response_data["Modelo"]
        data["ano_modelo"] = str(response_data["AnoModelo"])
        data["combustivel"] = response_data["Combustivel"]
        data["codigo_fipe"] = response_data["CodigoFipe"]
        data["mes_referencia"] = self.parse_reference_month(response_data["MesReferencia"])
        #data["autenticacao"] = response_data["Autenticacao"]
        data["tipo_veiculo"] = response_data["TipoVeiculo"]
        data["sigla_combustivel"] = response_data["SiglaCombustivel"]
        data["data_consulta"] = response.meta["formdata"]["data_consulta"]
        return data

    def get_data(self, response):
        data = self.parse_data(self, response)
        self.export_data(data)

    def export_data(self, data):
        response = requests.post(
            "http://localhost:8080/veiculo",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code != 201:
            self.logger.error(json.dumps(data, indent=4))
