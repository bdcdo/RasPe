# RasPe - Raspadores para Pesquisas Acadêmicas 🔍📊

## Simplificando a Coleta de Dados para Pesquisa Empírica no Brasil

### Sobre o Projeto

O **RasPe** é uma biblioteca Python desenvolvida para facilitar a coleta automatizada de dados de diversas fontes brasileiras. Esta ferramenta foi criada para democratizar o acesso à informação pública e acadêmica, permitindo que pesquisadores obtenham dados estruturados de múltiplas fontes oficiais e institucionais do Brasil.

### Por que o RasPe é Importante? 📊

A pesquisa empírica no Brasil enfrenta desafios significativos relacionados à dispersão e falta de padronização dos dados. O RasPe resolve esses problemas ao:

- **Automatizar a coleta de dados** de múltiplas fontes brasileiras
- **Padronizar as informações** em formatos facilmente analisáveis (Pandas DataFrames)
- **Reduzir drasticamente o tempo** necessário para a coleta de dados
- **Minimizar erros humanos** no processo de coleta
- **Permitir análises em grande escala** que seriam impraticáveis manualmente

### Fontes Suportadas Atualmente 🏛️

- **Presidência da República**: Legislação federal brasileira
- **Câmara dos Deputados**: Proposições e atividade legislativa
- **Senado Federal**: Projetos de lei e atividade senatorial
- **Conselho Nacional de Justiça (CNJ)**: Comunicados e normas do sistema judiciário
- **IPEA**: Instituto de Pesquisa Econômica Aplicada

### Impacto na Pesquisa Empírica 🚀

O RasPe transforma a maneira como pesquisadores podem abordar estudos empíricos:

1. **Escala sem precedentes**: Coleta de dados que levaria meses pode ser realizada em horas
2. **Democratização da pesquisa**: Acesso a dados robustos para instituições com recursos limitados
3. **Reprodutibilidade científica**: Pesquisas mais transparentes e verificáveis
4. **Análises longitudinais**: Facilita estudos temporais da evolução de políticas e legislação
5. **Cruzamento de dados**: Permite correlacionar informações de diferentes fontes

### Instalação

```bash
pip install git+https://github.com/bdcdo/RasPe.git
```

### Como Usar 💻

O RasPe foi projetado para ser simples e intuitivo:

```python
import raspe

# Criar um raspador para a Presidência da República
scraper_presidencia = raspe.presidencia()

# Buscar informações
dados = scraper_presidencia.scrape(pesquisa="Lei de Responsabilidade Fiscal")

# Os dados vêm estruturados como Pandas DataFrame, prontos para análise
print(dados.head())
```

### Exemplos de Uso por Fonte

#### Presidência da República
```python
import raspe

presidencia = raspe.presidencia()
dados = presidencia.scrape(pesquisa="meio ambiente")
```

#### Câmara dos Deputados
```python
import raspe

camara = raspe.camara()
dados = camara.scrape(pesquisa="educação")
```

#### Senado Federal
```python
import raspe

senado = raspe.senado()
dados = senado.scrape(pesquisa="saúde pública")
```

#### Conselho Nacional de Justiça (CNJ)
```python
import raspe

cnj = raspe.cnj()
dados = cnj.scrape(pesquisa="resolução")
```

#### IPEA
```python
import raspe

ipea = raspe.ipea()
dados = ipea.scrape(pesquisa="economia brasileira")
```

### Funcionalidades Avançadas

#### Buscar múltiplos termos
```python
import raspe

presidencia = raspe.presidencia()
# Busca múltiplos termos e adiciona coluna 'termo_busca' para identificação
dados = presidencia.scrape(pesquisa=["educação", "saúde", "segurança"])
```

#### Controlar paginação
```python
import raspe

camara = raspe.camara()
# Buscar apenas as primeiras 5 páginas
dados = camara.scrape(pesquisa="meio ambiente", paginas=range(1, 6))
```

### Requisitos

- Python >= 3.11
- pandas >= 2.0.0
- requests >= 2.28.0
- beautifulsoup4 >= 4.12.2
- tqdm >= 4.66.1

### Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue ou pull request no repositório do GitHub.

### Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

### Contato

**Bruno da C. de Oliveira** - bruno.dcdo@gmail.com

Link do Projeto: [https://github.com/bdcdo/RasPe](https://github.com/bdcdo/RasPe)

---

### Citação

Se você utilizar o RasPe em sua pesquisa, por favor considere citá-lo:

```bibtex
@software{raspe2025,
  author = {Oliveira, Bruno da C. de},
  title = {RasPe: Raspadores para Pesquisas Acadêmicas},
  year = {2025},
  url = {https://github.com/bdcdo/RasPe}
}
```
