# BraScraper - Ferramentas de Web Scraping para Pesquisa no Brasil 🔍📊

## Simplificando a Coleta de Dados de Fontes Brasileiras para Pesquisadores

### Sobre o Projeto

O **BraScraper** é uma biblioteca Python desenvolvida para facilitar a coleta automatizada de dados de diversas fontes brasileiras. Esta ferramenta foi criada para democratizar o acesso à informação pública e acadêmica, permitindo que pesquisadores obtenham dados estruturados de múltiplas fontes oficiais e institucionais do Brasil.

### Por que o BraScraper é Importante? 📊

A pesquisa empírica no Brasil enfrenta desafios significativos relacionados à dispersão e falta de padronização dos dados. O BraScraper resolve esses problemas ao:

- **Automatizar a coleta de dados** de múltiplas fontes brasileiras
- **Padronizar as informações** em formatos facilmente analisáveis
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

O BraScraper transforma a maneira como pesquisadores podem abordar estudos empíricos:

1. **Escala sem precedentes**: Coleta de dados que levaria meses pode ser realizada em horas
2. **Democratização da pesquisa**: Acesso a dados robustos para instituições com recursos limitados
3. **Reprodutibilidade científica**: Pesquisas mais transparentes e verificáveis
4. **Análises longitudinais**: Facilita estudos temporais da evolução de políticas e legislação
5. **Cruzamento de dados**: Permite correlacionar informações de diferentes fontes

### Instalação

```bash
pip install brascraper
```

### Como Usar 💻

O BraScraper foi projetado para ser simples de usar:

```python
from brascraper import scraper

# Criar um raspador para a Presidência da República
raspador = scraper("PRESIDENCIA")

# Buscar informações
dados = raspador.scrape(pesquisa="Lei de Responsabilidade Fiscal")

# Os dados vêm estruturados e prontos para análise
print(dados)
```

### Exemplos de Uso por Fonte

#### Câmara dos Deputados
```python
from brascraper import scraper

camara = scraper("CAMARA")
dados = camara.scrape(pesquisa="meio ambiente")
```

#### Senado Federal
```python
from brascraper import scraper

senado = scraper("SENADO")
dados = senado.scrape(pesquisa="educação")
```

#### IPEA
```python
from brascraper import scraper

ipea = scraper("IPEA")
dados = ipea.scrape(pesquisa="economia brasileira")
```

### Contribuindo

Contribuições são bem-vindas! Por favor, leia nossas diretrizes de contribuição antes de submeter pull requests.

### Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

### Contato

**Bruno da C. de Oliveira** - bruno.dcdo@gmail.com

Link do Projeto: [https://github.com/bdcdo/brascraper](https://github.com/bdcdo/brascraper)
