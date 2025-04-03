ciclo atual:

    scraper de 30 em 30 segundos:
        extrai mensagens pendentes de vendedores 
            envia mensagem por mensagem para o fluxo por array do tipo (658582274,Prancha de surf 5'11,silasurfing,80 €,Sim esta)
                o fluxo retorna uma respota e adiciona a db diretamente
                    a resposta retornada é enviada pelo scraper para a Olx

    resumo: Para cada mensagem o fluxo é chamado uma vez e causa problemas no rate de api calls da openAI

ciclo novo:

    scraper de 10 em 10 minutos:
        
        extrai mensagens pendentes de vendedores
            envia conjunto de mensagens de uma conversa (661646490,Prancha surf Torq 5'11,Nuno Fernandes,270 €,Bom dia. Sim está disponível. Sou de Carcavelos.Disponha)
                o fluxo retorna uma respota e adiciona a db diretamente
                    a resposta retornada é enviada pelo scraper para a Olx
                        Logo após enviar espera 30 segundos antes de buscar o novo conjunto de mensages da nova conversa


fluxo langflow:

To instruct your model effectively, you need to extract the following relevant information from the ads:

1. **Product Details**:
   - Type of product (e.g., electronics, furniture, vehicles).
   - Brand and model information.
   - Condition of the item (new, used, refurbished).

2. **Pricing Information**:
   - Asking price of the item.
   - Historical pricing data (average prices for similar items).
   - Reference price lists (e.g., market value, depreciation rates).

3. **Seller Information**:
   - Seller's profile (e.g., ratings, previous sales).
   - Location of the seller (to assess shipping or pickup options).

4. **Negotiation Context**:
   - Previous negotiation dialogues (if available) to understand common strategies and responses.
   - Successful negotiation examples related to similar products.

5. **Market Trends**:
   - Current trends in pricing and demand for specific products.
   - Recent news or updates that may affect pricing (e.g., new product launches).

6. **Negotiation Strategies**:
   - Guidelines or rules for effective negotiation (e.g., maintaining respect, explaining offers).
   - Common phrases or language used in negotiations specific to the platform.

Como fornecer essa informação: 
    
1. Ad_title + User answer about contition - ok 

2. Ad_price + WebSearcherAgent - ok

3. N/A

4. futuro

5. WebSearcherAgent - ok

6. Searching the pdf about negotiations



Fiz hoje (02/04)

Repensei em nova forma de realizar o ciclo

Agente para buscar informação no PDF usando gwen

Agente para buscar informações sobre produtos na web.
