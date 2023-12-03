# scrap_fipe
A webscrapping of [FIPE](https://veiculos.fipe.org.br/), a brazilian index for commercial car prices


## How to use

### 1. Install the requirements using poetry

```bash
poetry install
```

### 2. Run the script passing the desired year, month and filename as arguments
```bash
scrapy runspider spider.py -a year=2023 -a month=10 -o 2023_10.csv

```