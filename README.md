# Painel Brasileirão 2026

Painel do Campeonato Brasileiro 2026 com duas visões, para qualquer um dos 20 clubes:

- **Painel**: posição, pontos, aproveitamento, saldo, últimos jogos, distância para líder/G6/Z4, classificação completa e próximos jogos. Filtro de jogos em casa, fora ou todos.
- **Rumo à Meta**: quantos pontos faltam para uma meta (45 por padrão), chances de vitória em cada jogo restante e simulação dos resultados.

As cores da página mudam de acordo com o clube escolhido. Links diretos: `#sao-paulo`, `#meta-palmeiras` etc.

## Como atualizar

Tudo é calculado a partir de `dados/jogos.csv`, uma linha por jogo. Conforme as partidas acontecem, preencha `gols_mandante` e `gols_visitante` na linha do jogo e faça o commit. O GitHub Pages republica sozinho em cerca de um minuto.

Colunas: `competicao, fase, data, hora, mandante, visitante, gols_mandante, gols_visitante, observacao`.

## Como as probabilidades são calculadas

Para cada jogo, os gols esperados de cada time saem do ataque e da defesa em casa e fora nesta edição do Brasileirão, puxados para a média da liga. As chances de vitória, empate e derrota vêm de uma distribuição de Poisson, e a chance de bater a meta de 20 mil simulações. São estimativas, não previsões.

## Fontes

- Brasileirão: [openfootball/football.json](https://github.com/openfootball/football.json) (domínio público)
- Demais competições do São Paulo: Goal e Arquibancada Tricolor

Projeto de fã, não oficial e sem vínculo com nenhum clube. As cores apenas evocam as de cada time; não há escudos nem marcas.
