# OLX SurfBoards Negotiator

Um scraper para monitorar e gerenciar conversas de anúncios de pranchas de surf no OLX.

## Funcionalidades

- Monitora anúncios favoritos no OLX
- Extrai informações dos anúncios
- Coleta mensagens de vendedores
- Armazena dados em um banco de dados
- Fornece uma API REST para gerenciar as conversas

## Requisitos

- Python 3.8+
- Chrome/Chromium instalado
- Conta no OLX

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/Olx-SurfBoards-Negotiator.git
cd Olx-SurfBoards-Negotiator
```

2. Crie um ambiente virtual e ative-o:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Copie o arquivo de exemplo de variáveis de ambiente:
```bash
cp .env.example .env
```

5. Configure as variáveis de ambiente no arquivo `.env`:
```env
OLX_EMAIL=seu_email@exemplo.com
OLX_PASSWORD=sua_senha
API_URL=http://localhost:8000
HEADLESS=True
LOG_LEVEL=INFO
```

## Uso

1. Inicie a API:
```bash
uvicorn DataBaseAPIs:app --reload
```

2. Em outro terminal, execute o scraper:
```bash
python olx_scraper/main.py
```

O scraper irá:
- Fazer login no OLX
- Acessar a página de favoritos
- Coletar links dos anúncios
- Extrair informações e mensagens
- Enviar dados para a API
- Repetir o processo a cada 5 minutos

## Estrutura do Projeto

```
olx_scraper/
├── config/
│   └── settings.py
├── models/
│   └── anuncio.py
├── services/
│   ├── api.py
│   ├── browser.py
│   └── olx.py
├── utils/
│   └── logger.py
└── main.py
```

## Logs

Os logs são salvos em `olx_scraper.log` e também são exibidos no console.

## Cache

Os links processados são armazenados em `links_cache.json` para evitar duplicação.

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes. 