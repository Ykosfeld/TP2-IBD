**PROPOSTA TP2 \| INTRODUÇÃO A BANCO DE DADOS \| TB**

Evandro Araujo Furlaneto Delgado (2025018830)  
Letícia Schmidt Tolentino Santos (2025014168)  
Victor Daniel Barbosa Thome (2026303953)  
Vitória Medeiros Carrera de Oliveira (2019027245)  
Yuri Florentino Kosfeld (2022038503)

# **1\. CONJUNTO DE DADOS ESCOLHIDO** 

*Fiscalização \- Auto de Infração (IBAMA)*, portal [dados.gov.br/dados/conjuntos-dados](https://dados.gov.br/dados/conjuntos-dados):  [dados.gov.br/dados/conjuntos-dados/fiscalizacao-auto-de-infracao](http://dados.gov.br/dados/conjuntos-dados/fiscalizacao-auto-de-infracao) . Arquivo *auto\_infracao\_2026.csv*, atualizado em 27/10/2026, com 13.648 linhas e 84 colunas sobre autos de infração ambiental lavrados de jan a out/2026 em todas as 27 UFs. 

# **2\. ENTIDADES E INSTÂNCIAS**

| Entidade | PK | Atributos (s/ ser PK) | Colunas do dataset | Instâncias |
| ----- | ----- | ----- | ----- | ----- |
| INFRATOR | id\_infrator (um inteiro, vai ser criado) | nome\_infrator, tipo\_pessoa, cpf\_cnpj | NOME\_INFRATOR, TP\_PESSOA\_INFRATOR, CPF\_CNPJ\_INFRATOR  | \~10400 |
| MUNICIPIO | cod\_municipio | nome\_municipio, uf | COD\_MUNICIPIO (PK), MUNICIPIO, UF | 1674 |
| ORDEM\_FISCALIZACAO | codigo\_ordem  | unidade\_ordenadora, nome\_operacao | ORDEM\_FISCALIZACAO (PK), UNID\_ORDENADORA, OPERACAO\_SOL\_RECURSO  | 872 |
| TIPO\_INFRACAO | cod\_infracao | descricao\_infracao, tipo\_infracao | COD\_INFRACAO (PK), DES\_INFRACAO, TIPO\_INFRACAO | 23 |
| AUTO\_INFRACAO | num\_auto\_infracao | data\_hora, valor\_multa, tipo\_auto, descricao\_fato, forma\_entrega,  local, bioma, unidade\_controle, latitude, longitude | NUM\_AUTO\_INFRACAO (PK), DAT\_HORA\_AUTO\_INFRACAO, VAL\_AUTO\_INFRACAO, TIPO\_AUTO, DES\_AUTO\_INFRACAO, FORMA\_ENTREGA, DES\_LOCAL\_INFRACAO, DS\_BIOMAS\_ATINGIDOS, UNID\_CONTROLE, NUM\_LATITUDE\_AUTO, NUM\_LONGITUDE\_AUTO  | 13619 |

# **3\. RELACIONAMENTOS E INSTÂNCIAS**

| Relacionamento | Entidades | Card. | Instâncias |
| ----- | ----- | ----- | ----- |
| RECEBE  | INFRATOR, AUTO\_INFRACAO | M:N | 13619 |
| ENQUADRA | TIPO\_INFRACAO, AUTO\_INFRACAO | 1:N | 13619 |
| OCORRE\_EM | MUNICIPIO, AUTO\_INFRACAO | 1:N | 13619 |
| DECORRE\_DE | ORDEM\_FISCALIZACAO, AUTO\_INFRACAO | 1:N | 13466 |
| AUTUADO\_EM | INFRATOR, ORDEM\_FISCALIZACAO | M:N | 10641 |

# **4\. INVESTIGAÇÕES PREVISTAS**

• Geográfica: quais UFs e municípios concentram mais autos e maior valor de multas (preliminar: o Pará soma 38% do valor total), além de biomas mais atingidos.  
• Distribuição dos valores: a mediana é de R\$ 22 mil e a média de R\$ 311 mil; poucos autos de R\$ 1 milhão ou mais concentram a maior parte do valor. Quem são e onde estão?  
• Perfil das infrações: categorias (flora, fauna, pesca, licenciamento...) e valor médio por categoria.  
• Infratores: pessoa física contra pessoa jurídica (quantidade e valor médio), empresas autuadas em mais de um estado e reincidência.  
• Operações: ordens de fiscalização que percorrem mais municípios e unidades ordenadoras com mais autos.  
• Tempo: evolução mensal dos autos em 2026 e distribuição ao longo do ano.