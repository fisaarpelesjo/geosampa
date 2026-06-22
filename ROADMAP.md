# Roadmap do Projeto

Este roadmap lista evoluções úteis para transformar o projeto em uma ferramenta robusta de análise técnica de lotes, áreas públicas, restrições urbanísticas, camadas ambientais e possíveis intervenções públicas a partir de dados do GeoSampa e fontes oficiais complementares.

## Princípios

- Manter o projeto genérico para análise de qualquer setor, quadra e lote.
- Não versionar dados sensíveis, arquivos gerados, endereços, SQLs específicos de investigação ou documentos locais.
- Separar indício técnico de conclusão jurídica.
- Registrar fonte, camada, data de consulta e limitações de cada achado.
- Preferir WFS, metadados e documentos oficiais a scraping de interface.
- Fazer uma feature por commit, com título e descrição em português do Brasil, seguida de push.
- Priorizar features que validam a hipótese de investigação em curso antes de features operacionais/usabilidade.

## Concluído

- feat(intersecoes): consulta espacial com CRS/BBOX corrigidos.
- feat(camadas): descoberta de camadas candidatas via WFS.
- feat(fontes): inventário de fontes oficiais via CKAN.
- feat(documentos): extração de referências legais das camadas.
- feat(dossie): relatório investigativo consolidado.
- feat(documentos): validação legal (tarefas e matriz de validação).
- feat(ocupacao): cruzar com camadas de edificação e infraestrutura.
- feat(documentos): busca legislação municipal por número (link manual).

## Fase 1 — Validação da Hipótese (prioridade máxima)

A hipótese em investigação: o lote-alvo é área pública/protegida (manancial, parque, ZEIS sobrepostos, sem contribuinte cadastrado) e precisa confirmar se há ato legal válido (decreto/desapropriação) e se a ocupação real é compatível com isso.

### feat(ocupacao): comparar cadastro fiscal e ocupação aparente

- Criar seção de divergência cadastral.
- Comparar lote sem contribuinte/porta/área construída com camadas auxiliares.
- Registrar como indício técnico, não como prova dominial ou habitacional.

### feat(dossie): criar matriz de risco técnico

- Classificar achados em níveis como `BAIXO`, `MEDIO`, `ALTO` e `CRITICO`.
- Considerar área pública, DUP/DIS, parque proposto, manancial, APP e ZEIS.
- Explicar que risco técnico não é conclusão jurídica.
- Permitir ajustar pesos por configuração.

### feat(documentos): associar plantas e croquis

- Mapear campos de planta, croqui e desenho técnico.
- Gerar lista de plantas a solicitar ou consultar.
- Registrar fonte de cada planta.
- Preparar anexos quando os arquivos forem fornecidos localmente.

### feat(documentos): suporte a PDFs oficiais

- Ler PDFs locais de decreto, planta, certidão ou processo.
- Extrair texto quando possível.
- Indexar número de documento, data, órgão e termos relevantes.
- Gerar resumo cauteloso com citação de páginas.

## Fase 2 — Confiabilidade da Evidência

Sustenta a hipótese com dados tecnicamente confiáveis e rastreáveis.

### feat(geometria): validar qualidade geométrica

- Detectar geometria inválida, multipolígono, buracos e geometrias vazias.
- Registrar CRS original e CRS métrico usado.
- Calcular área, perímetro e centróide do lote.
- Gerar alerta quando a geometria parecer incompatível com o CRS.

### feat(intersecoes): melhorar estratégia de consulta por BBOX

- Testar automaticamente variações de BBOX quando uma camada retorna vazio.
- Registrar no CSV qual CRS/BBOX foi usado em cada consulta.
- Diferenciar retorno vazio real de falha técnica ou incompatibilidade de CRS.
- Adicionar coluna `bbox_crs` e `bbox_usado` em `intersections.csv`.

### feat(camadas): classificar camadas por relevância

- Criar categorias como `DESAPROPRIACAO`, `AREA_PUBLICA`, `PARQUE`, `MANANCIAL`, `APP`, `ZEIS`, `HABITACAO`, `INFRAESTRUTURA` e `CADASTRO`.
- Evitar depender apenas de keyword solta.
- Adicionar peso de relevância para priorizar camadas críticas no relatório.

### feat(dossie): registrar trilha de auditoria

- Salvar data/hora da consulta.
- Salvar endpoint, camada, parâmetros e hash do retorno.
- Incluir versão do programa no relatório.
- Registrar arquivos brutos usados para reproduzir o resultado.

## Fase 3 — Complementar (depois da hipótese validada)

### feat(intersecoes): resumir atributos das feições intersectantes

- Exportar CSV específico com atributos das feições intersectantes.
- Incluir área individual de interseção por feição.
- Incluir percentual de sobreposição por feição.
- Preservar propriedades originais em JSON técnico.

### feat(relatorio): melhorar linguagem e anexos

- Padronizar frases cautelosas.
- Adicionar seção "O que o dado indica".
- Adicionar seção "O que o dado não prova".
- Adicionar checklist de confirmação oficial.

### feat(imagens): integrar ortofotos ou imagens de referência

- Gerar mapa com camada base adequada.
- Permitir anexar imagem local de referência.
- Não versionar imagens sensíveis.
- Registrar data/fonte da imagem quando conhecida.

### feat(interface): criar painel web local

- Criar formulário para setor, quadra e lote.
- Executar pipeline pelo navegador.
- Mostrar progresso por etapa.
- Permitir abrir relatório, mapa e tabelas geradas.

### feat(interface): visualizar camadas críticas no mapa

- Exibir lote alvo destacado.
- Exibir interseções por categoria.
- Criar legenda por tipo de camada.
- Mostrar popup com atributos principais.

### feat(interface): criar tela de dossiê

- Mostrar resumo executivo.
- Mostrar matriz de risco técnico.
- Mostrar documentos pendentes.
- Permitir exportar pacote de análise.

### feat(cli): melhorar comandos e opções

- Adicionar `--somente-camadas-criticas`.
- Adicionar `--limite-camadas`.
- Adicionar `--sem-mapa`.
- Adicionar `--forcar-cache-refresh`.
- Adicionar `--saida` para diretório customizado.

### test(integracao): criar testes reais opcionais de WFS

- Marcar testes com `pytest.mark.integration`.
- Rodar apenas com variável de ambiente explícita.
- Testar consulta de lote genérico mockado ou controlado.
- Testar parse real de GetCapabilities sem gravar dados sensíveis.

### test(geometria): cobrir cenários de interseção

- Testar `CONTAINS_TARGET`.
- Testar `TARGET_CONTAINS_LAYER_FEATURE`.
- Testar `TOUCHES_ONLY`.
- Testar geometrias inválidas.
- Testar CRS ausente.

### chore(ci): configurar validação automatizada

- Rodar Ruff e Pytest em pull requests.
- Bloquear commit com arquivos em `data/`.
- Bloquear padrões de endereço ou SQL específico em arquivos versionados.
- Gerar relatório de cobertura simples.

### chore(privacidade): adicionar verificação de dados sensíveis

- Criar script para procurar endereços, SQLs específicos e nomes de arquivos gerados.
- Rodar antes de commit.
- Manter lista de padrões proibidos configurável.

### feat(exportacao): empacotar resultados

- Gerar pasta final com relatório, mapa, CSVs e metadados.
- Criar manifest com hashes dos arquivos.
- Permitir excluir dados brutos sensíveis.
- Gerar versão sanitizada do dossiê.

### feat(exportacao): gerar resumo para solicitação oficial

- Criar texto-base para pedir confirmação a órgãos públicos.
- Listar documentos e camadas que motivam a solicitação.
- Manter linguagem neutra e técnica.
- Não fazer alegações jurídicas conclusivas.

### docs: documentar metodologia

- Explicar como as camadas são descobertas.
- Explicar como interseções são calculadas.
- Explicar limitações de WFS, CRS, BBOX e metadados.
- Explicar diferença entre cadastro público, domínio, posse, ocupação e intervenção.

## Backlog Técnico

- Suporte a múltiplos lotes em lote.
- Cache com expiração configurável.
- Exportação para Excel.
- Exportação para GeoPackage.
- Paralelização controlada de consultas WFS.
- Limite de taxa para proteger serviços públicos.
- Logs em arquivo.
- Perfil de execução com tempo por camada.
- Configuração por YAML.
- Suporte a camadas WMS apenas para visualização.
- Comparação temporal quando houver versões de camadas.
- Normalização de nomes de campos por camada.
- Relatório de camadas não processadas e motivo.
- Download seletivo de camadas críticas.
- Modo offline usando cache local.
