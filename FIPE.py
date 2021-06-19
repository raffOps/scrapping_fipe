# -*- coding: utf-8 -*-
import json

import scrapy


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
        #'LOG_LEVEL': 'INFO',
        'DEFAULT_REQUEST_HEADERS': headers
    }

    def __init__(self, year, month):
        list_month = "janeiro fevereiro março abril maio junho julho agosto \
                      setembro outubro novembro dezembro".split()
        month = list_month[int(month)]
        self.reference = f"{month}/{year} "

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
                                 meta={"formdata":formdata.copy()})

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
            yield scrapy.Request(url="https://veiculos.fipe.org.br/api/veiculos//ConsultarValorComTodosParametros",
                                 callback=self.get_data,
                                 method="POST",
                                 body=json.dumps(formdata.copy()),
                                 meta={"formdata": formdata})

    def get_data(self, response):
        data = json.loads(response.text)
        yield data